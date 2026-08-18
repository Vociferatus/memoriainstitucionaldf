-- Memoria Institucional Navegavel
-- Esquema inicial para documentos, blocos e mencoes extraidas.
--
-- Principio: dados brutos e evidencias ficam separados de interpretacoes.
-- Este esquema persiste o que foi observado e de onde veio.

BEGIN;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sources (
    id bigserial PRIMARY KEY,
    name text NOT NULL,
    kind text NOT NULL,
    base_url text,
    notes text,
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT sources_name_kind_unique UNIQUE (name, kind),
    CONSTRAINT sources_kind_not_blank CHECK (btrim(kind) <> ''),
    CONSTRAINT sources_name_not_blank CHECK (btrim(name) <> '')
);

CREATE TABLE IF NOT EXISTS documents (
    id bigserial PRIMARY KEY,
    source_id bigint REFERENCES sources(id),
    document_key text NOT NULL,
    title text NOT NULL,
    document_type text,
    publication_date date,
    edition_number text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT documents_document_key_unique UNIQUE (document_key),
    CONSTRAINT documents_document_key_not_blank CHECK (btrim(document_key) <> ''),
    CONSTRAINT documents_title_not_blank CHECK (btrim(title) <> '')
);

CREATE TABLE IF NOT EXISTS document_captures (
    id bigserial PRIMARY KEY,
    document_id bigint NOT NULL REFERENCES documents(id) ON DELETE RESTRICT,
    capture_key text NOT NULL,
    raw_path text NOT NULL,
    filename text NOT NULL,
    media_type text NOT NULL,
    size_bytes bigint NOT NULL,
    sha256 char(64) NOT NULL,
    page_count integer,
    captured_at timestamptz,
    file_modified_at timestamptz,
    manifest_path text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT document_captures_capture_key_unique UNIQUE (capture_key),
    CONSTRAINT document_captures_sha256_unique UNIQUE (sha256),
    CONSTRAINT document_captures_sha256_format CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT document_captures_size_positive CHECK (size_bytes > 0),
    CONSTRAINT document_captures_page_count_positive CHECK (
        page_count IS NULL OR page_count > 0
    ),
    CONSTRAINT document_captures_raw_path_not_blank CHECK (btrim(raw_path) <> ''),
    CONSTRAINT document_captures_filename_not_blank CHECK (btrim(filename) <> '')
);

CREATE TABLE IF NOT EXISTS document_pages (
    id bigserial PRIMARY KEY,
    capture_id bigint NOT NULL REFERENCES document_captures(id) ON DELETE CASCADE,
    page_number integer NOT NULL,
    width numeric(12, 4),
    height numeric(12, 4),
    rotation integer,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT document_pages_capture_page_unique UNIQUE (capture_id, page_number),
    CONSTRAINT document_pages_page_number_positive CHECK (page_number > 0)
);

CREATE TABLE IF NOT EXISTS document_blocks (
    id bigserial PRIMARY KEY,
    capture_id bigint NOT NULL REFERENCES document_captures(id) ON DELETE CASCADE,
    page_number integer NOT NULL,
    block_id text NOT NULL,
    block_order integer NOT NULL,
    source_order integer,
    column_number integer,
    bbox numeric(12, 4)[] NOT NULL,
    text_original text NOT NULL,
    text_normalized text NOT NULL,
    font_size numeric(8, 4),
    bold boolean NOT NULL DEFAULT false,
    markdown_role text,
    removed_as_noise boolean NOT NULL DEFAULT false,
    noise_reason text,
    raw jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT document_blocks_capture_block_unique UNIQUE (capture_id, block_id),
    CONSTRAINT document_blocks_capture_page_fk FOREIGN KEY (capture_id, page_number)
        REFERENCES document_pages(capture_id, page_number) ON DELETE CASCADE,
    CONSTRAINT document_blocks_page_number_positive CHECK (page_number > 0),
    CONSTRAINT document_blocks_block_order_positive CHECK (block_order > 0),
    CONSTRAINT document_blocks_block_id_not_blank CHECK (btrim(block_id) <> ''),
    CONSTRAINT document_blocks_bbox_four_values CHECK (array_length(bbox, 1) = 4)
);

