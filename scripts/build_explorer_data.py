"""Gera um pacote compacto e navegável para o explorador web."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from min_df.semantic import build_semantic_payload


def build_explorer_data(structured_path: Path, mentions_path: Path) -> dict[str, Any]:
    structured = json.loads(structured_path.read_text(encoding="utf-8"))
    mentions = json.loads(mentions_path.read_text(encoding="utf-8"))
    semantic = build_semantic_payload(structured, structured_path)
    blocks = {
        block["id"]: {
            "id": block["id"],
            "page": page["number"],
            "bbox": block["bbox"],
            "text": block["text_normalized"],
        }
        for page in structured["pages"]
        for block in page["blocks"]
    }
    block_to_item = {
        block_id: item["id"]
        for item in semantic["published_items"]
        for block_id in item["block_ids"]
    }

    item_links: dict[str, dict[str, list[str]]] = defaultdict(
        lambda: {"actions": [], "entities": [], "references": [], "processes": []}
    )
    actions = []
    for action in semantic["actions"]:
        participant = next(
            (
                entity["value_normalized"]
                for entity in semantic["entity_mentions"]
                if entity["role"] == f"subject_of:{action['id']}"
            ),
            None,
        )
        actions.append({**action, "participant": participant})
        item_links[action["item_id"]]["actions"].append(action["id"])

    entity_groups: dict[tuple[str, str], dict[str, Any]] = {}
    for entity in semantic["entity_mentions"]:
        key = (entity["entity_type"], entity["value_normalized"])
        group = entity_groups.setdefault(
            key,
            {
                "id": f"entity-group-{len(entity_groups) + 1:05d}",
                "entity_type": entity["entity_type"],
                "name": entity["value_normalized"],
                "occurrences": [],
                "item_ids": [],
            },
        )
        occurrence = {
            "block_id": entity["block_id"],
            "page": entity["page"],
            "start": entity["start"],
            "end": entity["end"],
            "role": entity["role"],
            "method": entity["method"],
            "item_id": entity["item_id"],
        }
        group["occurrences"].append(occurrence)
        if entity["item_id"]:
            group["item_ids"].append(entity["item_id"])
            item_links[entity["item_id"]]["entities"].append(group["id"])

    for group in entity_groups.values():
        if group["entity_type"] == "organization":
            group["item_ids"].extend(
                item["id"]
                for item in semantic["published_items"]
                if group["name"] in item["breadcrumb"]
            )
        group["item_ids"] = sorted(set(group["item_ids"]))

    for reference in semantic["references"]:
        item_links[reference["item_id"]]["references"].append(reference["id"])

    process_groups: dict[str, dict[str, Any]] = {}
    for mention in mentions["mentions"]:
        value = mention["value_normalized"]
        process = process_groups.setdefault(
            value,
            {
                "id": f"process-{len(process_groups) + 1:05d}",
                "value": value,
                "occurrences": [],
                "item_ids": [],
            },
        )
        item_id = block_to_item.get(mention["block_id"])
        occurrence = {
            "block_id": mention["block_id"],
            "page": mention["page"],
            "start": mention["start"],
            "end": mention["end"],
            "item_id": item_id,
            "method": mention["rule"]["name"],
        }
        process["occurrences"].append(occurrence)
        if item_id:
            process["item_ids"].append(item_id)
            item_links[item_id]["processes"].append(process["id"])

    items = []
    for item in semantic["published_items"]:
        links = item_links[item["id"]]
        provisions = sum(1 for row in semantic["provisions"] if row["item_id"] == item["id"])
        items.append(
            {
                **item,
                "actions": sorted(set(links["actions"])),
                "entities": sorted(set(links["entities"])),
                "references": sorted(set(links["references"])),
                "processes": sorted(set(links["processes"])),
                "provision_count": provisions,
            }
        )

    return {
        "version": "1.0",
        "document": {
            "title": "DODF 112",
            "publication_date": "2026-06-22",
            "pages": len(structured["pages"]),
            "sha256": structured["source"]["sha256"],
            "counts": semantic["counts"],
        },
        "sections": semantic["sections"],
        "contexts": semantic["editorial_contexts"],
        "items": items,
        "actions": actions,
        "entities": list(entity_groups.values()),
        "references": semantic["references"],
        "processes": list(process_groups.values()),
        "blocks": blocks,
        "pages": [
            {"number": page["number"], "width": page["width"], "height": page["height"]}
            for page in structured["pages"]
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--structured", type=Path, required=True)
    parser.add_argument("--mentions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = build_explorer_data(args.structured, args.mentions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    print(f"items: {len(payload['items'])}")
    print(f"entities: {len(payload['entities'])}")
    print(f"processes: {len(payload['processes'])}")
    print(f"output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
