# Intent Pipeline — Unified Project Scope (V1)

**Full name:** B2B Intent Data Pipeline & Agentic Orchestrator
**Repo:** `intent-pipeline` (private GitHub) · **Stack:** Python 3.11+, venv/pip, setuptools src layout, Pydantic, spaCy, SQLite
**Version:** 1.2 · **Date:** 2026-07-11 · **Status:** DRAFT until owner sign-off, then LOCKED
**Supersedes:** "HubSpot Intent Matching Pipeline: V1 Architecture & Schema" (**Scope A**) and "Project Scope: B2B Intent Data Pipeline & Agentic Orchestrator" (**Scope B**). Both are retired to `docs/archive/` on sign-off.
**v1.1 changes:** added the Phase-1 value loop (§2), `tracking_code` + `outcome` fields (§6.2), vertical-slice hard rule (§7.8), fork F9 outcome capture (§10), outreach-compliance risk (§12).
**v1.2 changes:** added fork F10 (geographic scope — US-only V1 default).

---

## 1. Why This Document Exists

Two scope documents accumulated during planning: Scope A described a 3-layer intent-matching pipeline ending at a JSON handoff; Scope B expanded it into a 5-layer system with identity enrichment and an agentic orchestrator. They describe **one project at two moments in time** — Scope B explicitly extends Scope A — but keeping both alive created drift and confusion. This document is the single reconciliation. From sign-off forward:

- This is the **destination document**: it says where the project is going and where it may fork. It is read at milestone boundaries and when a fork in §10 resolves — not every session.
- `CLAUDE.md` carries the *always-true subset* of this document for the agent. The issues board carries the backlog. The playbook carries the ritual. Nothing in those artifacts may contradict this document; if reality changes, this document is amended first (see §15).
- **Anti-rot policy:** any idea, change, or discovery that is not a fork resolution goes to the issues board or the decision ledger — not into this document.

## 2. Vision and Objectives

**Vision.** A production-grade B2B intent data pipeline that turns public hiring signals into ranked, enriched, outreach-ready opportunities — built solo with AI-agent implementation under human architectural control, operated first as "Client Zero" to drive affiliate revenue in the IT/SaaS niche, and architected so its scoring intelligence can later be exposed as a commercial API.

**Objectives, ranked.** When objectives conflict, the higher one wins.

1. **Interview asset (primary).** By December graduation, this project is the centerpiece of the resume and the main interview subject: architecture, tradeoffs, tooling, and defensible decisions. *Standing rule: nothing gets built that the owner cannot defend in an interview.*
2. **Foundry project (secondary).** The system produces real affiliate-revenue opportunities in Phase 1 and preserves a credible path to a commercial product (Phase 3).
3. **Learning vehicle (tertiary, time-boxed).** Concepts are learned in the AFK block of the phase that needs them, captured as one ledger note, and left behind. Learning never blocks shipping; the pre-interview review in November is where notes get consolidated.

**The narrative.** This is pitched as a *production-grade intent data pipeline* — decoupled layered architecture, strict schema enforcement, relational modeling, NLP feature extraction, and an agentic orchestrator with real cost controls — never as "an affiliate marketing tool."

**The value loop (Phase 1 — Client Zero).** The pipeline's commercial job ends at a *qualified click*, not a sale. The full loop: hiring signal → intent score → enriched decision-maker → drafted outreach → **owner reviews and sends** → prospect clicks a tracked link → profile-matched comparison landing page (the Phase 2 asset) → affiliate link → the vendor closes the sale → commission. Everything left of "owner sends" is this system; everything to the right is the owner's marketing operation. Three design consequences follow: **(1)** the drafted email's call-to-action is always a link to the comparison page matching the lead's `matched_profile` — useful content, not a pitch — so the profile→URL mapping is drafter configuration (F8); **(2)** every draft embeds a per-lead `tracking_code` in that URL so clicks attribute back to specific leads; **(3)** outcomes (sent / clicked / converted / dead) are recorded on the lead — manually in V1 (F9) — because outcomes are simultaneously the ROI measure *and* the labeled data fork F3 needs before scoring can ever become a model. Expectation-setting: at 5 sends/day (~150/month), Phase 1 income will be modest; its real yield is a proven loop, live attribution data, and training labels. Other marketers plug the same payload into their own delivery mechanism (F7) — the loop above is Client Zero's instance of the product, not a constraint of it.

