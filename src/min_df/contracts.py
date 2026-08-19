"""Validação dos contratos JSON versionados do pipeline."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator


class ContractValidationError(ValueError):
    """Indica que um artefato não respeita seu contrato declarado."""


def load_schema(name: str) -> dict[str, Any]:
    resource = files("min_df.schemas").joinpath(f"{name}.schema.json")
    schema = json.loads(resource.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def validate_payload(payload: dict[str, Any], schema_name: str) -> None:
    validator = Draft202012Validator(load_schema(schema_name))
    errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
    if not errors:
        return

    error = errors[0]
    location = ".".join(str(part) for part in error.absolute_path) or "<root>"
    raise ContractValidationError(
        f"Contrato {schema_name!r} inválido em {location}: {error.message}"
    )


def validate_manifest(payload: dict[str, Any]) -> None:
    validate_payload(payload, "manifest")


def validate_structured(payload: dict[str, Any]) -> None:
    validate_payload(payload, "structured-document")


def validate_mentions(payload: dict[str, Any]) -> None:
    validate_payload(payload, "mentions")


def validate_semantic(payload: dict[str, Any]) -> None:
    validate_payload(payload, "semantic-document")


def validate_identity(payload: dict[str, Any]) -> None:
    validate_payload(payload, "identity-resolution")


def validate_human_annotation(payload: dict[str, Any]) -> None:
    validate_payload(payload, "human-annotation")

    source = payload["source"]
    scope = payload["scope"]
    scope_pages = set(scope["pages"])
    record_ids: set[str] = set()
    mode = payload["annotator"]["mode"]

    if any(page > source["page_count"] for page in scope_pages):
        raise ContractValidationError("O escopo contém página além do documento.")

    if mode in {"blind_primary", "independent_second"} and source["automatic_artifacts"]:
        raise ContractValidationError(
            "Anotação independente não pode declarar artefatos automáticos como entrada."
        )

    for record in payload["records"]:
        if record["id"] in record_ids:
            raise ContractValidationError(f"ID de anotação duplicado: {record['id']}")
        record_ids.add(record["id"])

        if mode in {"blind_primary", "independent_second"}:
            if record["annotation_type"] != "observation" or record["target"] is not None:
                raise ContractValidationError(
                    "Anotação independente aceita apenas observações sem alvo automático."
                )
        elif mode == "assisted_review" and record["annotation_type"] not in {
            "evaluation",
            "identity_decision",
        }:
            raise ContractValidationError(
                "Revisão assistida aceita avaliações ou decisões de identidade."
            )
        elif mode == "adjudication" and record["annotation_type"] != "adjudication":
            raise ContractValidationError(
                "Lote de adjudicação aceita somente registros de adjudicação."
            )

        allowed_judgments = {
            "observation": {"PRESENT", "AMBIGUOUS"},
            "evaluation": {
                "CONFIRMED",
                "REJECTED",
                "MISSING",
                "AMBIGUOUS",
                "NOT_APPLICABLE",
            },
            "identity_decision": {
                "SAME_ENTITY",
                "DISTINCT_ENTITIES",
                "UNRESOLVED",
            },
            "adjudication": {
                "CONFIRMED",
                "REJECTED",
                "MISSING",
                "AMBIGUOUS",
                "NOT_APPLICABLE",
                "SAME_ENTITY",
                "DISTINCT_ENTITIES",
                "UNRESOLVED",
            },
        }
        if record["judgment"] not in allowed_judgments[record["annotation_type"]]:
            raise ContractValidationError(
                f"Julgamento incompatível com {record['annotation_type']} em {record['id']}."
            )

        if record["judgment"] in {"CONFIRMED", "REJECTED"} and record["target"] is None:
            raise ContractValidationError(
                f"O julgamento {record['judgment']} exige alvo automático em {record['id']}."
            )
        if record["judgment"] in {"REJECTED", "MISSING"} and not record[
            "error_categories"
        ]:
            raise ContractValidationError(
                f"O julgamento {record['judgment']} exige categoria de erro em {record['id']}."
            )
        if record["annotation_type"] == "identity_decision" and (
            record["task_type"] != "identity_resolution"
            or len(record["payload"].get("fragment_ids", [])) < 2
        ):
            raise ContractValidationError(
                f"Decisão de identidade incompleta em {record['id']}."
            )

        if record["judgment"] in {
            "REJECTED",
            "AMBIGUOUS",
            "SAME_ENTITY",
            "DISTINCT_ENTITIES",
            "UNRESOLVED",
        } and not record["rationale"]:
            raise ContractValidationError(
                f"O julgamento {record['judgment']} exige justificativa em {record['id']}."
            )

        for evidence in record["evidence"]:
            if evidence["document_sha256"] != source["document_sha256"]:
                raise ContractValidationError(
                    f"Evidência {record['id']} pertence a outro documento."
                )
            if evidence["page"] not in scope_pages:
                raise ContractValidationError(
                    f"Página {evidence['page']} de {record['id']} está fora do escopo."
                )
            start, end = evidence["start"], evidence["end"]
            if (start is None) != (end is None) or (
                start is not None and end is not None and end <= start
            ):
                raise ContractValidationError(
                    f"Span inválido na evidência de {record['id']}."
                )
