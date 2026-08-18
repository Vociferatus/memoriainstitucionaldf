"""Segmentação semântica auditável de uma edição estruturada do DODF."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from min_df.contracts import validate_semantic, validate_structured

SCRIPT_VERSION = "0.1.0"
SECTION_RE = re.compile(r"^SEÇÃO\s+(I|II|III)$", re.IGNORECASE)
ITEM_TYPE_RE = re.compile(
    r"^(?P<type>ATO DECLARATÓRIO|AVISO|ATA|COMUNICADO|CONVOCAÇÃO|DECISÃO|"
    r"DECLARAÇÃO|DECRETO|DESPACHO|EDITAL|EXTRATO|INSTRUÇÃO|LEI|"
    r"ORDEM DE SERVIÇO|PORTARIA|RECURSO|RESOLUÇÃO|RETIFICAÇÃO|TERMO)\b",
    re.IGNORECASE,
)
ITEM_NUMBER_RE = re.compile(r"\bN[º°o]?\s*(?P<number>[\w./-]+)", re.IGNORECASE)
ITEM_DATE_RE = re.compile(
    r"\bDE\s+(?P<day>\d{1,2})\s+DE\s+(?P<month>[A-ZÇ]+)\s+DE\s+(?P<year>\d{4})",
    re.IGNORECASE,
)
MONTHS = {
    "JANEIRO": 1,
    "FEVEREIRO": 2,
    "MARÇO": 3,
    "ABRIL": 4,
    "MAIO": 5,
    "JUNHO": 6,
    "JULHO": 7,
    "AGOSTO": 8,
    "SETEMBRO": 9,
    "OUTUBRO": 10,
    "NOVEMBRO": 11,
    "DEZEMBRO": 12,
}
ORG_HEADING_RE = re.compile(
    r"\b(ADMINISTRAÇÃO|AGÊNCIA|ARQUIVO|CASA CIVIL|COMPANHIA|CONSELHO|"
    r"CONTROLADORIA|CORPO DE BOMBEIROS|DEFENSORIA|DEPARTAMENTO|EMPRESA|"
    r"FUNDAÇÃO|FUNDO|GABINETE|INSTITUTO|POLÍCIA|PROCURADORIA|SECRETARIA|"
    r"SUBSECRETARIA|TRIBUNAL)\b",
    re.IGNORECASE,
)
ACTION_RE = re.compile(
    r"\b(CESSAR\s+OS\s+EFEITOS|TORNAR\s+SEM\s+EFEITO|NOMEAR|EXONERAR|"
    r"DESIGNAR|DISPENSAR|RETIFICAR)\b",
    re.IGNORECASE,
)
ARTICLE_RE = re.compile(r"\bArt\.?\s*\d+[º°o]?", re.IGNORECASE)
PERSON_AFTER_ACTION_RE = re.compile(
    r"\s*,?\s*(?:(?:A PEDIDO|POR MOTIVO DE APOSENTADORIA)\s*,?\s+)?"
    r"(?P<name>[A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇ][A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇ\s]{2,118}?)(?=,)",
    re.IGNORECASE,
)
NON_PERSON_SUBJECTS = ("ORDEM DE SERVIÇO", "PORTARIA", "RESOLUÇÃO", "EDITAL")
CNPJ_RE = re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")
MONEY_RE = re.compile(r"R\$\s*[\d.]+,\d{2}")
NORM_RE = re.compile(
    r"\b(?:DECRETO|LEI|PORTARIA|RESOLUÇÃO)\s+(?:N[º°o]?\s*)?[\d.]+(?:/\d{4})?",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class BlockRef:
    id: str
    page: int
    order: int
    text: str
    role: str
    noise: bool


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def flatten_blocks(structured: dict[str, Any]) -> list[BlockRef]:
    return [
        BlockRef(
            id=block["id"],
            page=page["number"],
            order=block["order"],
            text=block.get("text_normalized", "").strip(),
            role=block.get("markdown_role", "paragraph"),
            noise=block.get("removed_as_noise", False),
        )
        for page in structured["pages"]
        for block in page["blocks"]
    ]


def is_context_heading(block: BlockRef) -> bool:
    if block.noise or not block.text or ITEM_TYPE_RE.match(block.text):
        return False
    if block.role in {"h1", "h2"}:
        return block.text == block.text.upper() and len(block.text) <= 180
    return (
        block.role == "h3"
        and block.text == block.text.upper()
        and len(block.text) <= 180
        and ORG_HEADING_RE.search(block.text) is not None
    )


def item_type(title: str) -> str:
    match = ITEM_TYPE_RE.match(title)
    if not match:
        return "unclassified"
    return match.group("type").lower().replace(" ", "_")


def item_metadata(title: str) -> dict[str, str | None]:
    number = ITEM_NUMBER_RE.search(title)
    date = ITEM_DATE_RE.search(title)
    iso_date = None
    if date:
        month = MONTHS.get(date.group("month").upper())
        if month:
            iso_date = f"{int(date.group('year')):04d}-{month:02d}-{int(date.group('day')):02d}"
    return {
        "number": number.group("number") if number else None,
        "date_literal": date.group(0) if date else None,
        "act_date": iso_date,
    }


def item_title(text: str) -> str:
    date = ITEM_DATE_RE.search(text)
    if date:
        return text[: date.end()].rstrip(" .")
    sentence = text.split(". ", 1)[0]
    return sentence[:180]


def extract_observations(
    items: list[dict[str, Any]],
    contexts: list[dict[str, Any]],
    block_index: dict[str, BlockRef],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    actions: list[dict[str, Any]] = []
    entities: list[dict[str, Any]] = []
    provisions: list[dict[str, Any]] = []
    references: list[dict[str, Any]] = []

    for context in contexts:
        for block_id in context["block_ids"]:
            block = block_index[block_id]
            entities.append(
                {
                    "id": f"entity-{len(entities) + 1:06d}",
                    "entity_type": "organization",
                    "value_original": block.text,
                    "value_normalized": block.text,
                    "role": "editorial_context",
                    "item_id": None,
                    "block_id": block.id,
                    "page": block.page,
                    "start": 0,
                    "end": len(block.text),
                    "method": "editorial_heading_v1",
                }
            )

    for item in items:
        for block_id in item["block_ids"]:
            block = block_index[block_id]
            reference_patterns = (
                ("cnpj", CNPJ_RE, "cnpj_checksum_v1"),
                ("monetary_value", MONEY_RE, "brl_literal_v1"),
                ("norm", NORM_RE, "norm_literal_v1"),
            )
            for ref_type, pattern, method in reference_patterns:
                for match in pattern.finditer(block.text):
                    literal = match.group(0)
                    references.append(
                        {
                            "id": f"reference-{len(references) + 1:06d}",
                            "reference_type": ref_type,
                            "value_original": literal,
                            "value_normalized": re.sub(r"\s+", " ", literal.upper()),
                            "valid": validate_cnpj(literal) if ref_type == "cnpj" else None,
                            "item_id": item["id"],
                            "block_id": block.id,
                            "page": block.page,
                            "start": match.start(),
                            "end": match.end(),
                            "method": method,
                        }
                    )
            for match in ARTICLE_RE.finditer(block.text):
                provisions.append(
                    {
                        "id": f"provision-{len(provisions) + 1:06d}",
                        "kind": "article",
                        "label": match.group(0),
                        "item_id": item["id"],
                        "block_id": block.id,
                        "page": block.page,
                        "start": match.start(),
                        "end": match.end(),
                    }
                )
            for match in ACTION_RE.finditer(block.text):
                verb = re.sub(r"\s+", "_", match.group(0).upper())
                action_id = f"action-{len(actions) + 1:06d}"
                actions.append(
                    {
                        "id": action_id,
                        "verb": verb,
                        "value_original": match.group(0),
                        "item_id": item["id"],
                        "block_id": block.id,
                        "page": block.page,
                        "start": match.start(),
                        "end": match.end(),
                        "status": "observed_text",
                        "method": "priority_action_verbs_v1",
                    }
                )
                person = PERSON_AFTER_ACTION_RE.match(block.text, match.end())
                if person:
                    name = re.sub(r"\s+", " ", person.group("name").strip())
                    if name.upper().startswith(NON_PERSON_SUBJECTS) or name != name.upper():
                        continue
                    entities.append(
                        {
                            "id": f"entity-{len(entities) + 1:06d}",
                            "entity_type": "person",
                            "value_original": name,
                            "value_normalized": name,
                            "role": f"subject_of:{action_id}",
                            "item_id": item["id"],
                            "block_id": block.id,
                            "page": block.page,
                            "start": person.start("name"),
                            "end": person.end("name"),
                            "method": "person_after_action_v1",
                        }
                    )
                    person_id = entities[-1]["id"]
                    position_start = person.end("name") + 1
                    position_end = block.text.find(",", position_start)
                    if position_end > position_start:
                        raw_position = block.text[position_start:position_end]
                        position = raw_position.strip()
                        position_start += len(raw_position) - len(raw_position.lstrip())
                        position_end = position_start + len(position)
                        if 3 <= len(position) <= 120 and not position.lower().startswith(
                            ("matrícula", "cpf", "processo")
                        ):
                            entities.append(
                                {
                                    "id": f"entity-{len(entities) + 1:06d}",
                                    "entity_type": "position",
                                    "value_original": position,
                                    "value_normalized": re.sub(r"\s+", " ", position),
                                    "role": f"current_position_of:{person_id}",
                                    "item_id": item["id"],
                                    "block_id": block.id,
                                    "page": block.page,
                                    "start": position_start,
                                    "end": position_end,
                                    "method": "position_after_person_v1",
                                }
                            )
    return actions, entities, provisions, references


def validate_cnpj(value: str) -> bool:
    digits = [int(char) for char in value if char.isdigit()]
    if len(digits) != 14 or len(set(digits)) == 1:
        return False
    for length in (12, 13):
        weights = list(range(length - 7, 1, -1)) + list(range(9, 1, -1))
        total = sum(
            number * weight for number, weight in zip(digits[:length], weights, strict=True)
        )
        remainder = total % 11
        check = 0 if remainder < 2 else 11 - remainder
        if digits[length] != check:
            return False
    return True


def build_semantic_payload(structured: dict[str, Any], source_path: Path) -> dict[str, Any]:
    validate_structured(structured)
    blocks = flatten_blocks(structured)
    sections: list[dict[str, Any]] = []
    contexts: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []
    assignments: list[dict[str, Any]] = []
    current_section: dict[str, Any] | None = None
    expected_sections = ["I", "II", "III"]
    next_section_index = 0
    breadcrumb: list[str] = []
    current_item: dict[str, Any] | None = None

    def close_item() -> None:
        nonlocal current_item
        if current_item is None:
            return
        item_blocks = current_item.pop("_blocks")
        current_item["block_ids"] = [block.id for block in item_blocks]
        current_item["start_page"] = item_blocks[0].page
        current_item["end_page"] = item_blocks[-1].page
        current_item["text"] = "\n\n".join(block.text for block in item_blocks)
        items.append(current_item)
        current_item = None

    for block in blocks:
        if block.noise:
            assignments.append({"block_id": block.id, "category": "noise"})
            continue

        section_match = SECTION_RE.fullmatch(block.text)
        if (
            section_match
            and next_section_index < len(expected_sections)
            and section_match.group(1).upper() == expected_sections[next_section_index]
        ):
            close_item()
            roman = section_match.group(1).upper()
            current_section = {
                "id": f"section-{roman.lower()}",
                "label": f"SEÇÃO {roman}",
                "start_block_id": block.id,
                "start_page": block.page,
            }
            sections.append(current_section)
            next_section_index += 1
            breadcrumb = []
            assignments.append(
                {
                    "block_id": block.id,
                    "category": "section_heading",
                    "section_id": current_section["id"],
                }
            )
            continue

        if current_section is None:
            category = "summary" if block.page == 1 else "front_matter"
            assignments.append({"block_id": block.id, "category": category})
            continue

        if block.text == "DIÁRIO OFICIAL DO DISTRITO FEDERAL":
            close_item()
            assignments.append(
                {
                    "block_id": block.id,
                    "category": "publication_header",
                    "section_id": current_section["id"],
                }
            )
            continue

        if block.text.startswith("Redação, Administração e Editoração:"):
            close_item()
            assignments.append(
                {
                    "block_id": block.id,
                    "category": "publication_metadata",
                    "section_id": current_section["id"],
                }
            )
            continue

        if is_context_heading(block):
            close_item()
            level = 1 if block.role == "h1" else 2 if block.role == "h2" else 3
            previous_assignment = assignments[-1] if assignments else None
            previous_context = contexts[-1] if contexts else None
            should_merge = (
                previous_assignment is not None
                and previous_assignment["category"] == "editorial_context"
                and previous_context is not None
                and previous_context["page"] == block.page
                and previous_context["level"] == level
                and ORG_HEADING_RE.search(block.text) is None
                and len(previous_context["label"] + " " + block.text) <= 180
            )
            if should_merge:
                assert previous_context is not None
                previous_context["label"] += " " + block.text
                previous_context["block_ids"].append(block.id)
                breadcrumb[-1] = previous_context["label"]
                previous_context["breadcrumb"] = list(breadcrumb)
                assignments.append(
                    {
                        "block_id": block.id,
                        "category": "editorial_context",
                        "section_id": current_section["id"],
                        "context_id": previous_context["id"],
                    }
                )
                continue
            breadcrumb = breadcrumb[: level - 1] + [block.text]
            context = {
                "id": f"context-{len(contexts) + 1:04d}",
                "section_id": current_section["id"],
                "level": level,
                "label": block.text,
                "block_ids": [block.id],
                "page": block.page,
                "breadcrumb": list(breadcrumb),
                "kind": "observed_editorial_heading",
            }
            contexts.append(context)
            assignments.append(
                {
                    "block_id": block.id,
                    "category": "editorial_context",
                    "section_id": current_section["id"],
                    "context_id": context["id"],
                }
            )
            continue

        title_match = ITEM_TYPE_RE.match(block.text)
        if title_match:
            close_item()
            metadata = item_metadata(block.text)
            current_item = {
                "id": f"item-{len(items) + 1:05d}",
                "section_id": current_section["id"],
                "breadcrumb": list(breadcrumb),
                "title": item_title(block.text),
                "item_type": item_type(block.text),
                **metadata,
                "_blocks": [block],
            }
            assignments.append(
                {
                    "block_id": block.id,
                    "category": "published_item",
                    "section_id": current_section["id"],
                    "item_id": current_item["id"],
                }
            )
            continue

        if current_item is not None:
            current_item["_blocks"].append(block)
            assignments.append(
                {
                    "block_id": block.id,
                    "category": "published_item",
                    "section_id": current_section["id"],
                    "item_id": current_item["id"],
                }
            )
        else:
            current_item = {
                "id": f"item-{len(items) + 1:05d}",
                "section_id": current_section["id"],
                "breadcrumb": list(breadcrumb),
                "title": block.text[:180],
                "item_type": "unclassified",
                "number": None,
                "date_literal": None,
                "act_date": None,
                "_blocks": [block],
            }
            assignments.append(
                {
                    "block_id": block.id,
                    "category": "published_item",
                    "section_id": current_section["id"],
                    "item_id": current_item["id"],
                }
            )

    close_item()
    block_index = {block.id: block for block in blocks}
    actions, entities, provisions, references = extract_observations(items, contexts, block_index)
    counts: dict[str, int] = {
        "blocks_total": len(blocks),
        "sections": len(sections),
        "contexts": len(contexts),
        "published_items": len(items),
        "multi_page_items": sum(item["start_page"] != item["end_page"] for item in items),
        "unclassified_items": sum(item["item_type"] == "unclassified" for item in items),
        "actions": len(actions),
        "entity_mentions": len(entities),
        "provisions": len(provisions),
        "references": len(references),
    }
    payload = {
        "schema_version": "1.0",
        "created_at": utc_now(),
        "tool": {"name": "semantic.py", "version": SCRIPT_VERSION},
        "source": {
            "structured_uri": f"repo:///{source_path.as_posix()}",
            "document_sha256": structured["source"]["sha256"],
        },
        "sections": sections,
        "editorial_contexts": contexts,
        "published_items": items,
        "provisions": provisions,
        "actions": actions,
        "entity_mentions": entities,
        "references": references,
        "block_assignments": assignments,
        "counts": counts,
    }
    validate_semantic(payload)
    return payload


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Segmenta contexto e matérias do DODF.")
    parser.add_argument("structured", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    structured = json.loads(args.structured.read_text(encoding="utf-8"))
    payload = build_semantic_payload(structured, args.structured)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for key, value in payload["counts"].items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
