"""Persistência da projeção semântica navegável."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from psycopg.types.json import Jsonb

from min_df.ledger import link_io, sha256_file, upsert_artifact, upsert_run


def load_semantic_projection(
    conn: Any,
    *,
    ledger_capture_id: int,
    block_db_ids: dict[str, int],
    structured_path: Path,
    semantic_path: Path,
    semantic: dict[str, Any],
) -> dict[str, int]:
    structured_hash = sha256_file(structured_path)
    structured_artifact_id = int(
        conn.execute(
            "SELECT id FROM artifacts WHERE sha256 = %s AND artifact_type = 'structured_document'",
            (structured_hash,),
        ).fetchone()[0]
    )
    semantic_artifact_id = upsert_artifact(
        conn,
        semantic_path,
        "semantic_document",
        "application/json",
        semantic["schema_version"],
    )
    semantic_hash = sha256_file(semantic_path)
    transformation_run_id = upsert_run(
        conn,
        run_key=f"semantic:{semantic_hash}",
        capture_id=ledger_capture_id,
        transformation_type="semantic_segmentation",
        tool=semantic["tool"],
        parameters={"contract": "semantic-document/1.0"},
        completed_at=semantic["created_at"],
    )
    link_io(
        conn,
        transformation_run_id,
        structured_artifact_id,
        "input",
        "structured_document",
    )
    link_io(conn, transformation_run_id, semantic_artifact_id, "output", "semantic_document")

    semantic_run_id = int(
        conn.execute(
            """
            INSERT INTO semantic_runs (transformation_run_id, schema_version, counts)
            VALUES (%s, %s, %s)
            ON CONFLICT (transformation_run_id) DO UPDATE
            SET schema_version = EXCLUDED.schema_version, counts = EXCLUDED.counts
            RETURNING id
            """,
            (transformation_run_id, semantic["schema_version"], Jsonb(semantic["counts"])),
        ).fetchone()[0]
    )

    conn.execute(
        "DELETE FROM semantic_entity_mentions WHERE semantic_run_id = %s",
        (semantic_run_id,),
    )
    conn.execute("DELETE FROM semantic_references WHERE semantic_run_id = %s", (semantic_run_id,))
    conn.execute(
        "DELETE FROM administrative_action_participants WHERE action_id IN "
        "(SELECT aa.id FROM administrative_actions aa JOIN published_items pi "
        "ON pi.id = aa.published_item_id WHERE pi.semantic_run_id = %s)",
        (semantic_run_id,),
    )
    conn.execute(
        "DELETE FROM administrative_actions WHERE published_item_id IN "
        "(SELECT id FROM published_items WHERE semantic_run_id = %s)",
        (semantic_run_id,),
    )
    conn.execute(
        "DELETE FROM semantic_provisions WHERE published_item_id IN "
        "(SELECT id FROM published_items WHERE semantic_run_id = %s)",
        (semantic_run_id,),
    )
    conn.execute(
        "DELETE FROM published_item_blocks WHERE published_item_id IN "
        "(SELECT id FROM published_items WHERE semantic_run_id = %s)",
        (semantic_run_id,),
    )
    conn.execute("DELETE FROM published_items WHERE semantic_run_id = %s", (semantic_run_id,))
    conn.execute(
        "DELETE FROM editorial_context_blocks WHERE context_id IN "
        "(SELECT id FROM editorial_contexts WHERE semantic_run_id = %s)",
        (semantic_run_id,),
    )
    conn.execute("DELETE FROM editorial_contexts WHERE semantic_run_id = %s", (semantic_run_id,))
    conn.execute("DELETE FROM editorial_sections WHERE semantic_run_id = %s", (semantic_run_id,))

    section_ids: dict[str, int] = {}
    for section in semantic["sections"]:
        row = conn.execute(
            """
            INSERT INTO editorial_sections (
                semantic_run_id, section_key, label, start_block_id, start_page
            ) VALUES (%s, %s, %s, %s, %s) RETURNING id
            """,
            (
                semantic_run_id,
                section["id"],
                section["label"],
                block_db_ids[section["start_block_id"]],
                section["start_page"],
            ),
        ).fetchone()
        section_ids[section["id"]] = int(row[0])

    for context in semantic["editorial_contexts"]:
        context_id = int(
            conn.execute(
                """
                INSERT INTO editorial_contexts (
                    semantic_run_id, section_id, context_key, level, label,
                    breadcrumb, kind
                ) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
                """,
                (
                    semantic_run_id,
                    section_ids[context["section_id"]],
                    context["id"],
                    context["level"],
                    context["label"],
                    Jsonb(context["breadcrumb"]),
                    context["kind"],
                ),
            ).fetchone()[0]
        )
        for ordinal, block_id in enumerate(context["block_ids"], start=1):
            conn.execute(
                "INSERT INTO editorial_context_blocks (context_id, block_id, ordinal) "
                "VALUES (%s, %s, %s)",
                (context_id, block_db_ids[block_id], ordinal),
            )

    item_ids: dict[str, int] = {}
    for item in semantic["published_items"]:
        item_id = int(
            conn.execute(
                """
                INSERT INTO published_items (
                    semantic_run_id, section_id, item_key, item_type, title,
                    item_number, date_literal, start_page, end_page, breadcrumb,
                    text_content, act_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    semantic_run_id,
                    section_ids[item["section_id"]],
                    item["id"],
                    item["item_type"],
                    item["title"],
                    item["number"],
                    item["date_literal"],
                    item["start_page"],
                    item["end_page"],
                    Jsonb(item["breadcrumb"]),
                    item["text"],
                    item["act_date"],
                ),
            ).fetchone()[0]
        )
        item_ids[item["id"]] = item_id
        for ordinal, block_id in enumerate(item["block_ids"], start=1):
            conn.execute(
                "INSERT INTO published_item_blocks (published_item_id, block_id, ordinal) "
                "VALUES (%s, %s, %s)",
                (item_id, block_db_ids[block_id], ordinal),
            )

    for provision in semantic["provisions"]:
        conn.execute(
            """
            INSERT INTO semantic_provisions (
                published_item_id, block_id, provision_key, kind, label,
                char_start, char_end
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                item_ids[provision["item_id"]],
                block_db_ids[provision["block_id"]],
                provision["id"],
                provision["kind"],
                provision["label"],
                provision["start"],
                provision["end"],
            ),
        )

    action_ids: dict[str, int] = {}
    for action in semantic["actions"]:
        action_id = int(
            conn.execute(
                """
            INSERT INTO administrative_actions (
                published_item_id, block_id, action_key, verb, value_original,
                char_start, char_end, observation_status, method
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
                (
                    item_ids[action["item_id"]],
                    block_db_ids[action["block_id"]],
                    action["id"],
                    action["verb"],
                    action["value_original"],
                    action["start"],
                    action["end"],
                    action["status"],
                    action["method"],
                ),
            ).fetchone()[0]
        )
        action_ids[action["id"]] = action_id

    entity_ids: dict[str, int] = {}
    for entity in semantic["entity_mentions"]:
        entity_id = int(
            conn.execute(
                """
            INSERT INTO semantic_entity_mentions (
                semantic_run_id, published_item_id, block_id, mention_key,
                entity_type, value_original, value_normalized,
                participation_role, char_start, char_end, method
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
                (
                    semantic_run_id,
                    item_ids.get(entity["item_id"]),
                    block_db_ids[entity["block_id"]],
                    entity["id"],
                    entity["entity_type"],
                    entity["value_original"],
                    entity["value_normalized"],
                    entity["role"],
                    entity["start"],
                    entity["end"],
                    entity["method"],
                ),
            ).fetchone()[0]
        )
        entity_ids[entity["id"]] = entity_id

    for entity in semantic["entity_mentions"]:
        prefix = "subject_of:"
        if entity["role"].startswith(prefix):
            action_key = entity["role"][len(prefix) :]
            conn.execute(
                """
                INSERT INTO administrative_action_participants (
                    action_id, entity_mention_id, participant_role
                ) VALUES (%s, %s, 'subject')
                """,
                (action_ids[action_key], entity_ids[entity["id"]]),
            )

    for reference in semantic["references"]:
        conn.execute(
            """
            INSERT INTO semantic_references (
                semantic_run_id, published_item_id, block_id, reference_key,
                reference_type, value_original, value_normalized, is_valid,
                char_start, char_end, method
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                semantic_run_id,
                item_ids[reference["item_id"]],
                block_db_ids[reference["block_id"]],
                reference["id"],
                reference["reference_type"],
                reference["value_original"],
                reference["value_normalized"],
                reference["valid"],
                reference["start"],
                reference["end"],
                reference["method"],
            ),
        )

    return {
        "semantic_run_id": semantic_run_id,
        "semantic_artifact_id": semantic_artifact_id,
        "semantic_transformation_run_id": transformation_run_id,
        "sections": len(semantic["sections"]),
        "contexts": len(semantic["editorial_contexts"]),
        "published_items": len(semantic["published_items"]),
        "actions": len(semantic["actions"]),
        "entity_mentions": len(semantic["entity_mentions"]),
        "references": len(semantic["references"]),
    }
