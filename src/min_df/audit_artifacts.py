"""Resume artefatos gerados para uma edicao processada.

Este script e uma ferramenta de conferencia: ele nao modifica dados. A ideia e
dar uma visao curta do manifesto, da estrutura documental e das extracoes.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from min_df.contracts import validate_manifest, validate_mentions, validate_structured


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Arquivo nao encontrado: {path}") from None
    except json.JSONDecodeError as exc:
        raise SystemExit(f"JSON invalido em {path}: {exc}") from exc


def audit(manifest_path: Path, structured_path: Path, mentions_path: Path) -> list[str]:
    manifest = read_json(manifest_path)
    structured = read_json(structured_path)
    mentions_payload = read_json(mentions_path)
    validate_manifest(manifest)
    validate_structured(structured)
    validate_mentions(mentions_payload)

    pages = structured.get("pages", [])
    blocks = [block for page in pages for block in page.get("blocks", [])]
    block_ids = {block.get("id") for block in blocks}
    mentions = mentions_payload.get("mentions", [])
    missing_blocks = [
        mention for mention in mentions if mention.get("block_id") not in block_ids
    ]
    mention_types = Counter(mention.get("type") for mention in mentions)
    pages_with_mentions = {mention.get("page") for mention in mentions}

    document = manifest.get("document", {})
    lines = [
        "Auditoria dos artefatos",
        "",
        f"Arquivo bruto: {document.get('filename')}",
        f"SHA-256: {document.get('sha256')}",
        f"Paginas no manifesto: {document.get('page_count')}",
        f"Paginas estruturadas: {len(pages)}",
        f"Blocos estruturados: {len(blocks)}",
        f"Blocos marcados como ruido: {sum(1 for b in blocks if b.get('removed_as_noise'))}",
        "",
        f"Mencoes extraidas: {len(mentions)}",
        f"Paginas com mencoes: {len(pages_with_mentions)}",
        f"Mencoes sem bloco correspondente: {len(missing_blocks)}",
    ]

    if mention_types:
        lines.append("")
        lines.append("Tipos de mencao:")
        for mention_type, count in mention_types.most_common():
            lines.append(f"- {mention_type}: {count}")

    examples = mentions[:5]
    if examples:
        lines.append("")
        lines.append("Primeiros exemplos:")
        for mention in examples:
            lines.append(
                "- "
                f"{mention.get('value_original')} -> "
                f"{mention.get('value_normalized')} "
                f"(pagina {mention.get('page')}, bloco {mention.get('block_id')})"
            )

    return lines


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resume manifesto, JSON estrutural e extracoes."
    )
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--structured", required=True, type=Path)
    parser.add_argument("--mentions", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    print("\n".join(audit(args.manifest, args.structured, args.mentions)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
