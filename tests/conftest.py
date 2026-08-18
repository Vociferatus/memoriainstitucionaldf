from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PILOT_STEM = "DODF 112 22-06-2026 INTEGRA"


@pytest.fixture(scope="session")
def project_root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def pilot_paths() -> dict[str, Path]:
    return {
        "pdf": ROOT / "data" / "raw" / f"{PILOT_STEM}.pdf",
        "manifest": ROOT / "data" / "manifests" / f"{PILOT_STEM}.manifest.json",
        "structured": ROOT / "data" / "structured" / f"{PILOT_STEM}.structured.json",
        "markdown": ROOT / "data" / "markdown" / f"{PILOT_STEM}.md",
        "mentions": ROOT / "data" / "extractions" / f"{PILOT_STEM}.mentions.json",
    }
