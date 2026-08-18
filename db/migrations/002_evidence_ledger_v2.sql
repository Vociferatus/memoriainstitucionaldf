-- Ledger de evidencias v2.
-- Migração estritamente aditiva: o schema 001 permanece disponível para rollback.

BEGIN;

CREATE TABLE IF NOT EXISTS source_policies (
    id bigserial PRIMARY KEY,
    source_id bigint NOT NULL REFERENCES sources(id) ON DELETE RESTRICT,
    policy_version text NOT NULL,
    authority_uri text NOT NULL,
    collection_policy jsonb NOT NULL DEFAULT '{}'::jsonb,
    effective_from timestamptz NOT NULL,
    effective_to timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT source_policies_version_unique UNIQUE (source_id, policy_version),
    CONSTRAINT source_policies_authority_uri_not_blank CHECK (btrim(authority_uri) <> ''),
    CONSTRAINT source_policies_interval_valid CHECK (
        effective_to IS NULL OR effective_to > effective_from
    )
);

CREATE TABLE IF NOT EXISTS blobs (
    id bigserial PRIMARY KEY,
    sha256 char(64) NOT NULL UNIQUE,
    size_bytes bigint NOT NULL,
    media_type text NOT NULL,
    storage_uri text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT blobs_sha256_format CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT blobs_size_positive CHECK (size_bytes > 0),
    CONSTRAINT blobs_storage_uri_not_blank CHECK (btrim(storage_uri) <> '')
);

