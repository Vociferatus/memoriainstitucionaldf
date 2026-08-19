-- Camada versionada de identidade material, separada das menções observadas.
BEGIN;

CREATE TABLE IF NOT EXISTS identity_runs (
    id bigserial PRIMARY KEY,
    transformation_run_id bigint NOT NULL UNIQUE REFERENCES transformation_runs(id),
    semantic_run_id bigint NOT NULL REFERENCES semantic_runs(id),
    schema_version text NOT NULL, policy jsonb NOT NULL, counts jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS identity_fragments (
    id bigserial PRIMARY KEY, identity_run_id bigint NOT NULL REFERENCES identity_runs(id) ON DELETE CASCADE,
    fragment_key text NOT NULL, entity_type text NOT NULL, source_kind text NOT NULL,
    source_key text NOT NULL, label text NOT NULL, block_id bigint NOT NULL REFERENCES document_blocks(id),
    published_item_id bigint REFERENCES published_items(id) ON DELETE SET NULL,
    page_number integer NOT NULL,
    char_start integer NOT NULL, char_end integer NOT NULL, observation_status text NOT NULL,
    method text NOT NULL, UNIQUE(identity_run_id, fragment_key),
    CHECK (char_start >= 0 AND char_end > char_start),
    CHECK (observation_status = 'observed_fragment')
);
CREATE INDEX IF NOT EXISTS identity_fragments_type_label_idx ON identity_fragments(entity_type, label);
ALTER TABLE identity_fragments DROP CONSTRAINT IF EXISTS identity_fragments_published_item_id_fkey;
ALTER TABLE identity_fragments ADD CONSTRAINT identity_fragments_published_item_id_fkey
    FOREIGN KEY (published_item_id) REFERENCES published_items(id) ON DELETE SET NULL;
CREATE TABLE IF NOT EXISTS identity_assertions (
    id bigserial PRIMARY KEY, fragment_id bigint NOT NULL REFERENCES identity_fragments(id) ON DELETE CASCADE,
    assertion_key text NOT NULL, attribute_name text NOT NULL, value_original text NOT NULL,
    value_normalized text NOT NULL, materiality_class char(1) NOT NULL, scope text,
    valid_from date, valid_to date, method text NOT NULL, UNIQUE(fragment_id, assertion_key)
);
CREATE TABLE IF NOT EXISTS material_identifiers (
    id bigserial PRIMARY KEY, fragment_id bigint NOT NULL REFERENCES identity_fragments(id) ON DELETE CASCADE,
    identifier_key text NOT NULL, identifier_type text NOT NULL, value_original text NOT NULL,
    value_normalized text NOT NULL, materiality_class char(1) NOT NULL, scope text NOT NULL,
    is_valid boolean NOT NULL, transferability text NOT NULL, method text NOT NULL,
    UNIQUE(fragment_id, identifier_key)
);
CREATE INDEX IF NOT EXISTS material_identifiers_lookup_idx ON material_identifiers(identifier_type, value_normalized);
CREATE TABLE IF NOT EXISTS canonical_entities (
    id bigserial PRIMARY KEY, identity_run_id bigint NOT NULL REFERENCES identity_runs(id) ON DELETE CASCADE,
    entity_key text NOT NULL, entity_type text NOT NULL, display_name text NOT NULL,
    entity_status text NOT NULL, materiality_basis char(1) NOT NULL, created_by_rule text NOT NULL,
    UNIQUE(identity_run_id, entity_key)
);
CREATE TABLE IF NOT EXISTS identity_links (
    id bigserial PRIMARY KEY, identity_run_id bigint NOT NULL REFERENCES identity_runs(id) ON DELETE CASCADE,
    link_key text NOT NULL, fragment_id bigint NOT NULL REFERENCES identity_fragments(id),
    canonical_entity_id bigint NOT NULL REFERENCES canonical_entities(id), decision text NOT NULL,
    reason text NOT NULL, rules jsonb NOT NULL, has_divergence boolean NOT NULL,
    review_status text NOT NULL, decision_version integer NOT NULL, UNIQUE(identity_run_id, link_key)
);
CREATE TABLE IF NOT EXISTS identity_candidate_groups (
    id bigserial PRIMARY KEY, identity_run_id bigint NOT NULL REFERENCES identity_runs(id) ON DELETE CASCADE,
    candidate_key_id text NOT NULL, entity_type text NOT NULL, candidate_key text NOT NULL,
    decision text NOT NULL, reason text NOT NULL, materiality_classes jsonb NOT NULL,
    missing_evidence jsonb NOT NULL, UNIQUE(identity_run_id, candidate_key_id)
);
CREATE TABLE IF NOT EXISTS identity_candidate_members (
    candidate_group_id bigint NOT NULL REFERENCES identity_candidate_groups(id) ON DELETE CASCADE,
    fragment_id bigint NOT NULL REFERENCES identity_fragments(id), PRIMARY KEY(candidate_group_id, fragment_id)
);
CREATE TABLE IF NOT EXISTS identity_resolution_cases (
    id bigserial PRIMARY KEY, identity_run_id bigint NOT NULL REFERENCES identity_runs(id) ON DELETE CASCADE,
    case_key text NOT NULL, entity_type text NOT NULL, case_type text NOT NULL, case_status text NOT NULL,
    divergences jsonb NOT NULL, analysis_chain jsonb NOT NULL, recommended_decision text NOT NULL,
    reason text NOT NULL, UNIQUE(identity_run_id, case_key)
);
CREATE TABLE IF NOT EXISTS identity_case_fragments (
    resolution_case_id bigint NOT NULL REFERENCES identity_resolution_cases(id) ON DELETE CASCADE,
    fragment_id bigint NOT NULL REFERENCES identity_fragments(id), PRIMARY KEY(resolution_case_id, fragment_id)
);

CREATE OR REPLACE VIEW navigable_material_entities AS
SELECT ir.id identity_run_id, ce.id canonical_entity_id, ce.entity_type, ce.display_name,
       ce.materiality_basis, ce.created_by_rule, count(il.id) fragment_count
FROM canonical_entities ce JOIN identity_runs ir ON ir.id=ce.identity_run_id
LEFT JOIN identity_links il ON il.canonical_entity_id=ce.id
GROUP BY ir.id, ce.id;
CREATE OR REPLACE VIEW navigable_identity_evidence AS
SELECT ir.id identity_run_id, ce.id canonical_entity_id, ce.entity_type, ce.display_name,
       f.fragment_key, f.label, f.source_kind, f.source_key, b.page_number, b.block_id,
       b.bbox, f.char_start, f.char_end, il.decision, il.reason, il.rules
FROM identity_links il JOIN identity_runs ir ON ir.id=il.identity_run_id
JOIN canonical_entities ce ON ce.id=il.canonical_entity_id
JOIN identity_fragments f ON f.id=il.fragment_id JOIN document_blocks b ON b.id=f.block_id;
CREATE OR REPLACE VIEW navigable_identity_review_queue AS
SELECT ir.id identity_run_id, rc.id resolution_case_id, rc.case_key, rc.entity_type,
       rc.case_type, rc.case_status, rc.divergences, rc.analysis_chain,
       rc.recommended_decision, rc.reason, count(icf.fragment_id) fragment_count
FROM identity_resolution_cases rc JOIN identity_runs ir ON ir.id=rc.identity_run_id
LEFT JOIN identity_case_fragments icf ON icf.resolution_case_id=rc.id
GROUP BY ir.id, rc.id;

INSERT INTO schema_migrations(version) VALUES ('004_material_identity') ON CONFLICT DO NOTHING;
COMMIT;
