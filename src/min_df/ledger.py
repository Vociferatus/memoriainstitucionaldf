"""Persistência do ledger de evidências v2."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from psycopg.types.json import Jsonb


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def portable_uri(path: Path, root: Path | None = None) -> str:
    """Produz URI estável sem persistir um caminho absoluto da máquina."""
    root = (root or Path.cwd()).resolve()
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError:
        return f"urn:sha256:{sha256_file(resolved)}"
    return f"repo:///{relative.as_posix()}"


def upsert_artifact(
    conn: Any,
    path: Path,
    artifact_type: str,
    media_type: str,
    schema_version: str | None = None,
) -> int:
    digest = sha256_file(path)
    row = conn.execute(
        """
        INSERT INTO artifacts (
            artifact_key, sha256, size_bytes, media_type, artifact_type,
            schema_version, storage_uri
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (sha256, artifact_type) DO UPDATE
        SET size_bytes = EXCLUDED.size_bytes,
            media_type = EXCLUDED.media_type,
            schema_version = EXCLUDED.schema_version,
            storage_uri = EXCLUDED.storage_uri
        RETURNING id
        """,
        (
            f"{artifact_type}:sha256:{digest}",
            digest,
            path.stat().st_size,
            media_type,
            artifact_type,
            schema_version,
            portable_uri(path),
        ),
    ).fetchone()
    return int(row[0])


def link_io(conn: Any, run_id: int, artifact_id: int, direction: str, role: str) -> None:
    conn.execute(
        """
        INSERT INTO transformation_io (
            transformation_run_id, artifact_id, direction, role
        ) VALUES (%s, %s, %s, %s)
        ON CONFLICT (transformation_run_id, direction, role, ordinal) DO UPDATE
        SET artifact_id = EXCLUDED.artifact_id
        """,
        (run_id, artifact_id, direction, role),
    )


def upsert_run(
    conn: Any,
    *,
    run_key: str,
    capture_id: int,
    transformation_type: str,
    tool: dict[str, Any],
    parameters: dict[str, Any],
    completed_at: str,
) -> int:
    row = conn.execute(
        """
        INSERT INTO transformation_runs (
            run_key, capture_id, transformation_type, tool_name, tool_version,
            parameters, completed_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (run_key) DO UPDATE
        SET capture_id = EXCLUDED.capture_id,
            parameters = EXCLUDED.parameters,
            completed_at = EXCLUDED.completed_at
        RETURNING id
        """,
        (
            run_key,
            capture_id,
            transformation_type,
            tool["name"],
            tool["version"],
            Jsonb(parameters),
            completed_at,
        ),
    ).fetchone()
    return int(row[0])


def load_ledger_v2(
    conn: Any,
    *,
    source_id: int,
    document_id: int,
    legacy_capture_id: int,
    block_db_ids: dict[str, int],
    manifest_path: Path,
    structured_path: Path,
    mentions_path: Path,
    manifest: dict[str, Any],
    structured: dict[str, Any],
    mentions_payload: dict[str, Any],
) -> dict[str, int]:
    """Registra linhagem completa mantendo as tabelas legadas disponíveis."""
    document = manifest["document"]
    source_policy_id = int(
        conn.execute(
            """
            INSERT INTO source_policies (
                source_id, policy_version, authority_uri, collection_policy,
                effective_from
            ) VALUES (%s, '1.0', %s, %s, '2026-01-01T00:00:00Z')
            ON CONFLICT (source_id, policy_version) DO UPDATE
            SET authority_uri = EXCLUDED.authority_uri,
                collection_policy = EXCLUDED.collection_policy
            RETURNING id
            """,
            (
                source_id,
                "https://www.dodf.df.gov.br/",
                Jsonb({"authority": "Diário Oficial do Distrito Federal"}),
            ),
        ).fetchone()[0]
    )

    blob_id = int(
        conn.execute(
            """
            INSERT INTO blobs (sha256, size_bytes, media_type, storage_uri)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (sha256) DO UPDATE
            SET size_bytes = EXCLUDED.size_bytes,
                media_type = EXCLUDED.media_type
            RETURNING id
            """,
            (
                document["sha256"],
                document["size_bytes"],
                document["media_type"],
                f"urn:sha256:{document['sha256']}",
            ),
        ).fetchone()[0]
    )

    manifest_hash = sha256_file(manifest_path)
    capture_key = f"manifest:sha256:{manifest_hash}"
    capture_id = int(
        conn.execute(
            """
            INSERT INTO captures (
                capture_key, document_id, blob_id, source_policy_id, capture_uri,
                captured_at, observed_filename, metadata, legacy_capture_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (legacy_capture_id) DO UPDATE
            SET capture_key = EXCLUDED.capture_key,
                document_id = EXCLUDED.document_id,
                blob_id = EXCLUDED.blob_id,
                source_policy_id = EXCLUDED.source_policy_id,
                metadata = EXCLUDED.metadata,
                legacy_capture_id = EXCLUDED.legacy_capture_id
            RETURNING id
            """,
            (
                capture_key,
                document_id,
                blob_id,
                source_policy_id,
                portable_uri(manifest_path) + "#capture",
                manifest["created_at"],
                document["filename"],
                Jsonb({"manifest_uri": portable_uri(manifest_path)}),
                legacy_capture_id,
            ),
        ).fetchone()[0]
    )

    raw_path = Path("data/raw") / document["filename"]
    raw_artifact_id = upsert_artifact(
        conn, raw_path, "raw_document", document["media_type"]
    )
    manifest_artifact_id = upsert_artifact(
        conn, manifest_path, "manifest", "application/json", manifest["schema_version"]
    )
    structured_artifact_id = upsert_artifact(
        conn,
        structured_path,
        "structured_document",
        "application/json",
        structured["schema_version"],
    )
    mentions_artifact_id = upsert_artifact(
        conn,
        mentions_path,
        "mentions",
        "application/json",
        mentions_payload["schema_version"],
    )
    markdown_path = Path(manifest["derived_outputs"]["markdown"].replace("\\", "/"))
    markdown_artifact_id = upsert_artifact(
        conn, markdown_path, "human_readable_markdown", "text/markdown"
    )

    structured_hash = sha256_file(structured_path)
    conversion_run_id = upsert_run(
        conn,
        run_key=f"conversion:{structured_hash}:{manifest_hash}",
        capture_id=capture_id,
        transformation_type="document_conversion",
        tool=manifest["tool"],
        parameters=structured.get("processing", {}),
        completed_at=manifest["created_at"],
    )
    link_io(conn, conversion_run_id, raw_artifact_id, "input", "raw_document")
    link_io(conn, conversion_run_id, manifest_artifact_id, "output", "manifest")
    link_io(conn, conversion_run_id, structured_artifact_id, "output", "structured_document")
    link_io(conn, conversion_run_id, markdown_artifact_id, "output", "markdown")

    mentions_hash = sha256_file(mentions_path)
    extraction_run_id = upsert_run(
        conn,
        run_key=f"extraction:{mentions_hash}",
        capture_id=capture_id,
        transformation_type="mention_extraction",
        tool=mentions_payload["tool"],
        parameters=mentions_payload["processing"],
        completed_at=mentions_payload["created_at"],
    )
    link_io(conn, extraction_run_id, structured_artifact_id, "input", "structured_document")
    link_io(conn, extraction_run_id, mentions_artifact_id, "output", "mentions")

    conn.execute(
        "DELETE FROM evidence_mentions WHERE transformation_run_id = %s",
        (extraction_run_id,),
    )
    for mention in mentions_payload["mentions"]:
        conn.execute(
            """
            INSERT INTO evidence_mentions (
                transformation_run_id, block_id, mention_key, mention_type,
                value_original, value_normalized, text_field, char_start,
                char_end, snippet, rule, raw
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                extraction_run_id,
                block_db_ids[mention["block_id"]],
                mention["id"],
                mention["type"],
                mention["value_original"],
                mention["value_normalized"],
                mention["text_field"],
                mention["start"],
                mention["end"],
                mention["snippet"],
                Jsonb(mention["rule"]),
                Jsonb(mention),
            ),
        )

    return {
        "blob_id": blob_id,
        "ledger_capture_id": capture_id,
        "conversion_run_id": conversion_run_id,
        "ledger_extraction_run_id": extraction_run_id,
        "artifacts": 5,
        "evidence_mentions": len(mentions_payload["mentions"]),
    }
