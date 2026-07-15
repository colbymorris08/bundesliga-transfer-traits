# Analysis results — Bundesliga inbound traits

**Stability threshold:** r ≥ **0.70**  
**Metrics tested:** 16  
**Metrics that go through (pass 0.70):** **2** — `['dispossessed', 'pass_progressive']`  
**Cohort N:** 60 (StatsBomb Open Data; prior≥90 min, BL Y1≥45 min)

## Methodology discussion (brief)

We treat portability as **cross-league stability**: for each event-derived per-90 metric, Pearson *r* between prior-competition production and Bundesliga Year-1 for the same inbound players. Metrics with *r* ≥ 0.70 “go through.” Among those, we check redundancy (|*r*| ≥ 0.70 pairs); Step 2 is choosing which stable metrics to keep on the scout card. Pizzas plot destination percentiles with a **dotted average-Bundesliga** reference (50th pct) and a top-peer ring so “good” is relative to Germany, not the prior league.

This open-data run used prior≥90 and Y1≥45 minutes (partial-season samples). Low pass count at 0.70 is expected on a small, mixed prior sample (club + internationals); FBref Tier 1/2 is meant to re-estimate the same pipeline at larger N.

## Step 2 — redundancy selection (your call)

Among the **2** metrics that cleared stability:

- High-redundancy pairs (|r|≥0.70): **0** (see `redundancy_high_pairs_step2.csv`)
- **Default / recommendation:** push **both** `dispossessed` and `pass_progressive` through to the pizza scout card
- Optional: drop one if you want a shorter card

Pizzas currently show the **top 8 metrics by stability** for readability, with a green **PASS** badge on the two that met 0.70.  
**Dotted navy ring = average Bundesliga peer (50th percentile).** Solid gray = top peer (~90th).

## Top targets (ranked on the 2 passed metrics only)

| Rank | Player | Pos | Score | Source |
|---:|---|---|---:|---|
| 1 | Eric Dier | Central Defender | 100.0 | Premier League |
| 2 | Alexander Nübel | Goalkeeper | 99.55 | Ligue 1 |
| 3 | Gregor Kobel | Goalkeeper | 98.64 | FIFA World Cup |
| 4 | Josip Juranović | Full Back | 95.82 | FIFA World Cup |
| 5 | Dayotchanculle Upamecano | Central Defender | 94.27 | FIFA World Cup |
| 6 | Przemysław Tytoń | Goalkeeper | 93.55 | La Liga |
| 7 | Kevin Trapp | Goalkeeper | 93.27 | Ligue 1 |
| 8 | Min Jae Kim | Central Defender | 87.55 | FIFA World Cup |
| 9 | Jonas Omlin | Goalkeeper | 86.73 | Ligue 1 |
| 10 | Nico Schlotterbeck | Central Defender | 83.45 | FIFA World Cup |
| 11 | Emiliano Adrián Insúa Zapata | Full Back | 81.27 | La Liga |
| 12 | Junior Castello Lukeba | Central Defender | 80.27 | Ligue 1 |
| 13 | Ko Itakura | Central Defender | 79.73 | FIFA World Cup |
| 14 | Piero Martín Hincapié Reyna | Central Defender | 79.55 | FIFA World Cup |
| 15 | Willi Orban | Central Defender | 79.36 | UEFA Euro |
