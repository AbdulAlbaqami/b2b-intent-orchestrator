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
- Why / tradeoff: §10 F4 records the decision and its revisit conditions but states no
  explicit positive rationale — TODO (flagged). The tradeoff is legible from the revisit
  trigger: SQLite is sufficient while the system is a single-writer, single-node, single-tenant
  batch job; the move to Postgres is justified only when that stops being true. The repository
  boundary means the engine swap is contained.
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
