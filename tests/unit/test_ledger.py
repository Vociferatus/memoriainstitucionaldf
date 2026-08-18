from __future__ import annotations

from pathlib import Path

from min_df.ledger import portable_uri


def test_portable_uri_uses_repository_relative_path(tmp_path: Path) -> None:
    artifact = tmp_path / "data" / "artifact.json"
    artifact.parent.mkdir()
    artifact.write_text("{}", encoding="utf-8")

    assert portable_uri(artifact, tmp_path) == "repo:///data/artifact.json"


def test_v2_migration_encodes_ledger_invariants(project_root: Path) -> None:
    migration = (
        project_root / "db" / "migrations" / "002_evidence_ledger_v2.sql"
    ).read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS blobs" in migration
    assert "sha256 char(64) NOT NULL UNIQUE" in migration
    assert "CREATE TABLE IF NOT EXISTS captures" in migration
    assert "blob_id bigint NOT NULL REFERENCES blobs" in migration
    assert "UNIQUE (blob_id)" not in migration
    assert "CREATE TABLE IF NOT EXISTS transformation_runs" in migration
    assert "CREATE TABLE IF NOT EXISTS transformation_io" in migration
    assert "CREATE TRIGGER evidence_mentions_lineage_guard" in migration


def test_canonical_mentions_do_not_repeat_location(project_root: Path) -> None:
    migration = (
        project_root / "db" / "migrations" / "002_evidence_ledger_v2.sql"
    ).read_text(encoding="utf-8")
    table = migration.split("CREATE TABLE IF NOT EXISTS evidence_mentions", 1)[1].split(
        ");", 1
    )[0]

    assert "block_id bigint NOT NULL REFERENCES document_blocks" in table
    assert "capture_id" not in table
    assert "page_number" not in table
    assert "block_ref" not in table
    assert "block_bbox" not in table