## 3. One Project, Not Two — the Reconciliation

| Dimension | Scope A said | Scope B said | **V1 resolution** |
|---|---|---|---|
| Layers | 3 (Ingestion, Intelligence, Storage); L2.5 added in a late update | 4 tiers + Agentic Orchestrator | **Five layers: L1, L2, L2.5, L3, L4** |
| Delivery boundary | Output clean JSON to n8n/Zapier and stop | LLM drafts copy; 5 advisory emails/day to the owner | **Advisory email to owner is the V1 delivery.** The JSON payload survives as the *internal* L3→L4 contract. External API/n8n handoff is deferred to Phase 3 (fork F7). |
| Lead status enum | NEW, OUTREACH_PENDING, REJECTED | UNPROCESSED, QUEUED, DRAFTED, EMAILED_TO_ADMIN | **Unified state machine in §6.4.** Scope A's enum is retired. |
| Data sources | Job boards via DOM scraping (BeautifulSoup/Playwright) | Job boards; social scraping excluded | **API-keyed job boards only** (Adzuna primary). No DOM scraping in V1. `source_type` field defaults to `JOB_BOARD`, keeping the door open. |
| Enrichment | Layer 2.5 via Apollo, threshold-gated, cache-first | Implied within architecture | **Provider interface (`EnrichmentProvider` ABC).** Apollo is *one* implementation behind it — see fork F2 for the pricing wall discovered 2026-07. |
| Cost control | Dry-run flag, caching, threshold gate | Dry-run mandatory; 5/day cap | **All of it, consolidated as Hard Rules (§7).** |

**Verdict:** Scope A is absorbed, not abandoned. Its schemas and layer discipline carry forward; its delivery boundary and status enum are superseded. Archive both source documents.

## 4. The System in One Paragraph

On a scheduled run, Layer 1 pulls fresh job postings from API-keyed job boards and stores them as immutable raw records. Layer 2 — stateless and pure — scores each record against three HubSpot buyer profiles (A: "Spreadsheet Graduate" → CRM Starter; B: "Automation Seeker" → Marketing Hub; C: "Ecosystem Upgrader" → Sales/Service Enterprise) using spaCy keyword/phrase matching plus firmographic rules, producing an `intent_score ∈ [0,1]` and matched keywords. Leads clearing the storage threshold become tracked leads in SQLite (Layer 3), governed by a status state machine. Leads scoring above **0.85** trigger Layer 2.5: a cache-first lookup of decision-maker contacts through an enrichment-provider interface — never paying twice for the same company, including cached misses. Layer 4 ranks queued leads by opportunity score, drafts personalized outreach copy with an LLM for the top of the queue, and emails **at most 5 advisory digests per day** to the owner — lead context, strategy, drafted copy. The owner retains sole send authority; the system never contacts a prospect.

```
Adzuna API ──▶ L1 Ingestion ──▶ L3 raw store ──▶ L2 Scoring ──▶ L3 leads (state machine)
                                                                    │ score > 0.85
                                                                    ▼
                                                   L2.5 Enrichment (cache-first) ──▶ L3 contacts
                                                                    │
                                                                    ▼
                            L4 Priority queue ──▶ LLM drafter ──▶ ≤5 advisory emails/day ──▶ Owner (human send authority)
─────────────────────────────────────────── system boundary ───────────────────────────────────────────
Owner sends ──▶ prospect clicks tracked link ──▶ profile comparison page ──▶ affiliate link ──▶ commission
```

## 5. Architecture — Five Layers, One Contract

