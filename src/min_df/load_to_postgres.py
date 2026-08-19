"""Carrega uma edicao estruturada do DODF e suas mencoes no PostgreSQL.

Entrada esperada:
- manifesto gerado por scripts/dodf_to_markdown.py;
- JSON estrutural gerado pelo mesmo passo;
- JSON de mencoes gerado por scripts/extract_mentions.py.

O carregamento e idempotente para documento, captura, paginas, blocos e rodada
de extracao. Mencoes da mesma rodada sao substituidas antes da nova insercao.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from min_df.contracts import (
    validate_identity,
    validate_manifest,
    validate_mentions,
    validate_semantic,
    validate_structured,
)
from min_df.identity_store import load_identity_projection
from min_df.ledger import load_ledger_v2
from min_df.semantic_store import load_semantic_projection

SCRIPT_VERSION = "0.1.0"
DODF_FILENAME_RE = re.compile(
    r"^DODF\s+(?P<edition>\d+)\s+"
    r"(?P<day>\d{2})-(?P<month>\d{2})-(?P<year>\d{4})"
    r"(?:\s+(?P<suffix>.+))?$",
    re.IGNORECASE,
)


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Arquivo nao encontrado: {path}") from None
    except json.JSONDecodeError as exc:
        raise SystemExit(f"JSON invalido em {path}: {exc}") from exc


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_dodf_filename(filename: str) -> dict[str, Any]:
    stem = Path(filename).stem
    match = DODF_FILENAME_RE.match(stem)
    if not match:
        return {
            "document_key": f"dodf:{stem.lower()}",
            "title": stem,
            "document_type": "DODF",
            "publication_date": None,
            "edition_number": None,
        }

    parts = match.groupdict()
    publication_date = date(
        int(parts["year"]),
        int(parts["month"]),
        int(parts["day"]),
    )
    suffix = (parts.get("suffix") or "").strip().lower().replace(" ", "-")
    suffix_key = f":{suffix}" if suffix else ""
    document_key = f"dodf:{publication_date.isoformat()}:edicao-{parts['edition']}{suffix_key}"

    return {
        "document_key": document_key,
        "title": stem,
        "document_type": "DODF",
        "publication_date": publication_date,
        "edition_number": parts["edition"],
    }


def require_psycopg() -> None:
    """Mantém um ponto explícito de verificação para compatibilidade da API."""


def upsert_source(conn: Any, name: str, kind: str) -> int:
    row = conn.execute(
        """
        INSERT INTO sources (name, kind)
        VALUES (%s, %s)
        ON CONFLICT (name, kind) DO UPDATE
        SET name = EXCLUDED.name
        RETURNING id
        """,
        (name, kind),
    ).fetchone()
    return int(row[0])


def upsert_document(conn: Any, source_id: int, doc_info: dict[str, Any]) -> int:
    row = conn.execute(
        """
        INSERT INTO documents (
            source_id, document_key, title, document_type,
            publication_date, edition_number, metadata
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (document_key) DO UPDATE
        SET source_id = EXCLUDED.source_id,
            title = EXCLUDED.title,
            document_type = EXCLUDED.document_type,
            publication_date = EXCLUDED.publication_date,
            edition_number = EXCLUDED.edition_number,
            metadata = EXCLUDED.metadata,
            updated_at = now()
        RETURNING id
        """,
        (
            source_id,
            doc_info["document_key"],
            doc_info["title"],
            doc_info["document_type"],
            doc_info["publication_date"],
            doc_info["edition_number"],
            Jsonb(doc_info.get("metadata", {})),
        ),
    ).fetchone()
    return int(row[0])


def upsert_capture(
    conn: Any,
    document_id: int,
    manifest_path: Path,
    manifest: dict[str, Any],
) -> int:
    document = manifest["document"]
    sha256 = document["sha256"]
    row = conn.execute(
        """
        INSERT INTO document_captures (
            document_id, capture_key, raw_path, filename, media_type,
            size_bytes, sha256, page_count, captured_at, file_modified_at,
            manifest_path, metadata
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (sha256) DO UPDATE
        SET document_id = EXCLUDED.document_id,
            capture_key = EXCLUDED.capture_key,
            raw_path = EXCLUDED.raw_path,
            filename = EXCLUDED.filename,
            media_type = EXCLUDED.media_type,
            size_bytes = EXCLUDED.size_bytes,
            page_count = EXCLUDED.page_count,
            captured_at = EXCLUDED.captured_at,
            file_modified_at = EXCLUDED.file_modified_at,
            manifest_path = EXCLUDED.manifest_path,
            metadata = EXCLUDED.metadata
        RETURNING id
        """,
        (
            document_id,
            f"sha256:{sha256}",
            document["path"],
            document["filename"],
            document["media_type"],
            document["size_bytes"],
            sha256,
            document.get("page_count"),
            manifest.get("created_at"),
            document.get("modified_at"),
            str(manifest_path),
            Jsonb(manifest),
        ),
    ).fetchone()
    return int(row[0])


def load_pages_and_blocks(
    conn: Any,
    capture_id: int,
    structured: dict[str, Any],
) -> dict[str, int]:
    block_db_ids: dict[str, int] = {}

    for page in structured.get("pages", []):
        conn.execute(
            """
            INSERT INTO document_pages (
                capture_id, page_number, width, height, rotation, metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (capture_id, page_number) DO UPDATE
            SET width = EXCLUDED.width,
                height = EXCLUDED.height,
                rotation = EXCLUDED.rotation,
                metadata = EXCLUDED.metadata
            """,
            (
                capture_id,
                page["number"],
                page.get("width"),
                page.get("height"),
                page.get("rotation"),
                Jsonb({k: v for k, v in page.items() if k != "blocks"}),
            ),
        )

        for block in page.get("blocks", []):
            row = conn.execute(
                """
                INSERT INTO document_blocks (
                    capture_id, page_number, block_id, block_order, source_order,
                    column_number, bbox, text_original, text_normalized,
                    font_size, bold, markdown_role, removed_as_noise,
                    noise_reason, raw
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (capture_id, block_id) DO UPDATE
                SET page_number = EXCLUDED.page_number,
                    block_order = EXCLUDED.block_order,
                    source_order = EXCLUDED.source_order,
                    column_number = EXCLUDED.column_number,
                    bbox = EXCLUDED.bbox,
                    text_original = EXCLUDED.text_original,
                    text_normalized = EXCLUDED.text_normalized,
                    font_size = EXCLUDED.font_size,
                    bold = EXCLUDED.bold,
                    markdown_role = EXCLUDED.markdown_role,
                    removed_as_noise = EXCLUDED.removed_as_noise,
                    noise_reason = EXCLUDED.noise_reason,
                    raw = EXCLUDED.raw
                RETURNING id
                """,
                (
                    capture_id,
                    block["page"],
                    block["id"],
                    block["order"],
                    block.get("source_order"),
                    block.get("column"),
                    block.get("bbox", []),
                    block.get("text_original", ""),
                    block.get("text_normalized", ""),
                    block.get("font_size"),
                    block.get("bold", False),
                    block.get("markdown_role"),
                    block.get("removed_as_noise", False),
                    block.get("noise_reason"),
                    Jsonb(block),
                ),
            ).fetchone()
            block_db_ids[block["id"]] = int(row[0])

    return block_db_ids


def upsert_extraction_run(
    conn: Any,
    capture_id: int,
    structured_path: Path,
    mentions_path: Path,
    mentions_payload: dict[str, Any],
) -> int:
    tool = mentions_payload["tool"]
    processing = mentions_payload["processing"]
    run_key = f"extraction:{file_sha256(mentions_path)}"

    row = conn.execute(
        """
        INSERT INTO extraction_runs (
            capture_id, run_key, tool_name, tool_version, schema_version,
            structured_path, output_path, include_noise, extractors, counts,
            created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (run_key) DO UPDATE
        SET capture_id = EXCLUDED.capture_id,
            tool_name = EXCLUDED.tool_name,
            tool_version = EXCLUDED.tool_version,
            schema_version = EXCLUDED.schema_version,
            structured_path = EXCLUDED.structured_path,
            output_path = EXCLUDED.output_path,
            include_noise = EXCLUDED.include_noise,
            extractors = EXCLUDED.extractors,
            counts = EXCLUDED.counts,
            created_at = EXCLUDED.created_at,
            loaded_at = now()
        RETURNING id
        """,
        (
            capture_id,
            run_key,
            tool["name"],
            tool["version"],
            mentions_payload["schema_version"],
            str(structured_path),
            processing.get("output_path") or str(mentions_path),
            processing.get("include_noise", False),
            Jsonb(processing.get("extractors", [])),
            Jsonb(mentions_payload.get("counts", {})),
            mentions_payload["created_at"],
        ),
    ).fetchone()
    return int(row[0])


def replace_mentions(
    conn: Any,
    extraction_run_id: int,
    capture_id: int,
    block_db_ids: dict[str, int],
    mentions_payload: dict[str, Any],
) -> int:
    conn.execute("DELETE FROM mentions WHERE extraction_run_id = %s", (extraction_run_id,))

    inserted = 0
    for mention in mentions_payload.get("mentions", []):
        block_ref = mention["block_id"]
        block_db_id = block_db_ids.get(block_ref)
        if block_db_id is None:
            raise SystemExit(f"Bloco citado pela mencao nao foi carregado: {block_ref}")

        rule = mention["rule"]
        conn.execute(
            """
            INSERT INTO mentions (
                extraction_run_id, capture_id, block_id, mention_key,
                mention_type, value_original, value_normalized, page_number,
                block_ref, block_order, block_bbox, text_field, char_start,
                char_end, snippet, rule_name, rule_version, rule_pattern, raw
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
            """,
            (
                extraction_run_id,
                capture_id,
                block_db_id,
                mention["id"],
                mention["type"],
                mention["value_original"],
                mention["value_normalized"],
                mention["page"],
                block_ref,
                mention["block_order"],
                mention["block_bbox"],
                mention["text_field"],
                mention["start"],
                mention["end"],
                mention["snippet"],
                rule["name"],
                rule["version"],
                rule["pattern"],
                Jsonb(mention),
            ),
        )
        inserted += 1

    return inserted


def load_all(
    dsn: str,
    manifest_path: Path,
    structured_path: Path,
    mentions_path: Path,
    source_name: str,
    source_kind: str,
    semantic_path: Path | None = None,
    identity_path: Path | None = None,
) -> dict[str, int]:
    require_psycopg()

    manifest = read_json(manifest_path)
    structured = read_json(structured_path)
    mentions_payload = read_json(mentions_path)
    semantic_payload = read_json(semantic_path) if semantic_path else None
    identity_payload = read_json(identity_path) if identity_path else None
    validate_manifest(manifest)
    validate_structured(structured)
    validate_mentions(mentions_payload)
    if semantic_payload is not None:
        validate_semantic(semantic_payload)
    if identity_payload is not None:
        if semantic_payload is None or semantic_path is None:
            raise ValueError("A camada de identidade requer a projeção semântica.")
        validate_identity(identity_payload)
    doc_info = parse_dodf_filename(manifest["document"]["filename"])
    doc_info["metadata"] = {
        "manifest_schema_version": manifest.get("schema_version"),
        "manifest_tool": manifest.get("tool"),
        "loader": {"name": "load_to_postgres.py", "version": SCRIPT_VERSION},
    }

    with psycopg.connect(dsn) as conn, conn.transaction():
        source_id = upsert_source(conn, source_name, source_kind)
        document_id = upsert_document(conn, source_id, doc_info)
        capture_id = upsert_capture(conn, document_id, manifest_path, manifest)
        block_db_ids = load_pages_and_blocks(conn, capture_id, structured)
        extraction_run_id = upsert_extraction_run(
            conn,
            capture_id,
            structured_path,
            mentions_path,
            mentions_payload,
        )
        mentions_inserted = replace_mentions(
            conn,
            extraction_run_id,
            capture_id,
            block_db_ids,
            mentions_payload,
        )
        ledger = load_ledger_v2(
            conn,
            source_id=source_id,
            document_id=document_id,
            legacy_capture_id=capture_id,
            block_db_ids=block_db_ids,
            manifest_path=manifest_path,
            structured_path=structured_path,
            mentions_path=mentions_path,
            manifest=manifest,
            structured=structured,
            mentions_payload=mentions_payload,
        )
        semantic_result: dict[str, int] = {}
        if semantic_path is not None and semantic_payload is not None:
            semantic_result = load_semantic_projection(
                conn,
                ledger_capture_id=ledger["ledger_capture_id"],
                block_db_ids=block_db_ids,
                structured_path=structured_path,
                semantic_path=semantic_path,
                semantic=semantic_payload,
            )
        identity_result: dict[str, int] = {}
        if identity_path is not None and identity_payload is not None and semantic_path is not None:
            identity_result = load_identity_projection(
                conn,
                ledger_capture_id=ledger["ledger_capture_id"],
                semantic_run_id=semantic_result["semantic_run_id"],
                block_db_ids=block_db_ids,
                semantic_path=semantic_path,
                mentions_path=mentions_path,
                identity_path=identity_path,
                identity=identity_payload,
            )

    return {
        "source_id": source_id,
        "document_id": document_id,
        "capture_id": capture_id,
        "blocks": len(block_db_ids),
        "extraction_run_id": extraction_run_id,
        "mentions": mentions_inserted,
        **ledger,
        **semantic_result,
        **identity_result,
    }


def dry_run_summary(
    manifest_path: Path,
    structured_path: Path,
    mentions_path: Path,
) -> dict[str, Any]:
    manifest = read_json(manifest_path)
    structured = read_json(structured_path)
    mentions_payload = read_json(mentions_path)
    validate_manifest(manifest)
    validate_structured(structured)
    validate_mentions(mentions_payload)
    doc_info = parse_dodf_filename(manifest["document"]["filename"])
    pages = structured.get("pages", [])
    blocks = sum(len(page.get("blocks", [])) for page in pages)
    mentions = mentions_payload.get("mentions", [])

    missing_blocks = sorted(
        {
            mention["block_id"]
            for mention in mentions
            if not any(
                mention["block_id"] == block.get("id")
                for page in pages
                for block in page.get("blocks", [])
            )
        }
    )

    return {
        "document_key": doc_info["document_key"],
        "document_sha256": manifest["document"]["sha256"],
        "pages": len(pages),
        "blocks": blocks,
        "mentions": len(mentions),
        "missing_blocks": len(missing_blocks),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Carrega manifesto, JSON estrutural e mencoes no PostgreSQL."
    )
    parser.add_argument("--dsn", default=os.getenv("DATABASE_URL"))
    parser.add_argument(
        "--manifest",
        required=True,
        type=Path,
        help="Manifesto da captura.",
    )
    parser.add_argument(
        "--structured",
        required=True,
        type=Path,
        help="JSON estrutural.",
    )
    parser.add_argument(
        "--mentions",
        required=True,
        type=Path,
        help="JSON de mencoes extraidas.",
    )
    parser.add_argument(
        "--semantic",
        type=Path,
        help="JSON semântico opcional para navegação por matérias e entidades.",
    )
    parser.add_argument("--identity", type=Path, help="JSON opcional de identidade material.")
    parser.add_argument("--source-name", default="DODF")
    parser.add_argument("--source-kind", default="diario_oficial")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Valida os arquivos e imprime um resumo sem conectar ao banco.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.dry_run:
        result = dry_run_summary(args.manifest, args.structured, args.mentions)
        print("Dry-run concluido")
        for key, value in result.items():
            print(f"{key}: {value}")
        return 0

    if not args.dsn:
        raise SystemExit("Informe a conexao com --dsn ou pela variavel de ambiente DATABASE_URL.")

    result = load_all(
        dsn=args.dsn,
        manifest_path=args.manifest,
        structured_path=args.structured,
        mentions_path=args.mentions,
        source_name=args.source_name,
        source_kind=args.source_kind,
        semantic_path=args.semantic,
        identity_path=args.identity,
    )

    print("Carga concluida")
    for key, value in result.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
