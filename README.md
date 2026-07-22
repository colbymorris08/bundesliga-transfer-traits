# Bundesliga Transfer Traits (Cal Berkeley)

**Pipeline:** stability (prior → Bundesliga Year 1 in Bundesliga) → redundancy → scout pizza / explorer → success indicators (Year 1 in Bundesliga minutes).

**Destination:** **1. Bundesliga** only. **FBref** = scale · **StatsBomb** open data = event deep dive.

## Deliverables (submit)

| File | Role |
|------|------|
| [`bundesliga_transfer_traits.pptx`](bundesliga_transfer_traits.pptx) | Deck — method + final results + conclusion |
| [`interactive_player_explorer.html`](interactive_player_explorer.html) | Success summary + player radars (FBref ↔ StatsBomb) |
| [`stability_redundancy_inspector.html`](stability_redundancy_inspector.html) | Metric gates & redundancy by category |
| [`projectproposal.docx`](projectproposal.docx) | Proposal (Word) |
| [`projectproposal.txt`](projectproposal.txt) | Proposal source |

## Final sample & shortlists

| Layer | N | Stability | Redundancy | Shortlist |
|-------|--:|-----------|------------|----------:|
| **FBref** | **329** pairs · **19** leagues · **105→43→32** | Att/Pass/Other ≥0.60 · Def/Carry ≥0.50 → **43** | \|r\|≥0.95 | **32** |
| **StatsBomb** | **96** · **17** competitions | r≥0.40 | \|r\|≥0.85 (passes kept) | **7** |

- FBref window: first BL season end-years **2021–2025**; **minutes restriction** prior / Year 1 in Bundesliga ≥**300′** (N=329 is after that gate)
- StatsBomb: all male open comps as priors; BL open dumps **2015/16 + 2023/24**; prior ≥**45′** · Year 1 in Bundesliga ≥**30′**
- Success proxy: **Year 1 in Bundesliga minutes** (not Transfermarkt value)
- League-relative scaling tested on FBref — **did not help** rate→Year 1 in Bundesliga stability; not applied

## Local results (not in git)

Regenerable under `results/` (gitignored): stability/redundancy CSVs, success indicators, caches.
Headline numbers and feeder-regression tables are in this README. **Interactive results** (success tables, radars, gates) live in the explorer + inspector HTML — download either `.html` file and open it in a browser (fully self-contained; no server or install needed).

## Exploratory feeder regression (Phase 2b)

Big-5 FBref subset (**N = 117**). Outcome = Year 1 in Bundesliga minutes. Reference league = **Serie A**. Associative / exploratory — not a validated forecast.

**M1** · `y1_minutes ~ league + prior_minutes + position` · R² = 0.086  
**M3** · M1 + prior trait percentiles · R² = 0.215  
**M4** · 80/20 holdout correlation(pred, actual) = 0.35

### League effects (M1 · Δ Year 1 in Bundesliga minutes vs Serie A)

| League | Δ Year 1 in Bundesliga min | p |
|--------|--------:|--:|
| La Liga | +48 | 0.856 |
| Ligue 1 | +163 | 0.375 |
| Premier League | +88 | 0.661 |

None significant at p &lt; 0.05 — league gaps shrink to noise once minutes and position are held.

### Prior trait effects (M3 · controlling for league)

| Trait %ile | Δ Year 1 in Bundesliga min | p |
|------------|--------:|--:|
| Lost Aerial* | +9 | 0.002 |
| Final Third | +5 | 0.158 |
| Def Pen Touches | +5 | 0.189 |
| PrgDist Total | −4 | 0.249 |
| xG Per | +2 | 0.430 |
| Sh Blocks | +2 | 0.565 |

\* p &lt; 0.05. Takeaway: **trait profile matters more than league label** in this open-data subset.

## Rebuild (optional)

```bash
python3 scripts/finalize_deliverables.py   # explorer + success p-values from final shortlists
python3 scripts/run_success_indicators.py  # Phase-2 Spearman only
```