| Layer | Modules | Responsibility | Nature |
|---|---|---|---|
| **L1 Ingestion** | `ingestion/base.py`, `ingestion/job_board.py` | `IngestionSource` ABC; fetch raw payloads, pagination, rate-limit handling, DRY_RUN → fixture records | Volatile |
| **L2 Intelligence** | `intelligence/profiles.py`, `intelligence/scorer.py` | Buyer profiles A/B/C; raw text → `intent_score` + matched keywords. Pure functions, no I/O | Stateless |
| **L2.5 Enrichment** | `enrichment/base.py`, `enrichment/apollo.py`, `enrichment/mock.py` | `EnrichmentProvider` ABC; company → decision-maker contacts; threshold-gated, cache-first, misses cached | Gated |
| **L3 Storage** | `storage/database.py`, `storage/repository.py` | SQLite engine + repository hiding SQL behind a narrow API; owns all state transitions | Truth |
| **L4 Orchestrator** | `orchestrator/queue.py`, `orchestrator/drafter.py` | Priority queue by opportunity score; LLM drafter; daily cap; email delivery | Agentic, capped |
| **Contracts** | `schemas.py` | Pydantic models + status enum — the single source of truth every layer imports | Binding |

**Deep-module rule.** Each layer exposes one narrow interface (`base.py` / the repository); internals are large and delegated to the agent. The owner designs the boundaries; the agent fills the bodies. No scattering of logic into shallow files.

## 6. Binding Contracts

Schemas are contracts from day one. Schema-conformance tests are written **before** any implementation. Fields marked ⚑ depend on fork F1 (open).

### 6.1 RawRecord (raw ingestion)

| Field | Type | Notes |
|---|---|---|
| `raw_id` | UUID | Primary key |
| `scraped_at` | Timestamp (UTC) | Time of capture |
| `source_type` | String | Default `"JOB_BOARD"` — future-proofing |
| `source_url` | String | Origin URL ⚑ candidate uniqueness key |
| `company_name` | String | Extracted entity name |
| `job_title` | String ⚑ | Pending F1 — required if dedup uses company+title hash |
| `raw_text_payload` | Text | Full unedited posting text |

### 6.2 ScoredLead (processed lead)

| Field | Type | Notes |
|---|---|---|
| `lead_id` | UUID | Primary key |
| `raw_id_ref` | UUID | FK → RawRecord |
| `company_name` | String | Cleaned |
| `intent_score` | Float 0.0–1.0 | From L2 |
| `matched_profile` | Enum A/B/C | Which buyer profile fired |
| `matched_keywords` | Array[String] | Trigger phrases |
| `opportunity_score` | Float | **V1: alias of `intent_score`.** Reserved extension point for firmographic weighting — documented, not built |
| `tracking_code` | String | Short unique per-lead code embedded in the draft's CTA URL — attributes clicks back to the lead |
| `outcome` | Nullable Enum | SENT / CLICKED / CONVERTED / DEAD — owner-recorded in V1 (F9); the label source for F3 |
| `status` | Enum | See §6.4 |
| `created_at` / `updated_at` | Timestamp (UTC) | Audit |

### 6.3 Contact (enrichment output) + enrichment attempt log

| Field | Type | Notes |
|---|---|---|
| `contact_id` | UUID | Primary key |
| `lead_id_ref` | UUID | FK → ScoredLead (one-to-many) |
| `first_name`, `last_name`, `job_title`, `email_address` | String | From provider |
| `provider` | String | Which enricher produced it — future-proofing |
| `enrichment_date` | Timestamp (UTC) | |

**Enrichment attempt log (negative cache):** `(company_key, provider, attempted_at, result_count)`. Providers charge only when data is found, so a miss that isn't cached will be silently re-paid forever. Misses are first-class records.

### 6.4 Lead Lifecycle — the State Machine

```
UNPROCESSED ──▶ QUEUED ──▶ DRAFTED ──▶ EMAILED_TO_ADMIN   (terminal)
     │             │
     └──▶ REJECTED ◀┘                                      (terminal)
```

Rules: transitions happen **only** through repository methods; any other transition raises. `EMAILED_TO_ADMIN` and `REJECTED` are terminal — a lead can never be double-processed. The 5/day cap is enforced *in the database* as a count of transitions to `EMAILED_TO_ADMIN` per UTC day, never in memory. Enrichment is an attribute (a lead *has* contacts), not a status — the machine stays minimal. Exact transition guards get locked in the schemas session.

## 7. Hard Rules (Non-Negotiable)

