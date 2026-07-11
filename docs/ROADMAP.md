# Intent Pipeline — Build Roadmap

> Living plan for `hubspot-intent-pipeline`. Ordered by **dependency**, not by the
> loose "Phase/Milestone" labels in the module docstrings (those are reconciled below).
> No layer logic is implemented yet — every module under `src/intent_pipeline/` is a
> stub docstring. Phase 1 (scaffold) is committed and smoke tests pass.

---

## 1. Guiding principles (hold across every phase)

- **Cost-control invariant.** `DRY_RUN=true` by default. No layer may hit a paid API
  (Job board, Apollo, Anthropic) while `DRY_RUN` is on — it returns deterministic mock
  data instead. Every external-call layer needs a test proving this.
- **Schemas are the contract.** All cross-layer data moves as `schemas.py` Pydantic
  models. A layer never sees another layer's internals — only the shared record shapes.
- **Layers are decoupled and swappable.** L1 sources and L2.5 providers sit behind
  interfaces (`IngestionSource`, `EnrichmentProvider`) so concretes (job board, Apollo)
  can be replaced without touching consumers.
- **Storage is the single source of truth (L3).** Once persisted, downstream layers read
  from storage, not from upstream layers directly.
- **Threshold gating.** Enrichment only runs for leads with `intent_score >=
  ENRICHMENT_SCORE_THRESHOLD` (0.85). The orchestrator drafts at most
  `DAILY_EMAIL_LIMIT` (5) outreach emails/day, to `ADMIN_EMAIL`.

---

## 2. Dependency graph

```
                      schemas.py  (Phase 2 — foundation)
                          │
        ┌─────────────────┼──────────────────┐
        ▼                 ▼                  ▼
   L1 Ingestion      L2 Intelligence     L3 Storage
   (Phase 3)          (Phase 4)          (Phase 5)
        │                 │                  │
        └──────► tracer bullet L1→L2→L3 ◄─────┘   (proves the spine, DRY_RUN)
                          │
                          ▼
                  L2.5 Enrichment   (Phase 6 — needs L2 score + L3 cache)
                          │
                          ▼
                  L4 Orchestrator   (Phase 7 — queue + drafter)
                          │
                          ▼
                  End-to-end run     (Phase 8)
```

**Key reordering vs. the docstrings:** the stubs group Enrichment into "Milestone 3"
alongside Intelligence. But enrichment is **cache-first**, and the cache lives in L3
storage — so enrichment depends on both L2 (scores to gate on) *and* L3 (the cache).
It therefore lands **after** storage, in Phase 6.

---

## 3. Status lifecycle (define in Phase 2, enforced by L3)

```
RAW ──score──► SCORED ──(>=threshold)──► QUALIFIED ──enrich──► ENRICHED
                  │                                                │
              (<threshold)                                         ▼
                  ▼                                             QUEUED
              PARKED                                               │
                                                             ┌─────┴─────┐
                                                          DRAFTED     SKIPPED
                                                             │
                                                     SENT / REJECTED
```

Every record carries its state; the repository transitions it. This enum is the spine
of the whole pipeline and must be settled before any layer is written.

---

## 4. Phase-by-phase plan

### Phase 0 — Repo hygiene (pre-work, quick)
- Populate the empty `.gitignore` (build artifacts already tracked by mistake).
- Untrack `src/intent_pipeline.egg-info/` and all `__pycache__/*.pyc` (committed in `0dc3c82`).
- Decide the fate of leftover old-layout files: root `main.py`, `ingestion/`,
  `intelligence/`, and the empty `requirements.txt` (superseded by `pyproject.toml`).
- Refresh `CLAUDE.md` — it still documents the *old* linear ETL flow, not the 5-layer
  `src/` architecture. Misleads future sessions.
- **Exit:** clean `git status`, accurate CLAUDE.md, no dead files.

### Phase 2 — Data contracts (`schemas.py`)   *foundation*
- **Goal:** single source of truth for every record shape + the status enum.
- **Depends on:** nothing (pydantic already installed).
- **Deliverables:**
  - `RawRecord` — shape returned by any `IngestionSource` (source id, fetched-at, raw
    payload/text, company hints).
  - `ScoredLead` — raw + `intent_score: float [0,1]`, matched keywords, extracted
    firmographics, matched buyer profile (A/B/C).
  - `Contact` — decision-maker contact from enrichment (name, title, email, source).
  - `LeadStatus` / `BuyerProfile` enums.
- **Tests:** model validation (score bounds, enum membership), round-trip serialization.
- **Exit:** all downstream layers can import a stable contract.

