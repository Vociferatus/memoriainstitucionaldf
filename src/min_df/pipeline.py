"""Orquestra o vertical slice documental de uma edição do DODF."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

from min_df.audit_artifacts import audit
from min_df.contracts import validate_mentions
from min_df.dodf_to_markdown import convert_pdf
from min_df.extract_mentions import (
    build_extraction_payload,
    load_structured_json,
    write_json,
)
from min_df.load_to_postgres import dry_run_summary, load_all

PILOT_EXPECTATIONS = {
    "pages": 85,
    "blocks": 2553,
    "noise_blocks": 179,
    "mentions": 1140,
    "unique_processes": 1096,
    "missing_blocks": 0,
    "markdown_sha256": "c04bb534c81588b3302c66907a4dfdb71649dc9a963094a82763bcf825d086e2",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_paths(input_path: Path, output_dir: Path) -> dict[str, Path]:
    stem = input_path.stem
    return {
        "manifest": output_dir / "manifests" / f"{stem}.manifest.json",
        "structured": output_dir / "structured" / f"{stem}.structured.json",
        "markdown": output_dir / "markdown" / f"{stem}.md",
        "mentions": output_dir / "extractions" / f"{stem}.mentions.json",
        "audit": output_dir / "audit" / f"{stem}.audit.txt",
        "summary": output_dir / "audit" / f"{stem}.summary.json",
    }


def summarize(paths: dict[str, Path]) -> dict[str, Any]:
    structured = json.loads(paths["structured"].read_text(encoding="utf-8"))
    mentions_payload = json.loads(paths["mentions"].read_text(encoding="utf-8"))
    pages = structured["pages"]
    blocks = [block for page in pages for block in page["blocks"]]
    block_ids = {block["id"] for block in blocks}
    mentions = mentions_payload["mentions"]
    return {
        "pages": len(pages),
        "blocks": len(blocks),
        "noise_blocks": sum(block["removed_as_noise"] for block in blocks),
        "mentions": len(mentions),
        "unique_processes": len({mention["value_normalized"] for mention in mentions}),
        "missing_blocks": sum(mention["block_id"] not in block_ids for mention in mentions),
        "markdown_sha256": sha256_file(paths["markdown"]),
    }


def verify_pilot(summary: dict[str, Any]) -> None:
    divergences = {
        key: {"expected": expected, "actual": summary.get(key)}
        for key, expected in PILOT_EXPECTATIONS.items()
        if summary.get(key) != expected
    }
    if divergences:
        details = json.dumps(divergences, ensure_ascii=False, indent=2)
        raise RuntimeError(f"Regressão em relação ao piloto:\n{details}")


def run_pipeline(
    input_path: Path,
    output_dir: Path,
    *,
    verify_pilot_baseline: bool = False,
    dsn: str | None = None,
    source_name: str = "DODF",
    source_kind: str = "diario_oficial",
) -> dict[str, Any]:
    input_path = input_path.resolve()
    output_dir = output_dir.resolve()
    if not input_path.is_file():
        raise FileNotFoundError(input_path)

    paths = artifact_paths(input_path, output_dir)
    convert_pdf(
        input_path,
        markdown_path=paths["markdown"],
        page_markers=True,
        manifest_path=paths["manifest"],
        structured_path=paths["structured"],
    )

    structured = load_structured_json(paths["structured"])
    mentions_payload = build_extraction_payload(
        structured,
        paths["structured"],
        paths["mentions"],
        include_noise=False,
    )
    validate_mentions(mentions_payload)
    write_json(paths["mentions"], mentions_payload)

    report = audit(paths["manifest"], paths["structured"], paths["mentions"])
    paths["audit"].parent.mkdir(parents=True, exist_ok=True)
    paths["audit"].write_text("\n".join(report) + "\n", encoding="utf-8")

    summary = summarize(paths)
    summary["load_dry_run"] = dry_run_summary(
        paths["manifest"], paths["structured"], paths["mentions"]
    )
    if verify_pilot_baseline:
        verify_pilot(summary)
        summary["pilot_baseline_verified"] = True

    if dsn:
        summary["database"] = load_all(
            dsn,
            paths["manifest"],
            paths["structured"],
            paths["mentions"],
            source_name,
            source_kind,
        )

    paths["summary"].write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {"paths": paths, "summary": summary, "audit": report}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Processa, extrai, valida e audita uma edição do DODF."
    )
    parser.add_argument("input", type=Path, help="PDF de entrada")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(".artifacts/pipeline"),
        help="raiz dos artefatos gerados",
    )
    parser.add_argument(
        "--verify-pilot-baseline",
        action="store_true",
        help="exige as contagens e o hash do piloto DODF 112",
    )
    parser.add_argument(
        "--load-db",
        action="store_true",
        help="carrega o resultado no PostgreSQL usando DATABASE_URL",
    )
    parser.add_argument("--source-name", default="DODF")
    parser.add_argument("--source-kind", default="diario_oficial")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    dsn = os.getenv("DATABASE_URL") if args.load_db else None
    if args.load_db and not dsn:
        print("Erro: DATABASE_URL é obrigatória com --load-db.", file=sys.stderr)
        return 2

    try:
        result = run_pipeline(
            args.input,
            args.output_dir,
            verify_pilot_baseline=args.verify_pilot_baseline,
            dsn=dsn,
            source_name=args.source_name,
            source_kind=args.source_kind,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    for line in result["audit"]:
        print(line)
    print(f"Resumo: {result['paths']['summary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
