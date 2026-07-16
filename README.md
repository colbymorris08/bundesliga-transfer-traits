# Bundesliga Transfer Traits (Cal Berkeley)

**Pipeline:** stability (prior league → Bundesliga Y1) → redundancy (Step 2) → pizza charts.

## Latest run (StatsBomb Open Data)

| Item | Value |
|------|------:|
| Cohort N | **60** (prior ≥90 min · BL Y1 ≥45 min) |
| Metrics tested | **16** |
| **Passed stability r≥0.40** | **11** |
| Also pass strict r≥0.70 | **2** (`dispossessed`, `pass_progressive`) |
| Redundancy pairs among passers (\|r\|≥0.70) | **3** |
| Auto shortlist | **9** metrics |

See [`results/RESULTS.md`](results/RESULTS.md) and [`results/results_dashboard.html`](results/results_dashboard.html).

**FBref** is the planned scale layer (Tier 1 N≥500). The HTML explorer has a **Data source** dropdown (StatsBomb live · FBref planned).

## Latest run (FBref Big 5)

| Item | Value |
|------|------:|
| Paired inbound N | **117** |
| Metrics tested | **103** |
| Passed stability r≥0.40 | **71** |
| Passed r≥0.70 | **35** |
| Redundancy pairs | **217** |
| Auto shortlist | **22** |

See [`results/FBREF_RESULTS.md`](results/FBREF_RESULTS.md). Step-2 shortlist: **26** traits (`decisions/step2_fbref.json`).

## Success indicators (traits & leagues → BL Year-1)

Phase 2 asks which **prior traits** and **feeder leagues** associate with BL success (Y1 minutes + stable-trait score).

| Test | Method |
|------|--------|
| Traits | Spearman ρ: prior-season trait percentile → Y1 outcome |
| Leagues | Mean/median Y1 minutes & trait score by prior league |

See [`results/SUCCESS_INDICATORS.md`](results/SUCCESS_INDICATORS.md) · run with `python3 scripts/run_success_indicators.py`

**FBref (N=117):** prior final-third passing, defensive box touches, blocks, aerials ↔ more Y1 minutes. **Leagues:** Ligue 1 highest mean Y1 minutes; all Big 5 feeders viable.

**StatsBomb (N=60):** directional trait signals; league cells mostly intl comps (small N).

## Feeder regression (next phase — explain “best feeder”)

Descriptive league means are not enough. OLS on **Y1 minutes** (FBref N=117) estimates each Big-5 feeder vs **Serie A** (reference), controlling for prior minutes, position, and prior trait percentiles.

| Model | What it tests |
|-------|----------------|
| M1 | League dummies → Y1 minutes |
| M3 | League + prior trait percentiles (mediation) |
| M4 | 80/20 holdout check (exploratory) |

See [`results/FEEDER_REGRESSION.md`](results/FEEDER_REGRESSION.md) · run with `python3 scripts/run_feeder_regression.py`

**Headline:** Ligue 1 leads descriptively (+163 min vs Serie A in M1) but league dummies are **not significant** at this N; **Lost Aerial** prior pct is (p≈0.002). Trait profile explains more variance than league label (R² 0.09 → 0.22). Still **not** a validated BL performance forecast.

| File | Description |
|------|-------------|
| [`projectproposal.txt`](projectproposal.txt) | Editable proposal source |
| [`projectproposal.docx`](projectproposal.docx) | Word proposal |
| [`interactive_player_explorer.html`](interactive_player_explorer.html) | **FBref \| StatsBomb** · league · pizzas |
| [`results/`](results/) | CSVs, rankings, stability, redundancy for Step 2 |
| [`bundesliga_transfer_traits.pptx`](bundesliga_transfer_traits.pptx) | **Only deck** — methodology + FBref vs StatsBomb |
| [`mock_pizza_dier_nyrb_style.png`](mock_pizza_dier_nyrb_style.png) | Eric Dier pizza (NYRB wedge style) |
| [`mock_pizza_bundesliga.png`](mock_pizza_bundesliga.png) | Original matplotlib mock (kept) |

## Step 2 (your pick)

1. Open `results/stability_passed_r040.csv` — metrics that cleared **0.40**
2. Open `results/redundancy_high_pairs_step2.csv` — conflicting pairs (**3**)
3. Choose which passed metrics go on the final scout card / pizza

Inbound IDs come from first-Bundesliga season logic on open data (prior elsewhere), not Transfermarkt scraping.