### Phase 3 — L1 Ingestion (Milestone 1/2)
- **Goal:** fetch raw payloads from a swappable source; no analysis.
- **Depends on:** `schemas.RawRecord`.
- **Deliverables:**
  - `IngestionSource` ABC — `fetch()` → `list[RawRecord]`, rate-limit handling.
  - `JobBoardSource` — httpx client; `DRY_RUN` returns mock fixtures, live mode uses
    `JOB_BOARD_API_KEY`; pagination + rate limiting (shared helpers).
- **Tests:** DRY_RUN yields deterministic `RawRecord`s that validate against the schema.
- **Exit:** `for r in JobBoardSource().fetch(): assert isinstance(r, RawRecord)`.

### Phase 4 — L2 Intelligence (Milestone 3a)
- **Goal:** stateless scoring — raw text in, intent score + keywords out.
- **Depends on:** `schemas` (RawRecord in, ScoredLead out).
- **Deliverables:**
  - `profiles.py` — buyer profiles A/B/C: firmographic + hiring-signal criteria.
  - `scorer.py` — pure function: extract firmographics, match against profiles, return
    `intent_score ∈ [0,1]` + matched keywords. **No I/O** — fully unit-testable.
- **Tests:** known text → expected score band + keyword set; determinism.
- **Exit:** scorer runs offline with zero external calls.

### Phase 5 — L3 Storage + tracer bullet (the "Phase 4 tracer bullet")
- **Goal:** durable truth store + the first end-to-end slice.
- **Depends on:** `schemas`.
- **Deliverables:**
  - `database.py` — SQLite engine/session setup (`data/*.db`, gitignored).
  - `repository.py` — deep module: narrow read/write API (`save_raw`, `upsert_lead`,
    `save_contact`, `query_by_status`, status transitions). Hides all SQL.
  - **Tracer bullet:** wire L1 → L2 → L3 in DRY_RUN — ingest mock → score → persist.
    First real data flow; validates the schemas and interfaces cheaply.
- **Tests:** repo round-trips each model; tracer-bullet integration test.
- **Exit:** a mock lead flows ingest→score→store and is queryable by status.

### Phase 6 — L2.5 Enrichment (Milestone 3b)
- **Goal:** company → decision-maker contacts, cache-first, threshold-gated.
- **Depends on:** L2 (scores to gate on) **and** L3 (the cache/store).
- **Deliverables:**
  - `EnrichmentProvider` ABC — `enrich(company)` → `list[Contact]`.
  - `ApolloProvider` — cache-first (check L3 before calling), gated by `DRY_RUN` and
    `ENRICHMENT_SCORE_THRESHOLD`; uses `APOLLO_API_KEY` live.
- **Tests:** below-threshold leads are never enriched; cache hit skips the API; DRY_RUN
  returns mock contacts.
- **Exit:** qualified leads gain contacts without spending on repeat lookups.

### Phase 7 — L4 Orchestrator (Milestone 4)
- **Goal:** prioritize leads and draft rate-limited outreach.
- **Depends on:** everything above.
- **Deliverables:**
  - `queue.py` — dynamic priority queue: rank by opportunity score; high scores bypass
    older low-scoring leads.
  - `drafter.py` — LLM outreach drafter (Anthropic, `ANTHROPIC_API_KEY`) + rate limiter
    (≤ `DAILY_EMAIL_LIMIT`/day to `ADMIN_EMAIL`); gated by `DRY_RUN`.
- **Tests:** queue ordering invariants; daily limit enforced; DRY_RUN drafts without send.
- **Exit:** top-ranked leads produce draft emails within the daily cap.

### Phase 8 — End-to-end pipeline
- **Goal:** one entrypoint runs L1→L2→L2.5→L3→L4 on a schedule/CLI.
- **Deliverables:** pipeline runner, config validation, run logging, a full DRY_RUN
  integration test across all layers.
- **Exit:** `python -m intent_pipeline` completes a full dry run end-to-end.

---

## 5. Open decisions to resolve before/while building

1. **Old-layout cleanup (Phase 0):** delete root `main.py` / `ingestion/` / `intelligence/`
   / `requirements.txt`, or keep any of it?
2. **Enrichment ordering:** confirm Phase 6 placement (after storage) vs. the docstrings'
   "with intelligence" grouping.
3. **Migrations:** plain `create_all` for now, or bring in Alembic early?
4. **Job board target:** which concrete API is `JobBoardSource` hitting first?
5. **Scoring approach:** keyword/rule-based scorer to start, or model-assisted from day one?

---

## 6. Label reconciliation (docstrings → this roadmap)

| Docstring label            | This roadmap |
|----------------------------|--------------|
| Phase 1 (scaffold)         | done         |
| Phase 2 (schemas)          | Phase 2      |
| Milestone 1/2 (job board)  | Phase 3      |
| Milestone 3 (scorer/profiles) | Phase 4   |
| Phase 4 tracer bullet (storage) | Phase 5 |
| Milestone 3 (enrichment)   | Phase 6      |
| Milestone 4 (queue/drafter)| Phase 7      |
