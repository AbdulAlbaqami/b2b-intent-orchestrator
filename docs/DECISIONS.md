# Decision Ledger (ADRs)

**Append-only.** Never edit or delete a past entry. One entry per decision, in
chronological order, numbered ADR-00N. If a decision changes, add a **new** entry that
supersedes the old one and reference it (`Supersedes ADR-00X` / `Superseded by ADR-00Y`) —
the old entry stays untouched as the historical record.

Entries are sourced from `PROJECT_SCOPE.md` §10 (Road Divergence Map / decision forks);
interview lines from §11 and §14. Rationale is taken from the scope, not invented — a field
the scope does not support is marked `TODO`.

Entry format:

    ### ADR-00N — <short title>
    - Date:
    - Decision:
    - Alternatives rejected:
    - Why / tradeoff:
    - Revisit trigger:
    - Interview line:

---

### ADR-001 — Storage engine: SQLite (fork F4)
- Date: 2026-07-11 (recorded "Decided" in PROJECT_SCOPE v1.2 §10)
- Decision: Use SQLite as the V1 storage engine (L3), fronted by a repository that hides SQL
  behind a narrow API and owns all state transitions.
- Alternatives rejected: Postgres (deferred, not abandoned — the fork keeps the door open).
- Why / tradeoff: Single-user, single-writer workload with no deployment target in V1. SQLite
  is zero-config, ships with Python, and makes the repository pattern's test story trivial (a
  temp DB file per test). The cost — one writer at a time, no network access, weaker typing — is
  invisible at this scale and becomes blocking only at concurrent writers or a hosted deployment,
  which is exactly the F4 revisit trigger. Postgres now buys nothing and adds setup, ops, and a
  container dependency.
- Revisit trigger: Concurrent writers, deployment, or multi-tenant (§10 F4).
- Interview line: "Illegal states are unrepresentable — a lead cannot double-process, and I
  can say exactly what would force Postgres." (§11, Phase 5)

### ADR-002 — Scoring method: rule-based, not ML (fork F3)
- Date: 2026-07-11 (recorded "Decided" in PROJECT_SCOPE v1.2 §10)
- Decision: Score leads with rules — spaCy PhraseMatcher plus firmographic rules (L2, pure,
  no I/O) — rather than a trained model.
- Alternatives rejected: weighted rules and a trained model — both deferred along the stated
  progression (rules → weighted rules → trained model).
- Why / tradeoff: Per §10 F3, "rules generate the labels a future model trains on" — you
  cannot train a model with zero labeled outcomes, so rules bootstrap the label set the model
  would later need. Precision is favored over recall because every false positive burns an
  enrichment credit and one of five daily email slots.
- Revisit trigger: ~100+ labeled outcomes exist (§10 F3).
- Interview line: "Precision outweighs recall here: every false positive burns an enrichment
  credit and one of five daily email slots — a cost-weighted threshold." (§11, Phase 4)

### ADR-003 — Enrichment: provider interface + mock through V1 (fork F2)
- Date: 2026-07-11 (pricing wall found; recorded in PROJECT_SCOPE v1.2 §10/§12)
- Decision: Ship L2.5 as an `EnrichmentProvider` ABC with a mock implementation for all of
  V1; threshold-gated and cache-first (misses cached too). Status in scope: **spike pending**
  for the real provider — this ADR fixes the V1 default, not the eventual vendor.
- Alternatives rejected: (b) an alternative free-tier provider such as Hunter — pending a
  spike; (c) paying for Apollo's Organization plan now.
- Why / tradeoff: Apollo's API is gated behind an Organization plan (~$119/user/mo, 3-seat
  minimum); the free tier is ~100 credits and its ToS forbids powering external products with
  its data. Because L2.5 is an interface, the pricing wall is absorbed without redesign, and a
  mock-only V1 loses zero portfolio value — the pattern (gating, caching, cost control) is the
  asset, not the vendor.
- Revisit trigger: Spike results; budget decision (§10 F2).
- Interview line: "When my enrichment vendor's pricing changed mid-project, the swap cost one
  file, because the boundary was mine and the vendor was replaceable." (§14)

### ADR-004 — Cost-control thresholds are code, not configuration (Hard Rules 2 & 3)
- Date: 2026-08-16
- Decision: The enrichment gate (`intent_score > 0.85`, Hard Rule 2) and the daily email cap
  (5/day, Hard Rule 3) are defined as constants in code — a future `config.py`, given the same
  treatment as the `opportunity_score` extension point — not as `.env` variables. Removed
  `ENRICHMENT_SCORE_THRESHOLD` and `DAILY_EMAIL_LIMIT` from `.env.example`.
- Alternatives rejected: sourcing them from `.env` (as the Phase-0 scaffold initially did).
- Why / tradeoff: These values are contract, not environment. In `.env`, a typo silently
  disables a business rule the test suite is meant to guarantee, and the Phase 6 exit criterion
  "the gate provably blocks <0.85" becomes true only in the one environment it was run in.
  `DRY_RUN`, `DATABASE_PATH`, and secrets are genuine deployment settings and stay in `.env`;
  contract thresholds do not. Cost of the change: one constant plus a comment marking the
  firmographic-weighting extension point.
- Revisit trigger: A real need to tune a threshold per-deployment without a code change (e.g.
  multi-tenant / Phase 3) — at which point it becomes validated configuration, not a bare env var.
- Interview line: "Cost-control thresholds are code, not configuration — they're contract, so a
  typo can't silently disable a business rule my tests are supposed to guarantee."
