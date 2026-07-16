# Bundesliga Transfer Traits (Cal Berkeley)

**Pipeline:** stability (prior → Bundesliga Y1) → redundancy (Step 2) → scout pizza / explorer → success indicators (Y1 minutes).

## Deliverables

| File | Role |
|------|------|
| [`bundesliga_transfer_traits.pptx`](bundesliga_transfer_traits.pptx) | Deck — method + results |
| [`interactive_player_explorer.html`](interactive_player_explorer.html) | Success summary + player examples |
| [`projectproposal.docx`](projectproposal.docx) | Proposal (Word) |
| [`projectproposal.txt`](projectproposal.txt) | Proposal source (edit here → reconvert to docx) |

## Stability & redundancy CSVs

### StatsBomb (N=60 · gate r≥0.40)

| File | Role |
|------|------|
| [`results/stability_all_metrics.csv`](results/stability_all_metrics.csv) | All metrics tested |
| [`results/stability_passed_r040.csv`](results/stability_passed_r040.csv) | Passed stability gate |
| [`results/redundancy_high_pairs_step2.csv`](results/redundancy_high_pairs_step2.csv) | Near-duplicate pairs |
| [`results/redundancy_auto_shortlist_suggestion.csv`](results/redundancy_auto_shortlist_suggestion.csv) | Auto shortlist suggestion |

### FBref Big 5 (N=117 · gate r≥0.50)

| File | Role |
|------|------|
| [`results/fbref_stability_all_metrics.csv`](results/fbref_stability_all_metrics.csv) | All metrics tested |
| [`results/fbref_stability_passed_r050.csv`](results/fbref_stability_passed_r050.csv) | Passed stability gate |
| [`results/fbref_redundancy_high_pairs_step2.csv`](results/fbref_redundancy_high_pairs_step2.csv) | Near-duplicate pairs |
| [`results/fbref_redundancy_auto_shortlist_suggestion.csv`](results/fbref_redundancy_auto_shortlist_suggestion.csv) | Auto shortlist suggestion |

## Scripts

| Script | What it builds |
|--------|----------------|
| [`run_analysis.py`](run_analysis.py) | StatsBomb stability + redundancy CSVs |
| [`scripts/run_fbref_stability.R`](scripts/run_fbref_stability.R) | FBref stability + redundancy CSVs |
| [`scripts/run_success_indicators.py`](scripts/run_success_indicators.py) | Traits / leagues → Y1 minutes |
| [`scripts/run_feeder_regression.py`](scripts/run_feeder_regression.py) | Feeder-league OLS (why Ligue 1 looks best) |

**Success proxy:** first-season Bundesliga minutes (Y1). Transfermarkt Δ value would be preferred if licensed data were available.

## Headlines

- **StatsBomb:** 11 metrics pass r≥0.40; 3 redundancy pairs; Step-2 shortlist ~9–11 traits
- **FBref:** 61 metrics pass r≥0.50; Step-2 shortlist **26** traits
- **Success:** prior final-third / defensive-box / aerial traits ↔ more Y1 minutes; Ligue 1 leads descriptively on mean Y1 minutes; regression shows league dummies are weak vs trait profile