1. **DRY_RUN** defaults ON and is honored by every layer that touches network or money: L1 fetch, L2.5 enrichment, L4 drafting and email.
2. **Enrichment gate:** only `intent_score > 0.85`, always cache-first, misses cached (§6.3).
3. **5 advisory emails/day**, enforced in the database per UTC day.
4. **Human send authority:** the system never emails a prospect. Ever. V1 delivers to the owner only.
5. **Secrets** live in `.env` (gitignored) only — never in code, logs, or fixtures.
6. **All timestamps UTC.**
7. **`schemas.py` is the only source of truth.** Every layer imports it; conformance tests precede implementation.
8. **Vertical slices only.** Every implementation session delivers one thin slice that runs end-to-end (on mocks where needed) and is proven by its failing test turning green — never a horizontal layer built in isolation. One slice = one session = one commit; discoveries become issues, never mid-session detours. This rule is injected into every AFK implementation via CLAUDE.md and the `/new-slice` skill.

## 8. In Scope / Out of Scope (V1)

**In scope:** API-keyed job-board ingestion (Adzuna primary) behind an `IngestionSource` interface; rule-based NLP intent scoring against Profiles A/B/C; threshold-gated, cache-first enrichment behind an `EnrichmentProvider` interface (mock acceptable for V1 — F2); SQLite storage with strict schemas and the state machine; priority queue + LLM drafter; up to 5 internal advisory emails/day; DRY_RUN end-to-end; test suite enforcing every contract.

**Out of scope (V1):** sending anything to prospects; DOM or social-media scraping; landing pages (Phase 2, pre-October); commercial/subscription API (Phase 3); multi-user, auth, or dashboards; Alembic migrations (F5); model-based scoring (F3); reselling any vendor's contact data (F7 — ToS constraint).

## 9. Delivery Plan — Phases and Milestones

Dependency-ordered phases (numbering preserved from the roadmap/issues board; Phase 1 was merged into 0/2 during reconciliation). Indicative pace: ~12 weeks from mid-July → early October, leaving a November buffer before December graduation. Owner pins calendar dates on the issues board.

| Phase | Deliverable | Exit criterion | Milestone |
|---|---|---|---|
| 0 | Repo hygiene: `.gitignore`, untrack junk, delete old-layout files, rewrite `CLAUDE.md`, `.env` scaffold | Clean tree; agent loads a truthful constitution | M1 |
| 2 | `schemas.py`: RawRecord, ScoredLead, Contact, status enum, F1 resolved | Conformance tests green; illegal transitions raise | M1 |
| 3 | L1: `IngestionSource` ABC + `JobBoardSource`; DRY_RUN → fixtures from real Adzuna response | Mock ingestion emits schema-valid RawRecords | M1 |
| 4 | L2: profiles A/B/C + pure scorer | Known fixtures score as expected; zero I/O in layer | M1 |
| 5 | L3: SQLite + repository; **first tracer flow** ingest→score→store on mocks | One command runs the half-pipeline dry | M1 ✦ |
| — | Live pass: real Adzuna key, backoff, pagination, dedup in anger | ≥1 scheduled live ingestion run stored cleanly | M2 |
| 6 | L2.5: provider ABC + mock (+ real provider if F2 resolves); gate + caches | Gate provably blocks <0.85; miss re-query costs zero | M3 |
| 7 | L4: queue (`ORDER BY opportunity_score, created_at`) + drafter + cap + email | 5/day cap holds under test; drafts render | M4 |
| 8 | End-to-end: `python -m intent_pipeline --dry-run` | Full L1→L4 dry run, tests green | M4 ✦ |

**Tracer-bullet definition:** the thinnest slice touching every layer on mocks. Half-tracer lands at Phase 5; the full tracer is the Phase 8 dry run. Slice sizing stays 1 slice ≈ 1 session ≈ 1 commit; anything bigger gets split.

## 10. Road Divergence Map (Decision Forks)

Every known point where the road can split. Defaults are chosen; each fork records what would trigger revisiting. **Changing direction at a fork requires amending this section — nothing else in the doc.**

