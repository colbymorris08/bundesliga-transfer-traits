# Bundesliga Transfer Traits (Cal Berkeley)

**Pipeline:** stability (prior league → Bundesliga Y1) → redundancy (Step 2) → pizza charts.

## Latest run (StatsBomb Open Data)

| Item | Value |
|------|------:|
| Cohort N | **60** |
| Metrics tested | **16** |
| **Passed stability r≥0.70** | **2** (`dispossessed`, `pass_progressive`) |
| Redundancy pairs among passed | **0** → Step 2 default: push **both** |

See [`results/RESULTS.md`](results/RESULTS.md) and [`results/results_dashboard.html`](results/results_dashboard.html).

## Files

| File | Description |
|------|-------------|
| [`projectproposal.txt`](projectproposal.txt) | Editable proposal source |
| [`projectproposal.docx`](projectproposal.docx) | Word proposal |
| [`interactive_player_explorer.html`](interactive_player_explorer.html) | Pizzas · **dotted avg Bundesliga** · ranked targets |
| [`results/`](results/) | CSVs, rankings, stability, redundancy for Step 2 |
| [`bundesliga_statsbomb_deck.pptx`](bundesliga_statsbomb_deck.pptx) | **StatsBomb mock deck** (from RBNY general PPT layout) |
| [`bundesliga_transfer_traits.pptx`](bundesliga_transfer_traits.pptx) | Same deck (alias) |
| [`mock_pizza_bundesliga.png`](mock_pizza_bundesliga.png) | Mock/static pizza image |

## Step 2 (your pick)

1. Open `results/stability_passed_r070.csv` — metrics that cleared **0.70**
2. Open `results/redundancy_high_pairs_step2.csv` — conflicting pairs (currently none)
3. Choose which passed metrics go on the final scout card / pizza

Inbound IDs come from FBref-style season logic on open data (first Bundesliga season + prior elsewhere), not Transfermarkt scraping.
