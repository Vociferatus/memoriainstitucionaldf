"""Extrai mencoes deterministicas a partir do JSON estrutural do DODF.

Este passo nao interpreta o conteudo administrativo. Ele apenas localiza
padroes textuais com regras versionadas e guarda a evidencia do bloco onde a
mencao apareceu.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from min_df.contracts import validate_mentions, validate_structured

SCRIPT_VERSION = "0.1.0"
OUTPUT_SCHEMA_VERSION = "1.0"

SPACE_RE = re.compile(r"\s+")
PROCESSO_SEI_RE = re.compile(
    r"\b\d{5}\s*-\s*\d{8}\s*/\s*\d{4}\s*-\s*\d{2}\b"
)
PROCESSO_SEI_RULE = {
    "name": "processo_sei",
    "version": "1.0.0",
    "pattern": PROCESSO_SEI_RE.pattern,
}


@dataclass(frozen=True)
class Mention:
    id: str
    type: str
    value_original: str
    value_normalized: str
    page: int
    block_id: str
    block_order: int
    block_bbox: list[float]
    text_field: str
    start: int
    end: int
    snippet: str
    rule: dict[str, str]


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def normalize_spaces(text: str) -> str:
    return SPACE_RE.sub(" ", text).strip()


def normalize_processo_sei(value: str) -> str:
    normalized = re.sub(r"\s*-\s*", "-", value)
    normalized = re.sub(r"\s*/\s*", "/", normalized)
    return normalized.strip()


def make_snippet(text: str, start: int, end: int, radius: int = 90) -> str:
    snippet_start = max(0, start - radius)
    snippet_end = min(len(text), end + radius)
    prefix = "..." if snippet_start > 0 else ""
    suffix = "..." if snippet_end < len(text) else ""
    return prefix + normalize_spaces(text[snippet_start:snippet_end]) + suffix


def iter_blocks(structured: dict[str, Any], include_noise: bool) -> Iterable[dict[str, Any]]:
    for page in structured.get("pages", []):
        for block in page.get("blocks", []):
            if block.get("removed_as_noise") and not include_noise:
                continue
            yield block


def extract_processos_sei(
    structured: dict[str, Any], include_noise: bool = False
) -> list[Mention]:
    mentions: list[Mention] = []

    for block in iter_blocks(structured, include_noise=include_noise):
        text = block.get("text_normalized") or block.get("text_original") or ""
        if not text:
            continue

        for match in PROCESSO_SEI_RE.finditer(text):
            mention_number = len(mentions) + 1
            mentions.append(
                Mention(
                    id=f"processo_sei-{mention_number:06d}",
                    type="processo_sei",
                    value_original=match.group(0),
                    value_normalized=normalize_processo_sei(match.group(0)),
                    page=int(block["page"]),
                    block_id=str(block["id"]),
                    block_order=int(block["order"]),
                    block_bbox=list(block.get("bbox", [])),
                    text_field="text_normalized",
                    start=match.start(),
                    end=match.end(),
                    snippet=make_snippet(text, match.start(), match.end()),
                    rule=PROCESSO_SEI_RULE,
                )
            )

    return mentions


def default_output_path(input_path: Path) -> Path:
    stem = input_path.stem
    if stem.endswith(".structured"):
        stem = stem[: -len(".structured")]
    return Path("data/extractions") / f"{stem}.mentions.json"


def build_extraction_payload(
    structured: dict[str, Any],
    structured_path: Path,
    output_path: Path,
    include_noise: bool,
) -> dict[str, Any]:
    mentions = extract_processos_sei(structured, include_noise=include_noise)
    source = structured.get("source", {})

    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "created_at": utc_now(),
        "tool": {
            "name": "extract_mentions.py",
            "version": SCRIPT_VERSION,
        },
        "source": {
            "structured_path": str(structured_path),
            "document_path": source.get("path"),
            "document_filename": source.get("filename"),
            "document_sha256": source.get("sha256"),
            "document_page_count": source.get("page_count"),
            "structured_schema_version": structured.get("schema_version"),
        },
        "processing": {
            "include_noise": include_noise,
            "output_path": str(output_path),
            "extractors": [PROCESSO_SEI_RULE],
        },
        "counts": {
            "mentions_total": len(mentions),
            "processo_sei": len(mentions),
            "unique_processo_sei": len({m.value_normalized for m in mentions}),
        },
        "mentions": [asdict(mention) for mention in mentions],
    }


def load_structured_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Arquivo nao encontrado: {path}") from None
    except json.JSONDecodeError as exc:
        raise SystemExit(f"JSON invalido em {path}: {exc}") from exc
    validate_structured(payload)
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extrai mencoes deterministicas do JSON estrutural do DODF."
    )
    parser.add_argument(
        "structured_json",
        type=Path,
        help="JSON estrutural gerado por scripts/dodf_to_markdown.py.",
    )
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        help="Arquivo de saida. Padrao: data/extractions/<nome>.mentions.json.",
    )
    parser.add_argument(
        "--include-noise",
        action="store_true",
        help="Inclui blocos marcados como ruido pelo estruturador.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    structured_path = args.structured_json
    output_path = args.output or default_output_path(structured_path)

    structured = load_structured_json(structured_path)
    payload = build_extraction_payload(
        structured=structured,
        structured_path=structured_path,
        output_path=output_path,
        include_noise=args.include_noise,
    )
    validate_mentions(payload)
    write_json(output_path, payload)

    print(f"Extracao concluida: {payload['counts']['mentions_total']} mencoes")
    print(f"Processos SEI unicos: {payload['counts']['unique_processo_sei']}")
    print(f"Saida: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
