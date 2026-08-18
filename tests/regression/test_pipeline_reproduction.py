from __future__ import annotations

import hashlib
import json
from pathlib import Path

from min_df.dodf_to_markdown import markdown_from_structure, structured_document, write_text
from min_df.extract_mentions import build_extraction_payload


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def without_created_at(payload: dict) -> dict:
    result = dict(payload)
    result.pop("created_at", None)
    return result


def portable_structure(payload: dict) -> dict:
    result = without_created_at(payload)
    result["source"] = dict(result["source"])
    result["source"].pop("path", None)
    # O checkout pode atribuir ao arquivo um mtime diferente em cada máquina.
    # Integridade e identidade continuam cobertas por SHA-256, tamanho e conteúdo.
    result["source"].pop("modified_at", None)
    return result


def test_pdf_structure_and_markdown_are_exact(
    pilot_paths: dict[str, Path], tmp_path: Path
) -> None:
    expected = load(pilot_paths["structured"])
    actual = structured_document(pilot_paths["pdf"])

    assert portable_structure(actual) == portable_structure(expected)

    markdown = markdown_from_structure(actual, page_markers=True)
    generated = tmp_path / "DODF 112.md"
    write_text(generated, markdown)
    digest = hashlib.sha256(generated.read_bytes()).hexdigest()
    assert digest == "c04bb534c81588b3302c66907a4dfdb71649dc9a963094a82763bcf825d086e2"


def test_mentions_are_exact(pilot_paths: dict[str, Path], project_root: Path) -> None:
    structured = load(pilot_paths["structured"])
    expected = load(pilot_paths["mentions"])
    structured_path = pilot_paths["structured"].relative_to(project_root)
    output_path = pilot_paths["mentions"].relative_to(project_root)

    actual = build_extraction_payload(
        structured=structured,
        structured_path=structured_path,
        output_path=output_path,
        include_noise=False,
    )

    assert without_created_at(actual) == without_created_at(expected)
