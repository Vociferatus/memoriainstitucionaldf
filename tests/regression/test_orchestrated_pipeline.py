from __future__ import annotations

from pathlib import Path

from min_df.pipeline import run_pipeline


def test_orchestrated_pipeline_verifies_pilot(
    pilot_paths: dict[str, Path], tmp_path: Path
) -> None:
    result = run_pipeline(
        pilot_paths["pdf"],
        tmp_path,
        verify_pilot_baseline=True,
    )

    assert result["summary"]["pilot_baseline_verified"] is True
    assert result["summary"]["load_dry_run"]["missing_blocks"] == 0
    assert result["paths"]["summary"].is_file()
    assert result["paths"]["audit"].is_file()
