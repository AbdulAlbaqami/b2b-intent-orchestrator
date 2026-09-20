# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**This is the agent's always-true constitution**, derived from `docs/PROJECT_SCOPE.md` §§5–8.
`docs/PROJECT_SCOPE.md` is the destination document (read at milestone boundaries / fork
resolutions); this file is the subset that is true every session. **Nothing here may
contradict the scope** — if reality changes, the scope is amended first, then this file.
The backlog lives in `issues/` (one slice per file).

## Project Purpose

`intent-pipeline` (repo dir `hubspot-intent-pipeline`) is a **B2B Intent Data Pipeline &
Agentic Orchestrator**. On a scheduled run it pulls public job postings, scores them for
buyer intent against three HubSpot buyer profiles, enriches high-scoring leads with
decision-maker contacts, persists everything in SQLite under a state machine, and drafts
personalized outreach — delivering **at most 5 advisory email digests per day to the
owner**, who retains sole send authority. Operated as "Client Zero" to drive affiliate
revenue in the IT/SaaS niche; architected so the scoring layer can later become a
commercial API. Pitch it as a production-grade intent data pipeline — never as an
"affiliate marketing tool."

## Environment Setup

Python 3.11+ (dev venv is 3.14 at `.venv/`), `src/` layout, editable install:

```bash
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env        # fill in secrets; NEVER commit .env
```

## Common Commands

```bash
pytest                                                 # suite (pythonpath=src, config in pyproject.toml)
pytest tests/test_smoke.py::test_dry_run_defaults_on   # a single test
ruff check .                                           # lint (line-length 100, py311)
ruff format .                                          # format
python -m intent_pipeline --dry-run                    # (Phase 8) full L1→L4 dry run
```

## Hard Rules (Non-Negotiable — Scope §7)

1. **DRY_RUN defaults ON** and is honored by every layer that touches network or money:
   L1 fetch, L2.5 enrichment, L4 drafting and email. When on, return deterministic mock data.
2. **Enrichment gate:** only leads with `intent_score > 0.85` may enrich; always cache-first;
   **misses are cached too** (negative cache) — providers charge only when data is found.
3. **≤ 5 advisory emails/day**, enforced **in the database** as a count of transitions to
   `EMAILED_TO_ADMIN` per UTC day — never in memory (must survive restarts).
4. **Human send authority:** the system NEVER emails a prospect. V1 delivers to the owner only.
5. **Secrets live in `.env` (gitignored) only** — never in code, logs, or fixtures.
6. **All timestamps UTC.**
7. **`schemas.py` is the only source of truth.** Every layer imports it; schema-conformance
   tests are written **before** implementation.
8. **Vertical slices only.** Every session delivers one thin slice that runs end-to-end (on
   mocks where needed), proven by a failing test turning green. One slice = one session =
   one commit. Discoveries become issues, never mid-session detours.

## Working Rules (How We Operate)

- **Context hygiene:** `/clear` and reload from disk between slices; never `/compact`. The urge
  to compact mid-slice means the slice is too big — split it.
- **Reload from disk:** at session start, reconstruct state from `CLAUDE.md` + `docs/HANDOFF.md`
  + the active `issues/` file + the relevant code — never from a compacted summary. Verify the
  handoff against `git status` before trusting it.
- **One job per file:** every file holds exactly ONE kind of information (destination →
  `PROJECT_SCOPE.md` · decided → `DECISIONS.md` · unresolved → `OPEN_QUESTIONS.md` · next →
  `issues/` · always-true → `CLAUDE.md` · current-frontier → `HANDOFF.md`). No file mixes
  decisions, state, logs, and output. If a doc grows past a few screens, it holds too many jobs —
  split it.
- **No logs in markdown:** run output, test results, and transcripts go to the terminal or
  gitignored log files — never into a tracked `.md`.
- **Version control is delegated (ADR-009):** the agent stages **explicit paths** (never
  `git add -A`), commits one slice at a time with a labeled message, and pushes when a remote
  exists. Never force-push, never rewrite pushed history, never stage `.env` or secrets.
  Destructive git (`reset --hard`, `clean -fd`, branch deletion) asks the owner first.

## Architecture — Five Layers, One Contract (Scope §5)

Data moves between layers **only** as `schemas.py` Pydantic models. Each layer exposes one
narrow interface (`base.py` ABC / the repository); internals are large and delegated.
The owner designs boundaries; the agent fills bodies. No scattering logic into shallow files.

```
Adzuna API → L1 Ingestion → L3 raw store → L2 Scoring → L3 leads (state machine)
                                                          │ score > 0.85
                                                          ▼
                                        L2.5 Enrichment (cache-first) → L3 contacts
                                                          │
                                                          ▼
                    L4 Priority queue → LLM drafter → ≤5 advisory emails/day → Owner
```

