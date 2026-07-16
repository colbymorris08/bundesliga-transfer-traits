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

See [`results/FBREF_RESULTS.md`](results/FBREF_RESULTS.md).

## Files

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