- Next-session instruction: when `config.py` is created (L2.5 / L4 slices), add
  `ENRICHMENT_SCORE_THRESHOLD = 0.85` and `DAILY_EMAIL_LIMIT = 5` as constants, and reconcile
  the `enrichment/apollo.py` and `orchestrator/drafter.py` stub docstrings that currently name
  them as env vars.

### ADR-005 — Dedup key strategy (fork F1)
- Date: 2026-08-16
- Decision: Two-level dedup. `source_url` UNIQUE on RawRecord (ingestion idempotency);
  normalized `hash(company_name + job_title)` on ScoredLead (cross-board duplicate leads).
  Requires adding a `job_title` field to RawRecord. Resolves fork F1 as (a)+(b).
- Alternatives rejected: `source_url` only (misses the same role posted to two boards under
  different URLs); full-payload hash (brittle — any wording or whitespace change defeats it).
- Why / tradeoff: Two levels solve two different problems at two layers. Normalization
  (lowercase, strip punctuation and legal suffixes like Inc./LLC, collapse whitespace) stops
  "TechFlow Logistics, Inc." and "techflow logistics" splitting into two leads. Cost:
  normalization rules need maintenance as edge cases surface. Frequency capping (don't email one
  company twice this week) is deliberately NOT folded into a hash — it is a queue rule at the
  orchestrator (Phase 7), needing no schema field.
- Revisit trigger: First real duplicate that slips through (per §10 F1).
- Interview line: "Dedup is three questions at three layers — ingestion idempotency, cross-board
  lead identity, and outreach frequency. I solved the first two with a URL-unique raw key and a
  normalized company+title hash, and deliberately did NOT conflate the third into a hash — that's
  a queue rule at the orchestrator, needing no schema field."

### ADR-006 — Context hygiene: clear, never compact
- Date: 2026-08-16
- Decision: Between slices, `/clear` and reload state from disk; never `/compact`.
- Alternatives rejected: `/compact` to preserve context across a long session.
- Why / tradeoff: Compaction summarizes a confused context instead of resetting it — a confused
  large context becomes a confused small summary, which is the post-compaction-hallucination
  failure. The urge to compact mid-slice signals the slice is too big; split it instead.
- Revisit trigger: None.
- Interview line: "I treated context like Memento — clean resets over summarized drift — and
  sized work to fit one clean context."

### ADR-007 — Version control as a human checkpoint
- **Superseded by ADR-009 (2026-09-19).**
- Date: 2026-08-16
- Decision: The agent never runs git write commands; the owner performs all version control
  after reviewing each session's diff.
- Alternatives rejected: Agent auto-commits per slice.
- Why / tradeoff: Keeps a human review gate between agent output and recorded history — the
  commit is the QA checkpoint. Small, labeled, one-slice commits are the owner's, deliberately.
- Revisit trigger: None for V1.
- Interview line: "I ran the agent as implementer but kept version control as a human
  checkpoint — every commit is a reviewed diff."

### ADR-008 — Repository / package naming
- Date: 2026-08-16
- Decision: GitHub repo = `b2b-intent-orchestrator` (private). Python package = `intent_pipeline`
  (unchanged). Local dev folder to be renamed to `b2b-intent-orchestrator` by the owner.
  PROJECT_SCOPE.md §Repo header and §15 are amended to the new repo name in this session.
- Alternatives rejected: Naming the repo after the HubSpot/affiliate vertical.
- Why / tradeoff: The repo name reflects the architecture (an orchestrator, not just a pipeline)
  and the B2B domain, without binding to a replaceable vertical. Package left as `intent_pipeline`
  because renaming a package touches imports, the editable install, and pyproject for cosmetic
  gain. Repo name ≠ package name is normal and fine.
- Revisit trigger: None for V1.
- Interview line: "Named the engine, not the campaign — the repo describes the system, not the
  current affiliate target."

### ADR-009 — Version control delegated to the agent (supersedes ADR-007)
- Date: 2026-09-19
- Decision: The agent may run git writes — stage, commit, and push — on the owner's behalf,
  normally at `/session-close`. Guardrails: stage **explicit paths** (never `git add -A`);
  one slice = one labeled commit; never force-push; never rewrite pushed history (no amend or
  rebase of pushed commits); never stage `.env` or any secret. Destructive git
  (`reset --hard`, `clean -fd`, branch deletion, history rewrite) still asks the owner first.
- Supersedes: ADR-007 (version control as a human checkpoint).
- Alternatives rejected: Keeping the ADR-007 print-the-commands gate — it became the project's
  actual bottleneck; retaining it with a "but commit promptly" promise would not have fixed the
  failure mode, which was owner availability, not owner intent.
- Why / tradeoff: The review gate moves from *before* the commit to *after* it — git history is
  the review surface, and small one-slice commits keep every change cheaply revertible. Evidence
  for the change: a complete infrastructure-freeze session sat uncommitted for over a month
  (2026-08-16 → 2026-09-19) because recording history depended on a human keystroke, so the
  ledger, the scope amendment, and the session baton were all unversioned and at risk the whole
  time. Cost: a bad commit can now land unreviewed; mitigated by slice sizing, explicit-path
  staging, a private solo `main` where `git revert` is cheap, and the no-force-push rule that
  keeps history recoverable.
- Revisit trigger: A second contributor joins, the repo goes public, or a bad agent commit
  reaches a shared branch.
- Interview line: "I delegated version control to the agent only after the human gate proved to
  be the bottleneck — a whole session's work sat unversioned for a month. I bought the safety
  back structurally: slice-sized commits, explicit path staging, and no force-push, so every
  change stays revertible."