CREATE TABLE IF NOT EXISTS extraction_runs (
    id bigserial PRIMARY KEY,
    capture_id bigint NOT NULL REFERENCES document_captures(id) ON DELETE RESTRICT,
    run_key text NOT NULL,
    tool_name text NOT NULL,
    tool_version text NOT NULL,
    schema_version text NOT NULL,
    structured_path text NOT NULL,
    output_path text,
    include_noise boolean NOT NULL DEFAULT false,
    extractors jsonb NOT NULL DEFAULT '[]'::jsonb,
    counts jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT extraction_runs_run_key_unique UNIQUE (run_key),
    CONSTRAINT extraction_runs_tool_name_not_blank CHECK (btrim(tool_name) <> ''),
    CONSTRAINT extraction_runs_tool_version_not_blank CHECK (btrim(tool_version) <> ''),
    CONSTRAINT extraction_runs_schema_version_not_blank CHECK (btrim(schema_version) <> ''),
    CONSTRAINT extraction_runs_structured_path_not_blank CHECK (btrim(structured_path) <> '')
);

CREATE TABLE IF NOT EXISTS mentions (
    id bigserial PRIMARY KEY,
    extraction_run_id bigint NOT NULL REFERENCES extraction_runs(id) ON DELETE CASCADE,
    capture_id bigint NOT NULL REFERENCES document_captures(id) ON DELETE RESTRICT,
    block_id bigint NOT NULL REFERENCES document_blocks(id) ON DELETE RESTRICT,
    mention_key text NOT NULL,
    mention_type text NOT NULL,
    value_original text NOT NULL,
    value_normalized text NOT NULL,
    page_number integer NOT NULL,
    block_ref text NOT NULL,
    block_order integer NOT NULL,
    block_bbox numeric(12, 4)[] NOT NULL,
    text_field text NOT NULL,
    char_start integer NOT NULL,
    char_end integer NOT NULL,
    snippet text NOT NULL,
    rule_name text NOT NULL,
    rule_version text NOT NULL,
    rule_pattern text NOT NULL,
    raw jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT mentions_run_mention_unique UNIQUE (extraction_run_id, mention_key),
    CONSTRAINT mentions_capture_block_ref_fk FOREIGN KEY (capture_id, block_ref)
        REFERENCES document_blocks(capture_id, block_id) ON DELETE RESTRICT,
    CONSTRAINT mentions_page_number_positive CHECK (page_number > 0),
    CONSTRAINT mentions_block_order_positive CHECK (block_order > 0),
    CONSTRAINT mentions_char_range_valid CHECK (char_start >= 0 AND char_end > char_start),
    CONSTRAINT mentions_block_bbox_four_values CHECK (array_length(block_bbox, 1) = 4),
    CONSTRAINT mentions_mention_type_not_blank CHECK (btrim(mention_type) <> ''),
    CONSTRAINT mentions_value_original_not_blank CHECK (btrim(value_original) <> ''),
    CONSTRAINT mentions_value_normalized_not_blank CHECK (btrim(value_normalized) <> ''),
    CONSTRAINT mentions_rule_name_not_blank CHECK (btrim(rule_name) <> ''),
    CONSTRAINT mentions_rule_version_not_blank CHECK (btrim(rule_version) <> '')
);

CREATE INDEX IF NOT EXISTS document_captures_document_id_idx
    ON document_captures(document_id);

CREATE INDEX IF NOT EXISTS document_pages_capture_id_idx
    ON document_pages(capture_id);

CREATE INDEX IF NOT EXISTS document_blocks_capture_page_order_idx
    ON document_blocks(capture_id, page_number, block_order);

CREATE INDEX IF NOT EXISTS document_blocks_text_normalized_gin_idx
    ON document_blocks USING gin (to_tsvector('portuguese', text_normalized));

CREATE INDEX IF NOT EXISTS extraction_runs_capture_id_idx
    ON extraction_runs(capture_id);

CREATE INDEX IF NOT EXISTS mentions_capture_type_value_idx
    ON mentions(capture_id, mention_type, value_normalized);

CREATE INDEX IF NOT EXISTS mentions_page_idx
    ON mentions(capture_id, page_number);

CREATE INDEX IF NOT EXISTS mentions_rule_idx
    ON mentions(rule_name, rule_version);

INSERT INTO schema_migrations (version)
VALUES ('001_initial_schema')
ON CONFLICT (version) DO NOTHING;

COMMIT;
