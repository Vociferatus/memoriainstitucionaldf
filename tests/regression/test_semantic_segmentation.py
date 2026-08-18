from __future__ import annotations

import json
from pathlib import Path

from min_df.semantic import build_semantic_payload


def test_semantic_segmentation_covers_every_block_once(
    pilot_paths: dict[str, Path], project_root: Path
) -> None:
    structured = json.loads(pilot_paths["structured"].read_text(encoding="utf-8"))
    source_path = pilot_paths["structured"].relative_to(project_root)
    semantic = build_semantic_payload(structured, source_path)

    source_block_ids = {block["id"] for page in structured["pages"] for block in page["blocks"]}
    assigned_ids = [item["block_id"] for item in semantic["block_assignments"]]

    assert len(assigned_ids) == 2553
    assert len(set(assigned_ids)) == 2553
    assert set(assigned_ids) == source_block_ids


def test_semantic_pilot_landmarks(pilot_paths: dict[str, Path], project_root: Path) -> None:
    structured = json.loads(pilot_paths["structured"].read_text(encoding="utf-8"))
    semantic = build_semantic_payload(
        structured, pilot_paths["structured"].relative_to(project_root)
    )

    assert [(section["label"], section["start_page"]) for section in semantic["sections"]] == [
        ("SEÇÃO I", 1),
        ("SEÇÃO II", 31),
        ("SEÇÃO III", 50),
    ]
    assert semantic["counts"] == {
        "blocks_total": 2553,
        "sections": 3,
        "contexts": 133,
        "published_items": 403,
        "multi_page_items": 54,
        "unclassified_items": 33,
        "actions": 114,
        "entity_mentions": 218,
        "provisions": 834,
        "references": 1396,
    }

    merged = next(
        context
        for context in semantic["editorial_contexts"]
        if context["label"] == "SECRETARIA DE ESTADO DE GOVERNANÇA DIGITAL E INTEGRAÇÃO"
    )
    assert merged["block_ids"] == ["p0002-b0013", "p0002-b0014"]

    first = semantic["published_items"][0]
    assert first["title"] == "ORDEM DE SERVIÇO Nº 89, DE 16 DE JUNHO DE 2026"
    assert first["breadcrumb"] == [
        "SECRETARIA DE ESTADO DE GOVERNO",
        "SECRETARIA EXECUTIVA DAS CIDADES",
    ]


def test_item_assignments_reference_existing_items(
    pilot_paths: dict[str, Path], project_root: Path
) -> None:
    structured = json.loads(pilot_paths["structured"].read_text(encoding="utf-8"))
    semantic = build_semantic_payload(
        structured, pilot_paths["structured"].relative_to(project_root)
    )
    item_ids = {item["id"] for item in semantic["published_items"]}
    referenced = {
        assignment["item_id"]
        for assignment in semantic["block_assignments"]
        if assignment["category"] == "published_item"
    }
    assert referenced == item_ids


def test_semantic_observations_have_exact_evidence_spans(
    pilot_paths: dict[str, Path], project_root: Path
) -> None:
    structured = json.loads(pilot_paths["structured"].read_text(encoding="utf-8"))
    semantic = build_semantic_payload(
        structured, pilot_paths["structured"].relative_to(project_root)
    )
    block_text = {
        block["id"]: block["text_normalized"]
        for page in structured["pages"]
        for block in page["blocks"]
    }

    for action in semantic["actions"]:
        assert (
            block_text[action["block_id"]][action["start"] : action["end"]]
            == action["value_original"]
        )
        assert action["status"] == "observed_text"
    for entity in semantic["entity_mentions"]:
        assert (
            block_text[entity["block_id"]][entity["start"] : entity["end"]]
            == entity["value_original"]
        )
    for provision in semantic["provisions"]:
        assert (
            block_text[provision["block_id"]][provision["start"] : provision["end"]]
            == provision["label"]
        )
    for reference in semantic["references"]:
        assert (
            block_text[reference["block_id"]][reference["start"] : reference["end"]]
            == reference["value_original"]
        )

    cnpj = [ref for ref in semantic["references"] if ref["reference_type"] == "cnpj"]
    assert len(cnpj) == 203
    assert sum(ref["valid"] is True for ref in cnpj) == 202
