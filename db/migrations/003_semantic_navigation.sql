-- Projeção navegável da segmentação semântica observada.

BEGIN;

CREATE TABLE IF NOT EXISTS semantic_runs (
    id bigserial PRIMARY KEY,
    transformation_run_id bigint NOT NULL UNIQUE
        REFERENCES transformation_runs(id) ON DELETE RESTRICT,
    schema_version text NOT NULL,
    counts jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS editorial_sections (
    id bigserial PRIMARY KEY,
    semantic_run_id bigint NOT NULL REFERENCES semantic_runs(id) ON DELETE CASCADE,
    section_key text NOT NULL,
    label text NOT NULL,
    start_block_id bigint NOT NULL REFERENCES document_blocks(id) ON DELETE RESTRICT,
    start_page integer NOT NULL,
    UNIQUE (semantic_run_id, section_key)
);

CREATE TABLE IF NOT EXISTS editorial_contexts (
    id bigserial PRIMARY KEY,
    semantic_run_id bigint NOT NULL REFERENCES semantic_runs(id) ON DELETE CASCADE,
    section_id bigint NOT NULL REFERENCES editorial_sections(id) ON DELETE RESTRICT,
    context_key text NOT NULL,
    level integer NOT NULL,
    label text NOT NULL,
    breadcrumb jsonb NOT NULL,
    kind text NOT NULL,
    UNIQUE (semantic_run_id, context_key),
    CHECK (level BETWEEN 1 AND 3)
);

CREATE TABLE IF NOT EXISTS editorial_context_blocks (
    context_id bigint NOT NULL REFERENCES editorial_contexts(id) ON DELETE CASCADE,
    block_id bigint NOT NULL REFERENCES document_blocks(id) ON DELETE RESTRICT,
    ordinal integer NOT NULL,
    PRIMARY KEY (context_id, ordinal),
    UNIQUE (context_id, block_id)
);

CREATE TABLE IF NOT EXISTS published_items (
    id bigserial PRIMARY KEY,
    semantic_run_id bigint NOT NULL REFERENCES semantic_runs(id) ON DELETE CASCADE,
    section_id bigint NOT NULL REFERENCES editorial_sections(id) ON DELETE RESTRICT,
    item_key text NOT NULL,
    item_type text NOT NULL,
    title text NOT NULL,
    item_number text,
    date_literal text,
    start_page integer NOT NULL,
    end_page integer NOT NULL,
    breadcrumb jsonb NOT NULL,
    text_content text NOT NULL,
    UNIQUE (semantic_run_id, item_key),
    CHECK (start_page > 0 AND end_page >= start_page)
);

CREATE INDEX IF NOT EXISTS published_items_type_idx ON published_items(item_type);

ALTER TABLE published_items ADD COLUMN IF NOT EXISTS act_date date;

CREATE TABLE IF NOT EXISTS published_item_blocks (
    published_item_id bigint NOT NULL REFERENCES published_items(id) ON DELETE CASCADE,
    block_id bigint NOT NULL REFERENCES document_blocks(id) ON DELETE RESTRICT,
    ordinal integer NOT NULL,
    PRIMARY KEY (published_item_id, ordinal),
    UNIQUE (published_item_id, block_id)
);

CREATE TABLE IF NOT EXISTS semantic_provisions (
    id bigserial PRIMARY KEY,
    published_item_id bigint NOT NULL REFERENCES published_items(id) ON DELETE CASCADE,
    block_id bigint NOT NULL REFERENCES document_blocks(id) ON DELETE RESTRICT,
    provision_key text NOT NULL,
    kind text NOT NULL,
    label text NOT NULL,
    char_start integer NOT NULL,
    char_end integer NOT NULL,
    UNIQUE (published_item_id, provision_key),
    CHECK (char_start >= 0 AND char_end > char_start)
);

CREATE TABLE IF NOT EXISTS administrative_actions (
    id bigserial PRIMARY KEY,
    published_item_id bigint NOT NULL REFERENCES published_items(id) ON DELETE CASCADE,
    block_id bigint NOT NULL REFERENCES document_blocks(id) ON DELETE RESTRICT,
    action_key text NOT NULL,
    verb text NOT NULL,
    value_original text NOT NULL,
    char_start integer NOT NULL,
    char_end integer NOT NULL,
    observation_status text NOT NULL,
    method text NOT NULL,
    UNIQUE (published_item_id, action_key),
    CHECK (observation_status = 'observed_text'),
    CHECK (char_start >= 0 AND char_end > char_start)
);

CREATE INDEX IF NOT EXISTS administrative_actions_verb_idx ON administrative_actions(verb);

CREATE TABLE IF NOT EXISTS semantic_entity_mentions (
    id bigserial PRIMARY KEY,
    semantic_run_id bigint NOT NULL REFERENCES semantic_runs(id) ON DELETE CASCADE,
    published_item_id bigint REFERENCES published_items(id) ON DELETE CASCADE,
    block_id bigint NOT NULL REFERENCES document_blocks(id) ON DELETE RESTRICT,
    mention_key text NOT NULL,
    entity_type text NOT NULL,
    value_original text NOT NULL,
    value_normalized text NOT NULL,
    participation_role text NOT NULL,
    char_start integer NOT NULL,
    char_end integer NOT NULL,
    method text NOT NULL,
    UNIQUE (semantic_run_id, mention_key),
    CHECK (entity_type IN ('person', 'organization', 'position')),
    CHECK (char_start >= 0 AND char_end > char_start)
);

CREATE INDEX IF NOT EXISTS semantic_entity_type_value_idx
    ON semantic_entity_mentions(entity_type, value_normalized);

CREATE TABLE IF NOT EXISTS administrative_action_participants (
    action_id bigint NOT NULL REFERENCES administrative_actions(id) ON DELETE CASCADE,
    entity_mention_id bigint NOT NULL
        REFERENCES semantic_entity_mentions(id) ON DELETE CASCADE,
    participant_role text NOT NULL,
    PRIMARY KEY (action_id, entity_mention_id, participant_role)
);

CREATE TABLE IF NOT EXISTS semantic_references (
    id bigserial PRIMARY KEY,
    semantic_run_id bigint NOT NULL REFERENCES semantic_runs(id) ON DELETE CASCADE,
    published_item_id bigint NOT NULL REFERENCES published_items(id) ON DELETE CASCADE,
    block_id bigint NOT NULL REFERENCES document_blocks(id) ON DELETE RESTRICT,
    reference_key text NOT NULL,
    reference_type text NOT NULL,
    value_original text NOT NULL,
    value_normalized text NOT NULL,
    is_valid boolean,
    char_start integer NOT NULL,
    char_end integer NOT NULL,
    method text NOT NULL,
    UNIQUE (semantic_run_id, reference_key),
    CHECK (reference_type IN ('cnpj', 'monetary_value', 'norm')),
    CHECK (char_start >= 0 AND char_end > char_start)
);

CREATE INDEX IF NOT EXISTS semantic_references_type_value_idx
    ON semantic_references(reference_type, value_normalized);

CREATE OR REPLACE VIEW navigable_published_items AS
SELECT sr.id AS semantic_run_id,
       s.label AS section_label,
       pi.id AS published_item_id,
       pi.item_key,
       pi.item_type,
       pi.title,
       pi.item_number,
       pi.date_literal,
       pi.start_page,
       pi.end_page,
       pi.breadcrumb
FROM published_items pi
JOIN semantic_runs sr ON sr.id = pi.semantic_run_id
JOIN editorial_sections s ON s.id = pi.section_id;

CREATE OR REPLACE VIEW navigable_entity_occurrences AS
SELECT sem.semantic_run_id,
       sem.entity_type,
       sem.value_normalized,
       sem.participation_role,
       pi.id AS published_item_id,
       pi.title AS published_item_title,
       b.page_number,
       b.block_id,
       b.bbox,
       sem.char_start,
       sem.char_end,
       sem.value_original,
       sem.method
FROM semantic_entity_mentions sem
JOIN document_blocks b ON b.id = sem.block_id
LEFT JOIN published_items pi ON pi.id = sem.published_item_id;

CREATE OR REPLACE VIEW navigable_process_items AS
SELECT DISTINCT em.value_normalized AS process_number,
       pi.semantic_run_id,
       pi.id AS published_item_id,
       pi.title AS published_item_title,
       b.page_number,
       b.block_id,
       b.bbox,
       em.char_start,
       em.char_end
FROM evidence_mentions em
JOIN document_blocks b ON b.id = em.block_id
JOIN published_item_blocks pib ON pib.block_id = b.id
JOIN published_items pi ON pi.id = pib.published_item_id
WHERE em.mention_type = 'processo_sei';

CREATE OR REPLACE VIEW navigable_action_entities AS
SELECT pi.semantic_run_id,
       pi.id AS published_item_id,
       pi.title AS published_item_title,
       aa.id AS action_id,
       aa.verb,
       sem.entity_type,
       sem.value_normalized AS entity_value,
       aap.participant_role,
       b.page_number,
       b.block_id,
       b.bbox,
       sem.char_start,
       sem.char_end
FROM administrative_action_participants aap
JOIN administrative_actions aa ON aa.id = aap.action_id
JOIN semantic_entity_mentions sem ON sem.id = aap.entity_mention_id
JOIN published_items pi ON pi.id = aa.published_item_id
JOIN document_blocks b ON b.id = sem.block_id;

INSERT INTO schema_migrations (version)
VALUES ('003_semantic_navigation')
ON CONFLICT (version) DO NOTHING;

COMMIT;
