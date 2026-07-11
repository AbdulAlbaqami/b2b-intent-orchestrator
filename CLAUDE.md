# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

`hubspot-intent-pipeline` (package: `intent-pipeline`) is a B2B intent-data pipeline and
agentic orchestrator, part of the `Affiliate_Marketing_AI_Sys` project. It ingests raw
signals (job-board postings), scores them for buyer intent, resolves decision-maker
contacts, persists everything, and drafts rate-limited outreach.

## Environment Setup

Python ≥3.11 (dev venv is 3.14 at `.venv/`), `src/` layout, editable install:

```bash
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env        # then fill in secrets; NEVER commit .env
```

## Common Commands

```bash
pytest                      # run the suite (config in pyproject.toml; pythonpath=src)
pytest tests/test_smoke.py::test_dry_run_defaults_on   # a single test
ruff check .                # lint (line-length 100, target py311)
ruff format .               # format
```

## Cost-Control Invariant (critical)

`DRY_RUN=true` is the default (`src/intent_pipeline/config.py`). **No layer may call a
paid API (job board, Apollo, Anthropic) while `DRY_RUN` is on** — it must return
deterministic mock data instead. `tests/test_smoke.py::test_dry_run_defaults_on` guards
this. Two more gates: enrichment only runs for leads scoring ≥ `ENRICHMENT_SCORE_THRESHOLD`
(0.85); the drafter sends at most `DAILY_EMAIL_LIMIT` (5) emails/day to `ADMIN_EMAIL`.
All config comes from `.env` via pydantic-settings — secrets are never hard-coded.

## Architecture — five decoupled layers

Data moves between layers only as `schemas.py` Pydantic models (the single source of
truth for record shapes). Layers sit behind interfaces so concretes are swappable.

```
L1 Ingestion → L2 Intelligence → L2.5 Enrichment → L3 Storage → L4 Orchestrator
```

All modules under `src/intent_pipeline/` are currently **stub docstrings** — no layer
logic is implemented yet.

- **`schemas.py`** — Pydantic data contracts + status enums shared by all layers.
- **`ingestion/`** (L1, volatile) — `base.py` `IngestionSource` interface (fetch raw
  payloads, handle rate limits, return Raw records; no analysis); `job_board.py` concrete
  source (API-first, swappable).
- **`intelligence/`** (L2, stateless) — `scorer.py` reads raw text → `intent_score ∈ [0,1]`
  + matched keywords (pure, no I/O); `profiles.py` buyer profiles A/B/C.
- **`enrichment/`** (L2.5, identity resolution) — `base.py` `EnrichmentProvider` interface
  (company → decision-maker contacts, cache-first, threshold-gated); `apollo.py` concrete.
- **`storage/`** (L3, truth) — `database.py` SQLite engine/session; `repository.py` deep
  module: narrow read/write API over the schemas, hides SQL.
- **`orchestrator/`** (L4) — `queue.py` dynamic priority queue (ranks by opportunity
  score); `drafter.py` LLM outreach drafter + daily rate limiter.

## Layout

`src/intent_pipeline/` (package), `tests/`, `data/{raw,processed}/` (local store, `*.db`
and raw outputs gitignored), `docs/` (see `docs/ROADMAP.md` for the build plan),
`notebooks/`, `scripts/`, `issues/`.

## Build Status

Phase 1 (scaffold) complete; smoke tests pass. Next work is tracked in
`docs/ROADMAP.md` — dependency-ordered phases starting with `schemas.py` (Phase 2).
