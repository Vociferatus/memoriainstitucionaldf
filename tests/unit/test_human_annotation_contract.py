from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from min_df.contracts import ContractValidationError, validate_human_annotation

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "annotations" / "templates"
DOCUMENT_SHA256 = "17389d23375c9b9b747c8a0f74305ce20ee4b52dbc20e23d92bef780ec4709fc"


def load_template(name: str) -> dict:
    return json.loads((TEMPLATES / name).read_text(encoding="utf-8"))


def evidence() -> dict:
    return {
        "document_sha256": DOCUMENT_SHA256,
        "page": 1,
        "block_id": "p0001-b0001",
        "start": 0,
        "end": 5,
        "bbox": None,
        "quote": "SEÇÃO",
    }


def test_annotation_templates_obey_contract() -> None:
    for path in sorted(TEMPLATES.glob("*.json")):
        validate_human_annotation(json.loads(path.read_text(encoding="utf-8")))


def test_blind_observation_with_evidence_is_valid() -> None:
    payload = load_template("blind-primary.template.json")
    payload["records"] = [
        {
            "id": "annotation-1",
            "annotation_type": "observation",
            "task_type": "document_structure",
            "judgment": "PRESENT",
            "target": None,
            "evidence": [evidence()],
            "payload": {"observed_type": "section_heading"},
            "confidence": "certain",
            "rationale": None,
            "error_categories": [],
            "notes": None,
        }
    ]

    validate_human_annotation(payload)


def test_blind_annotation_rejects_automatic_target() -> None:
    payload = load_template("blind-primary.template.json")
    payload["records"] = [
        {
            "id": "annotation-1",
            "annotation_type": "evaluation",
            "task_type": "entity_mention",
            "judgment": "CONFIRMED",
            "target": {"layer": "semantic", "record_id": "entity-000001"},
            "evidence": [evidence()],
            "payload": {},
            "confidence": "certain",
            "rationale": None,
            "error_categories": [],
            "notes": None,
        }
    ]

    with pytest.raises(ContractValidationError, match="observações sem alvo"):
        validate_human_annotation(payload)


def test_annotation_rejects_evidence_outside_scope() -> None:
    payload = load_template("blind-primary.template.json")
    out_of_scope = evidence()
    out_of_scope["page"] = 2
    payload["records"] = [
        {
            "id": "annotation-1",
            "annotation_type": "observation",
            "task_type": "document_structure",
            "judgment": "PRESENT",
            "target": None,
            "evidence": [out_of_scope],
            "payload": {"observed_type": "section_heading"},
            "confidence": "certain",
            "rationale": None,
            "error_categories": [],
            "notes": None,
        }
    ]

    with pytest.raises(ContractValidationError, match="fora do escopo"):
        validate_human_annotation(payload)


def test_rejected_annotation_requires_error_category() -> None:
    payload = load_template("assisted-review.template.json")
    payload["records"] = [
        {
            "id": "annotation-1",
            "annotation_type": "evaluation",
            "task_type": "entity_mention",
            "judgment": "REJECTED",
            "target": {"layer": "semantic", "record_id": "entity-000001"},
            "evidence": [evidence()],
            "payload": {},
            "confidence": "certain",
            "rationale": "O trecho não designa uma pessoa.",
            "error_categories": [],
            "notes": None,
        }
    ]

    with pytest.raises(ContractValidationError, match="categoria de erro"):
        validate_human_annotation(payload)


def test_identity_decision_requires_two_fragments() -> None:
    payload = copy.deepcopy(load_template("assisted-review.template.json"))
    payload["records"] = [
        {
            "id": "annotation-1",
            "annotation_type": "identity_decision",
            "task_type": "identity_resolution",
            "judgment": "UNRESOLVED",
            "target": {"layer": "identity", "record_id": "candidate-000001"},
            "evidence": [evidence()],
            "payload": {
                "fragment_ids": ["fragment-000001"],
                "decision": "UNRESOLVED",
            },
            "confidence": "uncertain",
            "rationale": "Há somente um fragmento disponível.",
            "error_categories": [],
            "notes": None,
        }
    ]

    with pytest.raises(ContractValidationError, match="Decisão de identidade incompleta"):
        validate_human_annotation(payload)
