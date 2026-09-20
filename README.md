# B2B Intent Orchestrator

*Status: early development — architecture and tooling in place; layer implementations in progress (see [Status](#status)).*

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

Requires **Python 3.11+**. Everything below runs offline: `DRY_RUN` defaults ON, so no paid
API is called and no email is sent until you explicitly turn it off.

```bash
git clone <repo-url>
cd b2b-intent-orchestrator
python -m venv .venv && source .venv/bin/activate    # Windows: .\.venv\Scripts\activate
pip install -e ".[dev]"                              # editable install + dev tools
cp .env.example .env                                 # configure — see below
pytest                                               # contract + smoke tests should pass
```

The full end-to-end dry run — `python -m intent_pipeline --dry-run`, exercising L1→L4 on
mock data — is the Phase 8 deliverable and is not wired up yet (see **Status**).

## Configuration

Copy `.env.example` to `.env` and fill in the values you need. Only `.env.example` (blank
placeholders) is committed — **your real `.env` is gitignored and never enters the repo.**
In the default `DRY_RUN=true` mode every value may stay blank; real keys are only required
to run live.

| Variable | Purpose |
|---|---|
| `DRY_RUN` | `true` (default) → mock data, no network or paid API, no email sent |
| `DATABASE_PATH` | SQLite database file location (e.g. `data/intent_pipeline.db`) |
| `ADMIN_EMAIL` | Address the advisory digests are delivered to |
| `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` | Adzuna job-board API credentials (L1) |
| `APOLLO_API_KEY` | Enrichment provider key (L2.5) — optional; V1 ships a mock provider |
| `ANTHROPIC_API_KEY` | LLM drafter (L4) |

The business thresholds — the `> 0.85` enrichment gate and the 5-emails/day cap — are
deliberately **not** environment settings. They are contract, defined as constants in code,
so a typo can't silently disable a rule the test suite is meant to guarantee.

## Tech stack

Python 3.11+ · setuptools `src/` layout · Pydantic v2 · spaCy · SQLite · Anthropic API.

## Status

Early development. The project scaffold and tooling are in place; all layer modules are
stubs pending the binding schema contract. Next up: `schemas.py` (Pydantic models + the lead
state machine), then the layers built in dependency order, L1 → L4, one vertical slice at a
time.