| Layer | Modules | Responsibility | Nature |
|---|---|---|---|
| **L1 Ingestion** | `ingestion/base.py`, `job_board.py` | `IngestionSource` ABC; fetch, pagination, rate-limit/backoff, DRY_RUN → fixtures | Volatile |
| **L2 Intelligence** | `intelligence/profiles.py`, `scorer.py` | Buyer profiles A/B/C; raw text → `intent_score` + keywords via spaCy PhraseMatcher + firmographic rules. **Pure, no I/O** | Stateless |
| **L2.5 Enrichment** | `enrichment/base.py`, `apollo.py`, `mock.py` | `EnrichmentProvider` ABC; company → contacts; threshold-gated, cache-first, misses cached | Gated |
| **L3 Storage** | `storage/database.py`, `repository.py` | SQLite + repository hiding SQL behind a narrow API; **owns all state transitions** | Truth |
| **L4 Orchestrator** | `orchestrator/queue.py`, `drafter.py` | Priority queue (`ORDER BY opportunity_score, created_at`); LLM drafter (Anthropic); daily cap; email | Agentic, capped |
| **Contracts** | `schemas.py` | Pydantic models + status enum — imported by every layer | Binding |

**Buyer profiles (L2):** A "Spreadsheet Graduate" → HubSpot CRM Starter · B "Automation
Seeker" → Marketing Hub · C "Ecosystem Upgrader" → Sales/Service Enterprise. Scoring is
**rule-based** (F3): spaCy PhraseMatcher + firmographics. Rules generate the labels a future
model would train on. Precision outweighs recall — every false positive burns an enrichment
credit and one of five daily email slots.

## Binding Contracts (Scope §6)

`schemas.py` defines: **RawRecord** (raw ingestion), **ScoredLead** (processed lead),
**Contact** (enrichment output) + an enrichment-attempt log (negative cache:
`company_key, provider, attempted_at, result_count`). Notable `ScoredLead` fields:
`intent_score` (0–1), `matched_profile` (A/B/C), `matched_keywords`, `opportunity_score`
(**V1: alias of `intent_score`**, reserved for firmographic weighting — documented, not
built), `tracking_code` (per-lead code in the draft CTA URL for click attribution),
`outcome` (nullable SENT/CLICKED/CONVERTED/DEAD — owner-recorded), `status`.

**Lead state machine** — transitions happen **only** through repository methods; any other
raises:

```
UNPROCESSED ──▶ QUEUED ──▶ DRAFTED ──▶ EMAILED_TO_ADMIN   (terminal)
     │             │
     └──▶ REJECTED ◀┘                                      (terminal)
```

`EMAILED_TO_ADMIN` and `REJECTED` are terminal — a lead can never be double-processed.
Enrichment is an attribute (a lead *has* contacts), not a status.

## In / Out of Scope (V1 — Scope §8)

**In:** API-keyed job-board ingestion (Adzuna primary) behind `IngestionSource`; rule-based
NLP scoring vs. profiles A/B/C; threshold-gated, cache-first enrichment behind
`EnrichmentProvider` (**mock acceptable for V1** — F2); SQLite + state machine; priority
queue + LLM drafter; ≤5 advisory emails/day; DRY_RUN end-to-end; contract-enforcing tests.

**Out:** sending anything to prospects; DOM/social scraping; landing pages (Phase 2);
commercial API (Phase 3); multi-user/auth/dashboards; Alembic (F5); model-based scoring
(F3); reselling any vendor's contact data (F7).

## Build Status & Open Forks

Phase 0 (repo hygiene) complete as of this slice — clean working tree and a truthful
constitution (Scope §9 Phase 0 / M1 exit criterion met); the decision ledger
(`docs/DECISIONS.md`) is seeded. Scaffold and tooling are in place; all `src/` modules are
stub docstrings. Phase 2 (`schemas.py`) has not started. Delivery plan is Scope §9;
decision forks are Scope §10.

- **F1 (dedup key) is OPEN and blocks Phase 2** — recommended resolution: `source_url`
  unique on RawRecord + normalized `hash(company_name + job_title)` at the lead layer, which
  requires adding `job_title` to RawRecord. Settle before writing `schemas.py`.
- **F2 (enrichment provider):** Apollo is gated behind a paid plan — **interface + mock
  through V1**; spike alternatives. The pattern (gating/caching/cost control) is the asset.
- Decided: SQLite (F4), `create_all` not Alembic (F5), rules-based scoring (F3),
  Anthropic + JSON drafter (F8), manual outcome capture (F9).

Next slice: resolve F1, then Phase 2 `schemas.py` (conformance tests first).