| # | Fork | Options | V1 default | Revisit trigger | Status |
|---|---|---|---|---|---|
| F1 | **Dedup key** — what makes two postings the same lead? | (a) unique `source_url` only; (b) add `job_title`, dedup on hash(company+title); (c) hash of full payload | **Recommended: (a)+(b)** — `source_url` unique on RawRecord, content-hash on lead for cross-board dupes | First real duplicate observed | **OPEN — blocks Phase 2** |
| F2 | **Enrichment provider** — Apollo API is gated behind Organization plan (~$119/user/mo, 3-seat min); free tier ~100 credits, ToS forbids external resale | (a) mock-only V1; (b) alternative free-tier provider (Hunter et al. — verify in spike); (c) pay | **Interface + mock through V1;** spike alternatives | Spike results; budget decision | Spike pending |
| F3 | **Scoring method** | rules → weighted rules → trained model | **Rules** (spaCy PhraseMatcher + firmographics). Rules generate the labels a future model trains on | ~100+ labeled outcomes exist | Decided |
| F4 | **Storage engine** | SQLite → Postgres | **SQLite** | Concurrent writers, deployment, or multi-tenant | Decided |
| F5 | **Migrations** | `create_all` → Alembic | **`create_all`** | First schema change after real data exists | Decided |
| F6 | **Email delivery** | console/file digest → SMTP (app password) → transactional provider | **Console through dev; SMTP by M4 exit** | Deliverability needs | Decided |
| F7 | **Commercial boundary (Phase 3)** | sell scoring/signal API; clients bring their own enrichment keys | Deferred — recorded so Phase 1 builds nothing that forecloses it. Constraint: never resell vendor contact data | Phase 3 kickoff | Deferred |
| F8 | **Drafter LLM & format** | Anthropic API; structured JSON output; prompts as versioned config files | As stated | Cost/quality review at M4 | Decided |
| F9 | **Outcome capture** — how does a click or conversion get back onto the lead? | manual recording by owner → redirect/click-logging service → affiliate-network reporting pull | **Manual in V1** — owner updates `outcome` | Phase 2 landing pages live | Decided |
| F10 | **Geographic scope** — which market does V1 target? | US-only → add UK/EU → multi-region | **US-only V1** — Adzuna is per-country, spaCy `en` pipeline, owner's compliance context is US (CAN-SPAM) | V1 loop proven; Phase 3 market decision | Decided — confirm at sign-off |

**Live forks in words.** *F1* is the only decision blocking the next coding session: recommendation is `source_url` uniqueness at the raw layer plus a normalized `hash(company_name + job_title)` at the lead layer, which requires adding `job_title` to RawRecord — ten seconds now versus a migration later. *F2* is the wall found on 2026-07-11: the architecture already absorbs it because L2.5 is an interface, and a mock-only V1 loses zero portfolio value — the pattern (gating, caching, cost control) is the asset, not the vendor.

## 11. Learning Curve Map — First-Big-Project Edition

Rule: learn each concept in the AFK block of the phase that needs it, write one ledger note, move on. November = consolidation pass before interviews.

| Phase | Concepts you will hit | Why it matters (the interview line) |
|---|---|---|
| 0–2 | src layout & packaging, venv discipline, Pydantic v2 models/validators, ABCs | "Schemas as binding contracts — when the agent knows exact I/O, it rarely fails the implementation" |
| 3 | REST pagination, exponential backoff & 429s, fixtures captured from real responses, idempotency | "I designed ingestion to be volatile by contract — failures never corrupt truth" |
| 4 | spaCy PhraseMatcher, precision vs recall, pure functions | "Precision outweighs recall here: every false positive burns an enrichment credit and one of five daily email slots — a cost-weighted threshold" |
| 5 | Repository pattern, SQLite semantics & limits, transactions, state machines | "Illegal states are unrepresentable — a lead cannot double-process, and I can say exactly what would force Postgres" |
| 6 | API cost-control patterns, caching incl. negative caching, provider abstraction | "When the vendor's pricing changed under me, swapping cost one file" |
| 7 | Structured LLM output, prompt-as-config, DB-enforced rate caps, priority queues in SQL | "The 5/day cap lives in the database, not in memory — restarts can't break it" |
| 8 | CLI entrypoints (`python -m`), end-to-end testing | "One command proves the whole system" |
| Cross-cutting | TDD with agents, context hygiene (Smart Zone, /clear), ADR/decision ledger, senior-style code review | "I ran the agent like a team: contracts first, failing test, review every diff" |

