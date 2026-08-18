from __future__ import annotations

import hashlib
import json
from pathlib import Path

from min_df.audit_artifacts import audit

EXPECTED = {
    "pdf": "17389d23375c9b9b747c8a0f74305ce20ee4b52dbc20e23d92bef780ec4709fc",
    "markdown": "c04bb534c81588b3302c66907a4dfdb71649dc9a963094a82763bcf825d086e2",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_baseline_hashes(pilot_paths: dict[str, Path]) -> None:
    assert sha256(pilot_paths["pdf"]) == EXPECTED["pdf"]
    assert sha256(pilot_paths["markdown"]) == EXPECTED["markdown"]


def test_baseline_counts_and_references(pilot_paths: dict[str, Path]) -> None:
    structured = load(pilot_paths["structured"])
    mentions_payload = load(pilot_paths["mentions"])
    blocks = [block for page in structured["pages"] for block in page["blocks"]]
    block_ids = {block["id"] for block in blocks}
    mentions = mentions_payload["mentions"]

    assert len(structured["pages"]) == 85
    assert len(blocks) == 2553
    assert sum(block["removed_as_noise"] for block in blocks) == 179
    assert len(mentions) == 1140
    assert len({mention["value_normalized"] for mention in mentions}) == 1096
    assert all(mention["block_id"] in block_ids for mention in mentions)


def test_auditor_reports_no_orphans(pilot_paths: dict[str, Path]) -> None:
    report = audit(
        pilot_paths["manifest"],
        pilot_paths["structured"],
        pilot_paths["mentions"],
    )
    assert "Mencoes sem bloco correspondente: 0" in report
