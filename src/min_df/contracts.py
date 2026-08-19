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
