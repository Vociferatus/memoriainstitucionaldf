from __future__ import annotations

from min_df.dodf_to_markdown import join_lines, normalize_line
from min_df.extract_mentions import normalize_processo_sei
from min_df.load_to_postgres import parse_dodf_filename


def test_normalize_line_collapses_horizontal_space() -> None:
    assert normalize_line("  DIÁRIO    OFICIAL\tDO DF  ") == "DIÁRIO OFICIAL DO DF"


def test_join_lines_repairs_hyphenated_word() -> None:
    assert join_lines(["Adminis-", "tração Pública"]) == "Administração Pública"


def test_normalize_processo_sei_removes_internal_spaces() -> None:
    value = "04003- 00000071/2026- 53"
    assert normalize_processo_sei(value) == "04003-00000071/2026-53"


def test_parse_dodf_filename_builds_stable_key() -> None:
    parsed = parse_dodf_filename("DODF 112 22-06-2026 INTEGRA.pdf")
    assert parsed["document_key"] == "dodf:2026-06-22:edicao-112:integra"
    assert parsed["edition_number"] == "112"
    assert parsed["publication_date"].isoformat() == "2026-06-22"
