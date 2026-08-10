# Bundesliga Transfer Traits (Cal Berkeley)

**Pipeline:** consistency check (prior season → first Bundesliga season) → drop near-duplicates → category radar charts / explorer → success tests (first-season Bundesliga minutes).

**Destination:** the **Bundesliga** only (Germany’s top men’s soccer league).  
**Football Reference** = larger sample, season-rate metrics. **StatsBomb** open data = smaller sample, deeper event metrics.

## Deliverables (submit)

| File | Role |
|------|------|
| [`bundesliga_transfer_traits.pptx`](bundesliga_transfer_traits.pptx) | Deck — method + final results + conclusion |
| [`interactive_player_explorer.html`](interactive_player_explorer.html) | Success summary + player radar charts (Football Reference ↔ StatsBomb) |
| [`stability_redundancy_inspector.html`](stability_redundancy_inspector.html) | Consistency floors & near-duplicate cuts by category |
| [`projectproposal.docx`](projectproposal.docx) | Proposal (Word) |
| [`projectproposal.txt`](projectproposal.txt) | Proposal source |

## Final sample & shortlists

| Layer | N | Consistency floor | Near-duplicate filter | Shortlist |
|-------|--:|-------------------|----------------------|----------:|
| **Football Reference** | **329** pairs · **19** leagues · **105→43→32** | Attacking / Passing / Other ≥0.60 · Defending / Carrying ≥0.50 → **43** | \|r\|≥0.95 | **32** |
| **StatsBomb** | **96** · **17** competitions | r≥0.40 | \|r\|≥0.85 (all kept) | **7** |

- Football Reference window: first Bundesliga season end-years **2021–2025**; minutes floor prior / first Bundesliga season ≥**300′** (N=329 is after that gate)
- StatsBomb: men’s open competitions as priors; Bundesliga open match files **2015/16 + 2023/24**; prior ≥**45′** · first Bundesliga season ≥**30′**
- Success measure: **minutes in the first Bundesliga season** (not Transfermarkt market value)
- League-relative scaling tested on Football Reference — **did not help** prior→first-season consistency; not applied

## Local results (not in git)

Regenerable under `results/` (gitignored): consistency / near-duplicate CSVs, success indicators, caches.  
Headline numbers and prior-league regression tables are in this README. **Interactive results** (success tables, radars, gates) live in the explorer + inspector HTML — download either `.html` file and open it in a browser (fully self-contained; no server or install needed).

## Exploratory prior-league regression (Phase 2b)

Big Five European leagues subset on Football Reference (**N = 117**): Premier League, La Liga, Serie A, Ligue 1 (plus Bundesliga as destination). Outcome = first-season Bundesliga minutes. Reference league = **Serie A**. Associative / exploratory — not a validated forecast.

**Model 1** · `first_season_minutes ~ prior_league + prior_minutes + position` · R² = 0.086  
**Model 2** · Model 1 + prior trait percentiles · R² = 0.215  
**Model 3** · 80/20 holdout correlation(predicted, actual) = 0.35

### League effects (Model 1 · change in first-season Bundesliga minutes vs Serie A)

| League | Change in first-season minutes | p |
|--------|--------:|--:|
| La Liga | +48 | 0.856 |
| Ligue 1 | +163 | 0.375 |
| Premier League | +88 | 0.661 |

None significant at p &lt; 0.05 — league gaps shrink to noise once minutes and position are held.

### Prior trait effects (Model 2 · controlling for league)

| Trait percentile | Change in first-season minutes | p |
|------------|--------:|--:|
| Aerials lost (fewer is better)* | +9 | 0.002 |
| Passes into the final third | +5 | 0.158 |
| Defensive penalty-area touches | +5 | 0.189 |
| Progressive carry distance | −4 | 0.249 |
| Expected goals (xG) | +2 | 0.430 |
| Shot blocks | +2 | 0.565 |

\* p &lt; 0.05. Takeaway: **the player’s prior trait profile matters more than the prior-league label** in this open-data subset.

## Rebuild (optional)

```bash
python3 scripts/finalize_deliverables.py   # explorer + success p-values from final shortlists
python3 scripts/run_success_indicators.py  # Phase-2 Spearman only
```
