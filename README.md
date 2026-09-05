# Kriyon BD Signal Agent — Phase 1

Internal signal-detection tool for Kriyon Technologies business development.
Phase 1 scope: **TED ingestion only**, for **DACH** (Germany, Austria,
Switzerland), targeting **mid-size** port/terminal/logistics operators,
scored across four axes, stored in Postgres, and written out as a daily
Markdown/CSV digest to disk.

No Slack, no CRM, no enrichment, no auto-send. See the project brief for
the full phase plan and hard constraints (agent never sends anything,
GDPR provenance on every personal-data field, no fabricated claims).

## Known limitation in this build: TED API access was not verified live

This codebase was written in a sandboxed environment where outbound access
to `api.ted.europa.eu` and `docs.ted.europa.eu` is blocked by network
policy. `src/kriyon_bd/ingest/ted_client.py` and `ted_parser.py` are built
against the **documented** TED Search API v3 contract (`POST
/v3/notices/search`, expert-query syntax, kebab-case eForms field names,
no auth required), sourced from third-party references, not verified
against a live response.

**Before trusting this for real ingestion:**
1. Confirm the request/response shape against the official Swagger at
   `https://ted.europa.eu/api/documentation/index.html` from a machine
   with network access.
2. Replace `tests/fixtures/ted_notices_raw/*.json` — those are
   **synthetic** notices modeled on the documented schema, clearly marked
   `"_fixture_note": "synthetic, not a real TED notice"`. The brief asks
   for ten *real* notices with your expected scores as the eval set; that
   swap has to happen wherever this runs with real network access, since
   it couldn't happen here.

## Setup

```bash
cp .env.example .env
# fill in ANTHROPIC_API_KEY at minimum

docker compose up -d postgres   # applies migrations/*.sql on first boot

pip install -e ".[dev]"

kriyon-bd ingest-ted            # pulls notices, dedupes, stores
kriyon-bd score                 # scores unscored signals via the rubric
kriyon-bd run-digest            # writes today's digest to data/digests/
```

Or all three in sequence via `scripts/run_daily.sh`, which is what cron
should call.

### Scheduling (Phase 1: cron)

```
0 6 * * * /path/to/kriyon_bd_agent/scripts/run_daily.sh >> /var/log/kriyon_bd.log 2>&1
```

## Config

All tunable, non-secret config lives in TOML under `config/`, not in code:

- `config/sources.toml` — TED query scope: countries, CPV codes reference,
  date window, page size.
- `config/cpv_codes.toml` — curated CPV code list + keywords, cross-referenced
  to Kriyon's five capability areas. Some codes are flagged
  `verified = false` where I could not confirm the code against the
  official CPV vocabulary from this sandbox — check those before relying
  on them.
- `config/rubric.toml` — the versioned scoring rubric (weights, per-axis
  prompt text, surfacing threshold). Bump `version` on every substantive
  edit; `signal_scores.rubric_version` records which version produced each
  score, so you can audit rubric changes against outcomes later (Phase 2).

## GDPR

Every row in the `contacts` table (the only personal-data table in Phase 1)
carries `source_url`, `retrieved_at`, and `legitimate_interest_basis`.
Purge a person or organisation's data with:

```bash
kriyon-bd purge --organisation-id <uuid>
kriyon-bd purge --contact-id <uuid>
kriyon-bd purge --contact-email someone@example.com
```

Every purge is logged to `deletion_log` (what was deleted, when, why) —
that log itself holds no personal data, only ids and counts.

## Tests

```bash
pytest --ignore=tests/test_classifier_eval.py   # fast, deterministic tests only
pytest tests/test_classifier_eval.py             # classifier eval (needs ANTHROPIC_API_KEY, costs money)
```

`tests/test_classifier_eval.py` runs the scoring classifier against
`tests/fixtures/ted_notices_raw/` and compares to
`tests/fixtures/expected_scores.yaml` — your hand-corrected scores. Update
the fixtures with real notices before treating this as a meaningful eval.

## Architecture note: the LLM boundary

Only `scoring/classifier.py` calls the Anthropic API. `ingest/` (fetching,
parsing, deduplication) and `digest/` (rendering) are deterministic code
with no model calls, so they're fully unit-testable without mocking an LLM.
