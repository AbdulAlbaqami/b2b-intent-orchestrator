# Intent Pipeline

**B2B Intent Data Pipeline & Agentic Orchestrator** — a production-grade Python pipeline
that turns public hiring signals into ranked, enriched, outreach-ready opportunities under
strict cost controls and human send authority.

On a scheduled run it pulls fresh job postings from API-keyed job boards, scores each one
for buyer intent against three defined buyer profiles, enriches high-scoring leads with
decision-maker contacts, persists everything in SQLite under a strict state machine, and
drafts personalized outreach — delivering **at most 5 advisory email digests per day to the
owner**, who alone decides what to send. The system never contacts a prospect.

## Architecture — five decoupled layers, one contract

Data moves between layers only as Pydantic models from `schemas.py` (the single source of
truth). Each layer sits behind a narrow interface, so concretes are swappable.

```
Adzuna API → L1 Ingestion → L3 raw store → L2 Scoring → L3 leads (state machine)
                                                          │ score > 0.85
                                                          ▼
                                        L2.5 Enrichment (cache-first) → L3 contacts
                                                          │
                                                          ▼
                    L4 Priority queue → LLM drafter → ≤5 advisory emails/day → Owner
```

- **L1 Ingestion** (volatile) — `IngestionSource` ABC over API-keyed job boards (Adzuna
  primary); pagination, backoff, `DRY_RUN` → fixtures.
- **L2 Intelligence** (stateless, pure) — rule-based scoring (spaCy PhraseMatcher +
  firmographics) against buyer profiles A/B/C → `intent_score ∈ [0,1]` + matched keywords.
- **L2.5 Enrichment** (gated) — `EnrichmentProvider` ABC; company → decision-maker contacts;
  threshold-gated (> 0.85), cache-first, misses cached (negative cache). Mock provider in V1.
- **L3 Storage** (truth) — SQLite + repository hiding SQL; owns all lead state transitions.
- **L4 Orchestrator** (agentic, capped) — priority queue by opportunity score; LLM drafter
  (Anthropic); daily cap enforced in the database.

## Design principles

- **Contracts first.** `schemas.py` is binding; schema-conformance tests are written before
  any implementation.
- **Cost controls are structural.** `DRY_RUN` defaults ON (no paid API is touched until it's
  off); enrichment is threshold-gated and cache-first; the 5-emails/day cap lives in the
  database, per UTC day — restarts can't break it.
- **Human in the loop.** V1 delivers advisory digests to the owner only; sole send authority
  stays human.
- **Vertical slices.** Each session ships one thin slice that runs end-to-end on mocks,
  proven by a failing test turning green.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .\.venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env                                # then fill in secrets — NEVER commit .env
pytest
```

Stack: Python 3.11+ · setuptools `src/` layout · Pydantic v2 · spaCy · SQLite.

## Project docs

- **`docs/PROJECT_SCOPE.md`** — the locked destination document (vision, architecture,
  binding contracts, hard rules, delivery plan, decision forks).
- **`CLAUDE.md`** — the always-true constitution for AI-agent implementation, derived from
  the scope.
- **`issues/`** — the backlog, one slice per file.

## Status

Scaffold complete (Phases 0–1); all layer modules are stubs. Next: resolve the dedup-key
fork (F1), then implement `schemas.py` (Phase 2). Full delivery plan in `docs/PROJECT_SCOPE.md` §9.
