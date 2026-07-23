# Open Questions Board — Loose Ends Until Lock

**Purpose.** Every worry, idea, or question gets triaged here within 60 seconds of appearing — then it lives in exactly one place and stops occupying your head. This board is reviewed once per session, at session open (Phase 1 of the routine). It is the *intake valve* for the four-artifact system, not a fifth artifact: items drain out of it into the scope, the issues board, the ledger, or the learning map.

**The five routes (every item takes exactly one):**

1. **SETTLED** — already answered in the scope. Action: reread the cited section; optionally one ledger line. Re-opening a settled fork requires its revisit trigger firing, not anxiety.
2. **FORK** — a genuine road divergence. Action: add or amend §10 of PROJECT_SCOPE at sign-off or a milestone boundary.
3. **DESIGN (phase-local)** — real question that belongs to a specific phase's grill session. Action: file an issue tagged to that phase; forget it until then.
4. **LEARNING** — a knowledge gap. Action: it's already in the §11 learning map or gets added; learn it in the AFK block of the phase that needs it.
5. **IDEA (V2 / Phase 3)** — expansion thinking. Action: one line on the issues board as a Phase-3 note; never touches V1.

**The blocking rule.** An item blocks building only if it blocks the *current* phase. The board must reach zero **blocking** items before Phase 0 — not zero items. A long non-blocking list is healthy; it means ideas are parked, not lost.

---

## The board (2026-07-11)

| # | Item | Route | Disposition | Blocking? | Due |
|---|---|---|---|---|---|
| Q1 | Session infrastructure: CLAUDE.md v2, /grill-me, /new-slice, session start/end rituals, ledger format, drift control | DESIGN | Next session's deliverable set — already scheduled. Start/end rituals = the approved six-phase routine written into the playbook checklist first; they become skill files only if friction appears | **YES — blocks Phase 0** | Session 2 |
| Q2 | Why no scrapers? What about social-platform announcements? | SETTLED | Scope §3 + §8: API-keyed boards only. DOM scraping = rate limits, CAPTCHAs, legal exposure, volatility — you buy structure via API instead of fighting the DOM. Social sources are out of scope V1; `source_type` already keeps that door open. V2 idea → issues board | No | — |
| Q3 | Are profiles A/B/C complete? Missing near-purchase signals? | DESIGN | Grill topic for Phase 4. Profiles are *config* (`profiles.py`), not architecture — adding a Profile D later is cheap. Review them against **real postings from the M2 live pass**, not from the armchair | No | Phase 4 grill |
| Q4 | Geography: US only, or other countries/regions? | FORK | **New fork F10**, scope bumped to v1.2. Default: US-only V1 (Adzuna API is per-country; spaCy `en` pipeline; owner's compliance context is CAN-SPAM/US). Generalize after the loop is proven | No — default chosen; confirm at sign-off | Sign-off |
| Q5 | Tools to pre-learn (LangGraph, AWS, …)? | SETTLED + LEARNING | No tool enters the stack for resume reasons. The stack is the story (§11); defensible "why NOT X" answers are ledger entries and interview gold. Only pre-learn: git basics + pytest basics (used from session one) | No | AFK blocks |
| Q6 | Unsupervised ML instead of rule-based scoring? | SETTLED | F3 stands. Clustering yields groupings, not intent — a human still has to name the clusters, which is exactly what profiles do explicitly and with controllable precision. Ledger note: embedding-similarity scoring is a legitimate F3 midpoint once the rules baseline and labels exist | No | F3 trigger |
| Q7 | LLM drafts must be personalized to company, person, and product | SETTLED + DESIGN | Already the design: the drafter payload carries `company_name`, the actual `matched_keywords` from *their* posting, `matched_profile` → product, and the contact's name/title (F8). Depth of personalization = prompt engineering, Phase 7 grill topic | No | Phase 7 grill |
| Q8 | **F1 dedup key decision** | FORK (open) | Recommendation is written in §10. Owner answers yes / no / modify — one line | **YES — blocks Phase 2** | Today |
| Q9 | De-risk spike: Adzuna account + one real JSON saved as fixture | DESIGN | 60–90 min, non-coding. Also confirms the F2 fallback landscape | **YES — soft-blocks Phase 3** | This week |
| Q10 | Learn basics first, or build first? | SETTLED | Build first; learn anchored in AFK blocks (§2 objective 3, §11). Concrete code cures abstract overwhelm | No | — |

---

**How to add to this board:** append a row, assign one route, move on. If you catch yourself thinking about an item outside its due phase, that is drift — the board's whole job is to let you *stop* thinking about parked items.
