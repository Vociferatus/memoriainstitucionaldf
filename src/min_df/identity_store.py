"""Persistência da camada de identidade material."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from psycopg.types.json import Jsonb

from min_df.ledger import link_io, sha256_file, upsert_artifact, upsert_run


def load_identity_projection(
    conn: Any,
    *,
    ledger_capture_id: int,
    semantic_run_id: int,
    block_db_ids: dict[str, int],
    semantic_path: Path,
    mentions_path: Path,
    identity_path: Path,
    identity: dict[str, Any],
) -> dict[str, int]:
    input_artifacts = []
    for path, artifact_type in ((semantic_path, "semantic_document"), (mentions_path, "mentions")):
        row = conn.execute(
            "SELECT id FROM artifacts WHERE sha256=%s AND artifact_type=%s",
            (sha256_file(path), artifact_type),
        ).fetchone()
        if row is None:
            raise ValueError(f"Artefato de entrada ausente no ledger: {path}")
        input_artifacts.append((int(row[0]), artifact_type))
    artifact_id = upsert_artifact(
        conn, identity_path, "identity_resolution", "application/json", identity["schema_version"]
    )
    transformation_run_id = upsert_run(
        conn,
        run_key=f"identity:{sha256_file(identity_path)}",
        capture_id=ledger_capture_id,
        transformation_type="material_identity_resolution",
        tool=identity["tool"],
        parameters={"contract": "identity-resolution/1.0", "policy": identity["policy"]},
        completed_at=identity["created_at"],
    )
    for source_id, role in input_artifacts:
        link_io(conn, transformation_run_id, source_id, "input", role)
    link_io(conn, transformation_run_id, artifact_id, "output", "identity_resolution")
    identity_run_id = int(
        conn.execute(
            """INSERT INTO identity_runs(
               transformation_run_id, semantic_run_id, schema_version, policy, counts)
           VALUES(%s,%s,%s,%s,%s) ON CONFLICT(transformation_run_id) DO UPDATE SET
           semantic_run_id=EXCLUDED.semantic_run_id, schema_version=EXCLUDED.schema_version,
           policy=EXCLUDED.policy, counts=EXCLUDED.counts RETURNING id""",
            (
                transformation_run_id,
                semantic_run_id,
                identity["schema_version"],
                Jsonb(identity["policy"]),
                Jsonb(identity["counts"]),
            ),
        ).fetchone()[0]
    )
    conn.execute(
        "DELETE FROM identity_candidate_groups WHERE identity_run_id=%s", (identity_run_id,)
    )
    conn.execute(
        "DELETE FROM identity_resolution_cases WHERE identity_run_id=%s", (identity_run_id,)
    )
    conn.execute("DELETE FROM identity_links WHERE identity_run_id=%s", (identity_run_id,))
    conn.execute("DELETE FROM canonical_entities WHERE identity_run_id=%s", (identity_run_id,))
    conn.execute("DELETE FROM identity_fragments WHERE identity_run_id=%s", (identity_run_id,))
    item_ids = {
        row[0]: int(row[1])
        for row in conn.execute(
            "SELECT item_key,id FROM published_items WHERE semantic_run_id=%s", (semantic_run_id,)
        ).fetchall()
    }
    fragment_ids: dict[str, int] = {}
    for value in identity["fragments"]:
        fragment_ids[value["id"]] = int(
            conn.execute(
                """INSERT INTO identity_fragments(
            identity_run_id,fragment_key,entity_type,source_kind,
            source_key,label,block_id,published_item_id,page_number,char_start,char_end,
            observation_status,method)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                (
                    identity_run_id,
                    value["id"],
                    value["entity_type"],
                    value["source_kind"],
                    value["source_id"],
                    value["label"],
                    block_db_ids[value["block_id"]],
                    item_ids.get(value["item_id"]),
                    value["page"],
                    value["start"],
                    value["end"],
                    value["status"],
                    value["method"],
                ),
            ).fetchone()[0]
        )
    for value in identity["assertions"]:
        conn.execute(
            """INSERT INTO identity_assertions(fragment_id,assertion_key,attribute_name,
        value_original,value_normalized,materiality_class,scope,valid_from,valid_to,method)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                fragment_ids[value["fragment_id"]],
                value["id"],
                value["attribute"],
                value["value_original"],
                value["value_normalized"],
                value["materiality_class"],
                value["scope"],
                value["valid_from"],
                value["valid_to"],
                value["method"],
            ),
        )
    for value in identity["identifiers"]:
        conn.execute(
            """INSERT INTO material_identifiers(fragment_id,identifier_key,identifier_type,
        value_original,value_normalized,materiality_class,scope,is_valid,transferability,method)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                fragment_ids[value["fragment_id"]],
                value["id"],
                value["identifier_type"],
                value["value_original"],
                value["value_normalized"],
                value["materiality_class"],
                value["scope"],
                value["is_valid"],
                value["transferability"],
                value["method"],
            ),
        )
    entity_ids: dict[str, int] = {}
    for value in identity["canonical_entities"]:
        entity_ids[value["id"]] = int(
            conn.execute(
                """INSERT INTO canonical_entities(identity_run_id,
        entity_key,entity_type,display_name,entity_status,materiality_basis,created_by_rule)
        VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                (
                    identity_run_id,
                    value["id"],
                    value["entity_type"],
                    value["display_name"],
                    value["status"],
                    value["materiality_basis"],
                    value["created_by_rule"],
                ),
            ).fetchone()[0]
        )
    for value in identity["identity_links"]:
        conn.execute(
            """INSERT INTO identity_links(identity_run_id,link_key,fragment_id,canonical_entity_id,
        decision,reason,rules,has_divergence,review_status,decision_version)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                identity_run_id,
                value["id"],
                fragment_ids[value["fragment_id"]],
                entity_ids[value["canonical_entity_id"]],
                value["decision"],
                value["reason"],
                Jsonb(value["rules"]),
                value["has_divergence"],
                value["review_status"],
                value["version"],
            ),
        )
    for value in identity["candidate_groups"]:
        group_id = int(
            conn.execute(
                """INSERT INTO identity_candidate_groups(identity_run_id,candidate_key_id,
        entity_type,candidate_key,decision,reason,materiality_classes,missing_evidence)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                (
                    identity_run_id,
                    value["id"],
                    value["entity_type"],
                    value["candidate_key"],
                    value["decision"],
                    value["reason"],
                    Jsonb(value["materiality_classes"]),
                    Jsonb(value["missing_evidence"]),
                ),
            ).fetchone()[0]
        )
        for fragment_id in value["fragment_ids"]:
            conn.execute(
                "INSERT INTO identity_candidate_members VALUES(%s,%s)",
                (group_id, fragment_ids[fragment_id]),
            )
    for value in identity["resolution_cases"]:
        case_id = int(
            conn.execute(
                """INSERT INTO identity_resolution_cases(identity_run_id,case_key,
        entity_type,case_type,case_status,divergences,analysis_chain,recommended_decision,reason)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                (
                    identity_run_id,
                    value["id"],
                    value["entity_type"],
                    value["case_type"],
                    value["status"],
                    Jsonb(value["divergences"]),
                    Jsonb(value["analysis_chain"]),
                    value["recommended_decision"],
                    value["reason"],
                ),
            ).fetchone()[0]
        )
        for fragment_id in value["fragment_ids"]:
            conn.execute(
                "INSERT INTO identity_case_fragments VALUES(%s,%s)",
                (case_id, fragment_ids[fragment_id]),
            )
    return {
        "identity_run_id": identity_run_id,
        "identity_artifact_id": artifact_id,
        **{f"identity_{key}": value for key, value in identity["counts"].items()},
    }
