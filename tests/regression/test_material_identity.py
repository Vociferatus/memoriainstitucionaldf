import json
from pathlib import Path

import pytest

from min_df.identity import build_identity_payload
from min_df.semantic import build_semantic_payload


@pytest.fixture(scope="module")
def identity_payload(pilot_paths: dict[str, Path], project_root: Path) -> dict:
    structured = json.loads(pilot_paths["structured"].read_text(encoding="utf-8"))
    semantic = build_semantic_payload(
        structured, pilot_paths["structured"].relative_to(project_root)
    )
    mentions = json.loads(pilot_paths["mentions"].read_text(encoding="utf-8"))
    return build_identity_payload(
        semantic,
        mentions,
        pilot_paths["structured"].with_suffix(".semantic.json"),
        pilot_paths["mentions"],
    )


def test_dodf_112_material_identity_baseline(identity_payload: dict) -> None:
    result = identity_payload
    assert result["counts"] == {
        "fragments": 1645,
        "assertions": 302,
        "identifiers": 1343,
        "canonical_entities": 1276,
        "identity_links": 1342,
        "candidate_groups": 45,
        "resolution_cases": 1,
        "unlinked_fragments": 303,
    }


def test_nominal_mentions_are_never_automatically_merged(identity_payload: dict) -> None:
    result = identity_payload
    fragments = {fragment["id"]: fragment for fragment in result["fragments"]}
    for link in result["identity_links"]:
        assert fragments[link["fragment_id"]]["entity_type"] not in {
            "person",
            "organization",
            "position",
        }
    assert all(group["decision"] == "KEEP_SEPARATE" for group in result["candidate_groups"])


def test_links_are_referentially_complete_and_material(identity_payload: dict) -> None:
    result = identity_payload
    fragment_ids = {fragment["id"] for fragment in result["fragments"]}
    entity_ids = {entity["id"] for entity in result["canonical_entities"]}
    assert all(link["fragment_id"] in fragment_ids for link in result["identity_links"])
    assert all(link["canonical_entity_id"] in entity_ids for link in result["identity_links"])
    assert all(not link["has_divergence"] for link in result["identity_links"])


def test_invalid_cnpj_opens_case_instead_of_entity(identity_payload: dict) -> None:
    result = identity_payload
    invalid = [identifier for identifier in result["identifiers"] if not identifier["is_valid"]]
    assert len(invalid) == 1
    invalid_fragment = invalid[0]["fragment_id"]
    assert all(link["fragment_id"] != invalid_fragment for link in result["identity_links"])
    assert any(invalid_fragment in case["fragment_ids"] for case in result["resolution_cases"])
