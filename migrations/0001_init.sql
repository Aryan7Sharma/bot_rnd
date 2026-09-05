-- Phase 1 schema: TED ingestion, scoring, digest, GDPR provenance/purge.
-- Applied automatically by docker-compose (mounted into
-- /docker-entrypoint-initdb.d) on first Postgres boot. To apply by hand
-- against an existing instance: psql "$DATABASE_URL" -f migrations/0001_init.sql

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- gen_random_uuid()

-- Embedding dimension: Phase 1 uses a deterministic feature-hashing
-- embedding (see ingest/dedupe.py) to avoid a hard dependency on a paid
-- embedding API or a heavy ML runtime before we know we need one. 256
-- dims is that placeholder's output size. If you swap in a real embedding
-- model (sentence-transformers, Voyage, etc.), this column's dimension
-- must match and existing rows need re-embedding.
-- (No cross-file constant here since this is plain SQL; kept in sync by
-- hand with EMBEDDING_DIM in src/kriyon_bd/settings.py.)

CREATE TABLE organisations (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name                text NOT NULL,
    normalized_name     text NOT NULL,
    country             text,               -- ISO-3
    org_type            text,               -- port_authority | terminal_operator | freight_forwarder | other
    website             text,
    notes               text,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_organisations_normalized_name ON organisations (normalized_name);

CREATE TABLE signals (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source              text NOT NULL,               -- 'ted' in Phase 1
    source_id           text NOT NULL,                -- e.g. TED publication-number
    source_url          text NOT NULL,
    title               text NOT NULL,
    summary             text NOT NULL,
    raw_payload         jsonb NOT NULL,               -- full original API response, for audit
    cpv_codes           text[] NOT NULL DEFAULT '{}',
    country             text,                         -- ISO-3, buyer country
    buyer_name          text,                         -- raw buyer name as it appears on the notice
    organisation_id     uuid REFERENCES organisations(id), -- resolved match, populated from Phase 3 enrichment onward
    publication_date    date,
    deadline_date       date,
    content_hash        text NOT NULL,                -- exact-duplicate check
    embedding           vector(256),                  -- near-duplicate check, see note above
    retrieved_at        timestamptz NOT NULL,
    created_at          timestamptz NOT NULL DEFAULT now(),
    UNIQUE (source, source_id)
);

CREATE INDEX idx_signals_content_hash ON signals (content_hash);
CREATE INDEX idx_signals_embedding ON signals USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_signals_organisation_id ON signals (organisation_id);
CREATE INDEX idx_signals_publication_date ON signals (publication_date);

CREATE TABLE signal_scores (
    id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id               uuid NOT NULL REFERENCES signals(id) ON DELETE CASCADE,
    rubric_version          text NOT NULL,
    fit_score               smallint NOT NULL CHECK (fit_score BETWEEN 0 AND 5),
    fit_justification       text NOT NULL,
    timing_score            smallint NOT NULL CHECK (timing_score BETWEEN 0 AND 5),
    timing_justification    text NOT NULL,
    reachability_score      smallint NOT NULL CHECK (reachability_score BETWEEN 0 AND 5),
    reachability_justification text NOT NULL,
    evidence_score          smallint NOT NULL CHECK (evidence_score BETWEEN 0 AND 5),
    evidence_justification   text NOT NULL,
    total_score             smallint NOT NULL,
    surfaced                boolean NOT NULL,
    model_name              text NOT NULL,
    raw_model_response      jsonb NOT NULL,
    scored_at               timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_signal_scores_signal_id ON signal_scores (signal_id);
CREATE INDEX idx_signal_scores_surfaced ON signal_scores (surfaced, total_score DESC);

-- The only personal-data table in Phase 1: TED notices often list a named
-- contact point (name/email/phone) for the tender. Every row must carry
-- GDPR provenance per the project's hard constraints.
CREATE TABLE contacts (
    id                          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id                   uuid REFERENCES signals(id) ON DELETE SET NULL,
    organisation_id             uuid REFERENCES organisations(id) ON DELETE SET NULL,
    name                        text,
    role                        text,
    email                       text,
    phone                       text,
    source_url                  text NOT NULL,
    retrieved_at                timestamptz NOT NULL,
    legitimate_interest_basis   text NOT NULL,
    created_at                  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_contacts_organisation_id ON contacts (organisation_id);
CREATE INDEX idx_contacts_email ON contacts (email);

-- Audit trail for GDPR purges. Holds no personal data itself, only ids,
-- counts and the stated reason.
CREATE TABLE deletion_log (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    target_type         text NOT NULL,      -- 'organisation' | 'contact'
    target_id           uuid NOT NULL,
    reason              text,
    deleted_counts      jsonb NOT NULL,     -- {"contacts": 3, "signals": 0, ...}
    deleted_at          timestamptz NOT NULL DEFAULT now()
);
