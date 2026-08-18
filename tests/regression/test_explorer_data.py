from __future__ import annotations

from pathlib import Path

from scripts.build_explorer_data import build_explorer_data


def test_explorer_data_connects_navigation_and_evidence(
    pilot_paths: dict[str, Path],
) -> None:
    payload = build_explorer_data(pilot_paths["structured"], pilot_paths["mentions"])

    assert len(payload["items"]) == 457
    assert len(payload["entities"]) == 210
    assert len(payload["processes"]) == 1096
    assert payload["document"]["counts"]["unclassified_items"] == 0

    process = next(row for row in payload["processes"] if row["value"] == "04018-00001552/2021-01")
    assert process["item_ids"]
    occurrence = process["occurrences"][0]
    block = payload["blocks"][occurrence["block_id"]]
    assert block["text"][occurrence["start"] : occurrence["end"]] == process["value"]