CREATE TABLE IF NOT EXISTS captures (
    id bigserial PRIMARY KEY,
    capture_key text NOT NULL UNIQUE,
    document_id bigint NOT NULL REFERENCES documents(id) ON DELETE RESTRICT,
    blob_id bigint NOT NULL REFERENCES blobs(id) ON DELETE RESTRICT,
    source_policy_id bigint REFERENCES source_policies(id) ON DELETE RESTRICT,
    capture_uri text NOT NULL,
    captured_at timestamptz NOT NULL,
    observed_filename text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    legacy_capture_id bigint UNIQUE REFERENCES document_captures(id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT captures_key_not_blank CHECK (btrim(capture_key) <> ''),
    CONSTRAINT captures_uri_not_blank CHECK (btrim(capture_uri) <> '')
);

CREATE INDEX IF NOT EXISTS captures_document_id_idx ON captures(document_id);
CREATE INDEX IF NOT EXISTS captures_blob_id_idx ON captures(blob_id);

CREATE TABLE IF NOT EXISTS artifacts (
    id bigserial PRIMARY KEY,
    artifact_key text NOT NULL UNIQUE,
    sha256 char(64) NOT NULL,
    size_bytes bigint NOT NULL,
    media_type text NOT NULL,
    artifact_type text NOT NULL,
    schema_version text,
    storage_uri text NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT artifacts_content_identity_unique UNIQUE (sha256, artifact_type),
    CONSTRAINT artifacts_sha256_format CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT artifacts_size_positive CHECK (size_bytes > 0),
    CONSTRAINT artifacts_type_not_blank CHECK (btrim(artifact_type) <> ''),
    CONSTRAINT artifacts_storage_uri_not_blank CHECK (btrim(storage_uri) <> '')
);

CREATE TABLE IF NOT EXISTS transformation_runs (
    id bigserial PRIMARY KEY,
    run_key text NOT NULL UNIQUE,
    capture_id bigint NOT NULL REFERENCES captures(id) ON DELETE RESTRICT,
    transformation_type text NOT NULL,
    tool_name text NOT NULL,
    tool_version text NOT NULL,
    parameters jsonb NOT NULL DEFAULT '{}'::jsonb,
    status text NOT NULL DEFAULT 'completed',
    started_at timestamptz,
    completed_at timestamptz NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT transformation_runs_type_not_blank CHECK (btrim(transformation_type) <> ''),
    CONSTRAINT transformation_runs_tool_not_blank CHECK (btrim(tool_name) <> ''),
    CONSTRAINT transformation_runs_status_valid CHECK (status IN ('completed', 'failed')),
    CONSTRAINT transformation_runs_interval_valid CHECK (
        started_at IS NULL OR completed_at >= started_at
    )
);

CREATE INDEX IF NOT EXISTS transformation_runs_capture_id_idx
    ON transformation_runs(capture_id);

CREATE TABLE IF NOT EXISTS transformation_io (
    transformation_run_id bigint NOT NULL REFERENCES transformation_runs(id) ON DELETE CASCADE,
    artifact_id bigint NOT NULL REFERENCES artifacts(id) ON DELETE RESTRICT,
    direction text NOT NULL,
    role text NOT NULL,
    ordinal integer NOT NULL DEFAULT 1,
    PRIMARY KEY (transformation_run_id, direction, role, ordinal),
    CONSTRAINT transformation_io_direction_valid CHECK (direction IN ('input', 'output')),
    CONSTRAINT transformation_io_role_not_blank CHECK (btrim(role) <> ''),
    CONSTRAINT transformation_io_ordinal_positive CHECK (ordinal > 0)
);

CREATE TABLE IF NOT EXISTS evidence_mentions (
    id bigserial PRIMARY KEY,
    transformation_run_id bigint NOT NULL
        REFERENCES transformation_runs(id) ON DELETE RESTRICT,
    block_id bigint NOT NULL REFERENCES document_blocks(id) ON DELETE RESTRICT,
    mention_key text NOT NULL,
    mention_type text NOT NULL,
    value_original text NOT NULL,
    value_normalized text NOT NULL,
    text_field text NOT NULL,
    char_start integer NOT NULL,
    char_end integer NOT NULL,
    snippet text NOT NULL,
    rule jsonb NOT NULL,
    raw jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT evidence_mentions_run_key_unique
        UNIQUE (transformation_run_id, mention_key),
    CONSTRAINT evidence_mentions_char_range_valid
        CHECK (char_start >= 0 AND char_end > char_start),
    CONSTRAINT evidence_mentions_type_not_blank CHECK (btrim(mention_type) <> '')
);

CREATE INDEX IF NOT EXISTS evidence_mentions_block_id_idx ON evidence_mentions(block_id);
CREATE INDEX IF NOT EXISTS evidence_mentions_type_value_idx
    ON evidence_mentions(mention_type, value_normalized);

CREATE OR REPLACE FUNCTION enforce_evidence_mention_lineage()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    block_capture_id bigint;
    run_legacy_capture_id bigint;
BEGIN
    SELECT capture_id INTO block_capture_id
    FROM document_blocks WHERE id = NEW.block_id;

    SELECT c.legacy_capture_id INTO run_legacy_capture_id
    FROM transformation_runs tr
    JOIN captures c ON c.id = tr.capture_id
    WHERE tr.id = NEW.transformation_run_id;

    IF block_capture_id IS DISTINCT FROM run_legacy_capture_id THEN
        RAISE EXCEPTION 'menção, bloco e transformação pertencem a capturas diferentes';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS evidence_mentions_lineage_guard ON evidence_mentions;
CREATE TRIGGER evidence_mentions_lineage_guard
BEFORE INSERT OR UPDATE OF transformation_run_id, block_id ON evidence_mentions
FOR EACH ROW EXECUTE FUNCTION enforce_evidence_mention_lineage();

INSERT INTO source_policies (
    source_id, policy_version, authority_uri, collection_policy, effective_from
)
SELECT id, '1.0', 'https://www.dodf.df.gov.br/',
       '{"authority":"Diário Oficial do Distrito Federal","method":"legacy_import"}'::jsonb,
       '2026-01-01T00:00:00Z'::timestamptz
FROM sources
WHERE name = 'DODF'
ON CONFLICT (source_id, policy_version) DO NOTHING;

INSERT INTO blobs (sha256, size_bytes, media_type, storage_uri)
SELECT sha256, size_bytes, media_type, 'urn:sha256:' || sha256
FROM document_captures
ON CONFLICT (sha256) DO NOTHING;

INSERT INTO captures (
    capture_key, document_id, blob_id, source_policy_id, capture_uri,
    captured_at, observed_filename, metadata, legacy_capture_id
)
SELECT 'legacy:' || dc.id,
       dc.document_id,
       b.id,
       sp.id,
       'urn:legacy-capture:' || dc.id,
       COALESCE(dc.captured_at, dc.created_at),
       dc.filename,
       jsonb_build_object('migrated_from', 'document_captures', 'legacy_metadata', dc.metadata),
       dc.id
FROM document_captures dc
JOIN blobs b ON b.sha256 = dc.sha256
JOIN documents d ON d.id = dc.document_id
LEFT JOIN source_policies sp ON sp.source_id = d.source_id AND sp.policy_version = '1.0'
ON CONFLICT (legacy_capture_id) DO NOTHING;

INSERT INTO schema_migrations (version)
VALUES ('002_evidence_ledger_v2')
ON CONFLICT (version) DO NOTHING;

COMMIT;
