import json
from pathlib import Path

from min_df.identity import build_identity_payload

ROOT = Path(__file__).parents[2]
SEMANTIC = ROOT / ".artifacts/pilot-db/DODF 112 22-06-2026 INTEGRA.semantic.json"
MENTIONS = ROOT / "data/extractions/DODF 112 22-06-2026 INTEGRA.mentions.json"


def payload() -> dict:
    return build_identity_payload(
        json.loads(SEMANTIC.read_text(encoding="utf-8")),
        json.loads(MENTIONS.read_text(encoding="utf-8")),
        SEMANTIC,
        MENTIONS,
    )


def test_dodf_112_material_identity_baseline() -> None:
    result = payload()
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


def test_nominal_mentions_are_never_automatically_merged() -> None:
    result = payload()
    fragments = {fragment["id"]: fragment for fragment in result["fragments"]}
    for link in result["identity_links"]:
        assert fragments[link["fragment_id"]]["entity_type"] not in {
            "person",
            "organization",
            "position",
        }
    assert all(group["decision"] == "KEEP_SEPARATE" for group in result["candidate_groups"])


def test_links_are_referentially_complete_and_material() -> None:
    result = payload()
    fragment_ids = {fragment["id"] for fragment in result["fragments"]}
    entity_ids = {entity["id"] for entity in result["canonical_entities"]}
    assert all(link["fragment_id"] in fragment_ids for link in result["identity_links"])
    assert all(link["canonical_entity_id"] in entity_ids for link in result["identity_links"])
    assert all(not link["has_divergence"] for link in result["identity_links"])


def test_invalid_cnpj_opens_case_instead_of_entity() -> None:
    result = payload()
    invalid = [identifier for identifier in result["identifiers"] if not identifier["is_valid"]]
    assert len(invalid) == 1
    invalid_fragment = invalid[0]["fragment_id"]
    assert all(link["fragment_id"] != invalid_fragment for link in result["identity_links"])
    assert any(invalid_fragment in case["fragment_ids"] for case in result["resolution_cases"])