**Expected friction (normal, not failure):** day-one import errors from the src layout; the urge to "just test it in a notebook" (banned — fix it in the repo with a test); the first live 429 rate limit; fixture drift when the real API differs from the mock. Each is a rite of passage; each becomes a ledger note.

## 12. External Dependencies and Risks

Seeds `docs/risks.md`, the living register. Verified 2026-07-11.

| Item | Status | Impact | Mitigation / fallback |
|---|---|---|---|
| Adzuna API | Free developer key; REST search; ≤50 results/page; free-tier rate limits | Primary L1 source | Fixture-first development; backoff; second source is a subclass, not a rewrite |
| Apollo | API access gated behind Organization plan; free tier ~100 credits/mo; ToS forbids powering external products with their data | L2.5 real data | F2: mock through V1; spike alternatives; commercial path sells own signals only |
| LLM API cost | Drafter tokens | Budget | DRY_RUN default, 5/day cap, prompt budget per draft |
| Data quality | Postings missing company names; cross-board duplicates | Score noise, wasted credits | Validation at ingestion; F1 dedup; REJECTED path |
| Time | ~12-week plan → early Oct; graduation in December | Portfolio deadline | Tracer early; slice discipline; November is buffer + interview prep, not build time |
| Solo blind spots | First big project, no senior on call | Design misses | Decision ledger; this document; one human senior review of the one-pager before M3 |
| Scope creep | Foundry ambitions + new ideas mid-build | Timeline | New ideas become issues or Phase-3 notes — never mid-session detours |
| Outreach compliance | Owner manually sends cold B2B email; rules such as CAN-SPAM require truthful subjects, sender identity + postal address, and an opt-out path | Deliverability, legal | Drafter template bakes required elements in; owner reviews every send; read the basics before first live send (not legal advice) |

## 13. Definition of Done (V1)

1. `python -m intent_pipeline --dry-run` executes L1→L4 end-to-end on mocks; full test suite green.
2. Live mode: scheduled Adzuna ingestion; scoring; storage; queue; ≤5 drafted advisory emails/day arriving in the owner's inbox for at least 5 consecutive days.
3. State machine provably prevents double-processing (dedicated test); daily cap holds under restart.
4. Repo hygiene: no secrets anywhere in history-facing files; clean clone + README quickstart works.
5. Decision ledger ≥ 25 entries; `docs/risks.md` current.
6. The 5-minute cold walkthrough script exists in `docs/` and the owner can deliver it without notes.

## 14. The Interview Narrative

*"I architected and shipped a production-grade B2B intent data pipeline: five decoupled layers in Python with Pydantic schemas as binding contracts, rule-based NLP scoring against defined buyer profiles, threshold-gated identity enrichment behind a provider interface, SQLite storage governed by a state machine that makes double-processing impossible, and an LLM orchestrator with database-enforced cost caps. I ran AI agents as my implementation team — contracts first, failing test first, every diff reviewed — and kept an architecture decision ledger throughout. When my enrichment vendor's pricing changed mid-project, the swap cost one file, because the boundary was mine and the vendor was replaceable."*

Embedded senior signals: contracts-first design · provider interfaces that survived a real vendor pricing change · cost-weighted thresholds argued in dollars · DB-enforced caps · state-machine correctness · ADR ledger + risk register · TDD-driven agent supervision.

## 15. Governance — Where This Fits

Four artifacts, four jobs: **this document** = destination (read at milestone boundaries; amended only at milestone boundaries or fork resolutions); **CLAUDE.md** = the agent's always-true constitution, derived from §§5–8 and kept short; **issues/** = the backlog, one slice per file; **playbook** = the owner's ritual. On sign-off: archive Scope A and Scope B to `docs/archive/`, place this file at `docs/PROJECT_SCOPE.md`, and derive the CLAUDE.md rewrite from it as the next deliverable.

**Sign-off:** _____________________ (owner) · Date: ____________
