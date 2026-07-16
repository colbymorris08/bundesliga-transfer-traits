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

### FBref Big 5 (N=137 · gate r≥0.50 · minutes ≥300)

| File | Role |
|------|------|
| [`results/fbref_stability_all_metrics.csv`](results/fbref_stability_all_metrics.csv) | All metrics tested |
| [`results/fbref_stability_passed_r050.csv`](results/fbref_stability_passed_r050.csv) | Passed stability gate |
| [`results/fbref_redundancy_high_pairs_step2.csv`](results/fbref_redundancy_high_pairs_step2.csv) | Near-duplicate pairs |
| [`results/fbref_redundancy_auto_shortlist_suggestion.csv`](results/fbref_redundancy_auto_shortlist_suggestion.csv) | Auto shortlist suggestion |

## Primary success (powered design)

| File | Role |
|------|------|
| [`results/primary_success_traits.csv`](results/primary_success_traits.csv) | 5 pre-specified traits → Y1 minutes + BH FDR |
| [`results/PRIMARY_SUCCESS.md`](results/PRIMARY_SUCCESS.md) | Write-up |

**Design:** overall cohort only (no league×trait grid) · 5 traits · Benjamini–Hochberg FDR · N=137 from Big‑5 cache (minute gate 300 — no extra scrapes).

**Result:** all 5 FDR-significant (Final Third, Lost Aerial inverted, Aerial win %, Def Pen touches, Shot Blocks).

## Scripts

| Script | What it builds |
|--------|----------------|
| [`run_analysis.py`](run_analysis.py) | StatsBomb stability + redundancy CSVs |
| [`scripts/run_fbref_stability.R`](scripts/run_fbref_stability.R) | FBref stability + redundancy + primary panel |
| [`scripts/run_primary_success.py`](scripts/run_primary_success.py) | Primary traits → Y1 minutes (FDR) |
| [`scripts/run_success_indicators.py`](scripts/run_success_indicators.py) | Broader trait/league descriptives |
| [`scripts/run_feeder_regression.py`](scripts/run_feeder_regression.py) | Feeder-league OLS |
| [`scripts/run_feeder_expand_safe.py`](scripts/run_feeder_expand_safe.py) | Optional: 3 extra feeders, sequential, cached |

**Success proxy:** first-season Bundesliga minutes (Y1). Transfermarkt Δ value would be preferred if licensed data were available.
