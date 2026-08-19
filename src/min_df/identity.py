"""Camada conservadora e auditável de identidade material."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from min_df.contracts import validate_identity, validate_mentions, validate_semantic

SCRIPT_VERSION = "0.1.0"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def nominal_key(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_value = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"[^A-Z0-9]+", " ", ascii_value.upper()).strip()


def digits(value: str) -> str:
    return "".join(char for char in value if char.isdigit())


def build_identity_payload(
    semantic: dict[str, Any],
    mentions: dict[str, Any],
    semantic_path: Path,
    mentions_path: Path,
) -> dict[str, Any]:
    validate_semantic(semantic)
    validate_mentions(mentions)
    if semantic["source"]["document_sha256"] != mentions["source"]["document_sha256"]:
        raise ValueError("Os artefatos semântico e de menções pertencem a documentos diferentes.")

    fragments: list[dict[str, Any]] = []
    assertions: list[dict[str, Any]] = []
    identifiers: list[dict[str, Any]] = []
    entities: list[dict[str, Any]] = []
    links: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    cases: list[dict[str, Any]] = []

    def add_fragment(
        *,
        entity_type: str,
        source_kind: str,
        source_id: str,
        label: str,
        block_id: str,
        page: int,
        start: int,
        end: int,
        item_id: str | None,
        method: str,
    ) -> str:
        fragment_id = f"fragment-{len(fragments) + 1:06d}"
        fragments.append(
            {
                "id": fragment_id,
                "entity_type": entity_type,
                "source_kind": source_kind,
                "source_id": source_id,
                "label": label,
                "block_id": block_id,
                "page": page,
                "start": start,
                "end": end,
                "item_id": item_id,
                "status": "observed_fragment",
                "method": method,
            }
        )
        return fragment_id

    nominal_groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for mention in semantic["entity_mentions"]:
        fragment_id = add_fragment(
            entity_type=mention["entity_type"],
            source_kind="semantic_entity_mention",
            source_id=mention["id"],
            label=mention["value_original"],
            block_id=mention["block_id"],
            page=mention["page"],
            start=mention["start"],
            end=mention["end"],
            item_id=mention["item_id"],
            method=mention["method"],
        )
        key = nominal_key(mention["value_normalized"])
        assertions.append(
            {
                "id": f"assertion-{len(assertions) + 1:06d}",
                "fragment_id": fragment_id,
                "attribute": "name" if mention["entity_type"] != "position" else "title",
                "value_original": mention["value_original"],
                "value_normalized": key,
                "materiality_class": "N",
                "scope": None,
                "valid_from": None,
                "valid_to": None,
                "method": "exact_nominal_normalization_v1",
            }
        )
        nominal_groups[(mention["entity_type"], key)].append(fragment_id)

    process_groups: dict[str, list[str]] = defaultdict(list)
    for mention in mentions["mentions"]:
        if mention["type"] != "processo_sei":
            continue
        value = mention["value_normalized"]
        fragment_id = add_fragment(
            entity_type="process",
            source_kind="evidence_mention",
            source_id=mention["id"],
            label=value,
            block_id=mention["block_id"],
            page=mention["page"],
            start=mention["start"],
            end=mention["end"],
            item_id=None,
            method="process_number_observation_v1",
        )
        identifiers.append(
            {
                "id": f"identifier-{len(identifiers) + 1:06d}",
                "fragment_id": fragment_id,
                "identifier_type": "processo_sei",
                "value_original": mention["value_original"],
                "value_normalized": value,
                "materiality_class": "S",
                "scope": "processo_administrativo_df",
                "is_valid": True,
                "transferability": "scoped_nontransferable",
                "method": "processo_sei_regex_v1",
            }
        )
        process_groups[value].append(fragment_id)

    cnpj_groups: dict[str, list[str]] = defaultdict(list)
    for reference in semantic["references"]:
        if reference["reference_type"] != "cnpj":
            continue
        value = digits(reference["value_normalized"])
        fragment_id = add_fragment(
            entity_type="legal_organization",
            source_kind="semantic_reference",
            source_id=reference["id"],
            label=reference["value_original"],
            block_id=reference["block_id"],
            page=reference["page"],
            start=reference["start"],
            end=reference["end"],
            item_id=reference["item_id"],
            method=reference["method"],
        )
        valid = bool(reference["valid"])
        identifiers.append(
            {
                "id": f"identifier-{len(identifiers) + 1:06d}",
                "fragment_id": fragment_id,
                "identifier_type": "cnpj",
                "value_original": reference["value_original"],
                "value_normalized": value,
                "materiality_class": "U",
                "scope": "brasil",
                "is_valid": valid,
                "transferability": "nontransferable",
                "method": "cnpj_checksum_v1",
            }
        )
        if valid:
            cnpj_groups[value].append(fragment_id)
        else:
            cases.append(
                {
                    "id": f"case-{len(cases) + 1:06d}",
                    "entity_type": "legal_organization",
                    "fragment_ids": [fragment_id],
                    "case_type": "invalid_identifier",
                    "status": "unresolved",
                    "divergences": ["cnpj_checksum_invalid"],
                    "analysis_chain": [
                        "verify_extraction",
                        "verify_source_image",
                        "seek_correction",
                    ],
                    "recommended_decision": "UNRESOLVED",
                    "reason": "CNPJ observado não supera a validação dos dígitos verificadores.",
                }
            )

    def materialize(entity_type: str, groups: dict[str, list[str]], rule: str) -> None:
        for value, fragment_ids in sorted(groups.items()):
            entity_id = f"canonical-{len(entities) + 1:06d}"
            display = f"CNPJ {value}" if entity_type == "legal_organization" else value
            entities.append(
                {
                    "id": entity_id,
                    "entity_type": entity_type,
                    "display_name": display,
                    "status": "materialized",
                    "materiality_basis": "U" if entity_type == "legal_organization" else "S",
                    "created_by_rule": rule,
                }
            )
            for fragment_id in fragment_ids:
                links.append(
                    {
                        "id": f"link-{len(links) + 1:06d}",
                        "fragment_id": fragment_id,
                        "canonical_entity_id": entity_id,
                        "decision": "AUTO_LINK",
                        "reason": rule,
                        "rules": [rule, "no_observed_divergence"],
                        "has_divergence": False,
                        "review_status": "automatic",
                        "version": 1,
                    }
                )

    materialize("process", process_groups, "same_scoped_process_identifier_v1")
    materialize("legal_organization", cnpj_groups, "same_valid_cnpj_v1")

    for (entity_type, key), fragment_ids in sorted(nominal_groups.items()):
        if len(fragment_ids) < 2:
            continue
        candidates.append(
            {
                "id": f"candidate-{len(candidates) + 1:06d}",
                "entity_type": entity_type,
                "candidate_key": key,
                "fragment_ids": fragment_ids,
                "decision": "KEEP_SEPARATE",
                "reason": "Coincidência nominal não constitui identidade material.",
                "materiality_classes": ["N"],
                "missing_evidence": ["nontransferable_identifier_or_complete_concordance"],
            }
        )

    counts = {
        "fragments": len(fragments),
        "assertions": len(assertions),
        "identifiers": len(identifiers),
        "canonical_entities": len(entities),
        "identity_links": len(links),
        "candidate_groups": len(candidates),
        "resolution_cases": len(cases),
        "unlinked_fragments": len(fragments) - len({link["fragment_id"] for link in links}),
    }
    payload = {
        "schema_version": "1.0",
        "created_at": utc_now(),
        "tool": {"name": "identity.py", "version": SCRIPT_VERSION},
        "policy": {
            "name": "material_identity_split_first",
            "version": "1.0",
            "default": "KEEP_SEPARATE",
            "principles": [
                "fragments_are_immutable_evidence",
                "names_are_not_material_identifiers",
                "one_unexplained_divergence_suspends_linking",
                "links_are_reversible_and_versioned",
            ],
        },
        "source": {
            "semantic_uri": f"repo:///{semantic_path.as_posix()}",
            "mentions_uri": f"repo:///{mentions_path.as_posix()}",
            "document_sha256": semantic["source"]["document_sha256"],
        },
        "fragments": fragments,
        "assertions": assertions,
        "identifiers": identifiers,
        "canonical_entities": entities,
        "identity_links": links,
        "candidate_groups": candidates,
        "resolution_cases": cases,
        "counts": counts,
    }
    validate_identity(payload)
    return payload


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Constrói a camada de identidade material.")
    parser.add_argument("--semantic", required=True, type=Path)
    parser.add_argument("--mentions", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    semantic = json.loads(args.semantic.read_text(encoding="utf-8"))
    mentions = json.loads(args.mentions.read_text(encoding="utf-8"))
    payload = build_identity_payload(semantic, mentions, args.semantic, args.mentions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for key, value in payload["counts"].items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
