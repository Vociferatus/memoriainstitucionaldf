from __future__ import annotations

import json
from pathlib import Path

from min_df.contracts import validate_human_annotation

ROOT = Path(__file__).resolve().parents[2]


def test_blind_annotation_ui_fixture_obeys_versioned_contract() -> None:
    fixture = ROOT / "web" / "tests" / "fixtures" / "blind-annotation-export.json"
    payload = json.loads(fixture.read_text(encoding="utf-8"))

    validate_human_annotation(payload)
