# Independent Study Proposal — Cal Berkeley (1 credit)

**Student:** Colby Morris  
**Advisor:** Conrad  
**Date:** July 15, 2026  
**Working title:** Which traits travel into the Bundesliga — and which source leagues should scouts prioritize?  
**Scope:** Bundesliga destination only (narrow one-league inbound study)

---

## Research question

When players transfer **into the 1. Bundesliga** from other leagues, which performance traits remain **stable vs. league-context**, and which **source leagues** produce the most effective arrivals?

Two evidence layers:

| Tier | Role | Data backbone | Headline N |
|------|------|---------------|------------|
| **Tier 1 — Wide** | Outcomes for *all* inbound / first Bundesliga seasons in the study window | **FBref** player-season stats | **≥500** |
| **Tier 2 — Deep** | Trait portability + league ranking | FBref prior → Bundesliga Y1 per-90; **StatsBomb Open Data** as event-level deep dive on a smaller overlap | Open data now ~**100**; FBref target **500+ paired** seasons |

This extends the NYRB scouting-metric framework (stability → redundancy → target), **replacing Transfermarkt market value** with a **Destination Effectiveness Score (DES)** and a traits-to-target / leagues-to-prioritize framing.

---

## Is Transfermarkt “public”?

| What | Reality |
|------|---------|
| **Browsing** | Yes — the site is free to view (transfers, clubs, minutes, values). |
| **Bulk scrape / bots** | **No** — Transfermarkt Terms of Use ban bots, spiders, and screen scraping, and reserve text/data-mining rights. |
| **Official research dump** | Not generally open; they prefer one-off data provision for research requests. |
| **Implication for this project** | Do **not** scrape Transfermarkt. Use **FBref** as the public performance and season source. Use Transfermarkt only via (a) manual spot-checks, (b) Conrad-approved contact/request, or (c) a pre-published dataset if Conrad signs off. |

**FBref** (Sports Reference) is the primary public dataset for Tier 1–2 metrics: viewable online; usable for coursework with attribution and rate-limited access. Respect their terms; do not redistribute raw dumps beyond the course.

---

## Two-tier design (Bundesliga only)

### Tier 1 — Robust FBref sample (headline N ≥ 500)

- **Who:** All players with a first Bundesliga season (or verified inbound transfer season) over a multi-year window (e.g. last 8–12 seasons), with a relaxed minutes filter (e.g. ≥270–450 Bundesliga minutes in Year 1 so N stays ≥500).
- **What:** Outcome metrics only — minutes share; per-90 attacking (shots, xG, progressive passes); defending (tackles, pressures, clearances) by position and **source league**.
- **Why:** Honest large N; answers “who succeeds after arrival?” without needing event data.

### Tier 2 — Portability model (FBref primary; StatsBomb deep dive)

- **Who:** Subset with measurable prior-season club stats in another league on FBref → target **500+** paired player-seasons.
- **What:** Pre-transfer vs Bundesliga Y1 z-scores / percentiles; portability *r* by metric × position; source-league ranking; light redundancy screen.
- **StatsBomb Open Data deep dive:** Same questions on the ~**94–120** players who currently have prior + Bundesliga minutes in open data (richer event taxonomy, interactive pizza profiles). Compare whether event-level conclusions **align** with FBref (validation: deeper but smaller).

**Destination Effectiveness Score (replaces market-value Axis 3):**

DES_i = Σ_m [ w_m × Pctile_Bundes(m)_i ] / Σ_m w_m

where w_m = max(0, r_port(m)) and r_port is the correlation of pre-transfer vs Year-1 z-scores for metric m.

**Outputs:** traits to target (high portability) and leagues to prioritize (high Year-1 minutes / DES among source leagues).

---

## Data stack

1. **FBref** — primary layer for Tier 1 (N≥500 outcomes) and Tier 2 (portability at scale).  
2. **StatsBomb Open Data** — deep dive + interactive pizza explorer on the smaller open-data overlap.  
3. **Transfermarkt** — browse / spot-check only; no scraping.

Open-data stress test already completed: Bundesliga first appearances ≈ **675**; with any prior open-data minutes ≈ **120**; analysis-ready (≥90 prior min) ≈ **94** (CM+FB ≈ **35**). That motivates FBref for scale while keeping StatsBomb for depth.

---

## Deliverables (current package)

| # | File | Description |
|---|------|-------------|
| 1 | `CONRAD_PROPOSAL.docx` | This proposal as a Word document for Conrad |
| 2 | `interactive_player_explorer.html` | Player dropdown sorted by position; StatsBomb-style pizza; DES; stock fonts |
| 3 | `methodology_results_brief.html` | Short 6-section method/results brief (Tier tables, traits, leagues, cases) |
| 4 | `cohort_data.json` / `README.md` | Open-data cohort artifact + package notes |

All live in: `cal-bundesliga-transfer-traits/`

---

## Timeline (≈4–5 weeks)

| Week | Work |
|------|------|
| 1 | FBref Bundesliga cohort freeze (Tier 1 N≥500); document no-scrape policy for Transfermarkt |
| 2 | Tier 1 outcomes by source league + position |
| 3 | Tier 2 FBref portability + DES; begin StatsBomb deep dive |
| 4 | Align FBref vs StatsBomb findings; finalize HTML deliverables |
| 5 | Write-up + Conrad review |

---

## Why this works for 1 credit

- **Honest N:** Tier 1 guarantees ≥500 without claiming open data has 500 paired transfers.  
- **Narrow:** only into the Bundesliga.  
- **Accurate where it matters:** FBref multi-season performance for the robust model; StatsBomb for a smaller, deeper event dive.  
- **Clean ethics:** FBref-first; Transfermarkt not scraped.

Attributions: FBref / Sports Reference; StatsBomb Open Data (where used).
