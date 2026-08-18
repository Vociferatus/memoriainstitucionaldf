from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from min_df.contracts import (
    ContractValidationError,
    validate_manifest,
    validate_mentions,
    validate_structured,
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_baseline_artifacts_obey_contracts(pilot_paths: dict[str, Path]) -> None:
    validate_manifest(load(pilot_paths["manifest"]))
    validate_structured(load(pilot_paths["structured"]))
    validate_mentions(load(pilot_paths["mentions"]))


def test_manifest_rejects_invalid_sha256(pilot_paths: dict[str, Path]) -> None:
    manifest = copy.deepcopy(load(pilot_paths["manifest"]))
    manifest["document"]["sha256"] = "invalid"

    with pytest.raises(ContractValidationError, match="document.sha256"):
        validate_manifest(manifest)


def test_mentions_reject_unknown_root_field(pilot_paths: dict[str, Path]) -> None:
    mentions = copy.deepcopy(load(pilot_paths["mentions"]))
    mentions["unexpected"] = True

    with pytest.raises(ContractValidationError, match="Additional properties"):
        validate_mentions(mentions)

