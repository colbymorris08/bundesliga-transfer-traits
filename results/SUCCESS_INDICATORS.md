# Success indicators — traits & leagues vs Bundesliga Year-1

## Method (Phase 2 · descriptive prediction)

After stability/redundancy, we ask: **which prior traits and feeder leagues line up with BL success?**

**BL success proxies (outcomes):**
- `y1_minutes` — Year-1 Bundesliga minutes (playing-time success)
- `y1_minutes_pct` — percentile of Y1 minutes within inbound cohort
- `stable_trait_score` — mean Y1 percentile on Step-2 shortlist traits

**Trait test:** Spearman ρ between **prior-season trait percentile** (vs BL position peers) and each outcome.

**League test:** Mean/median outcomes by **prior league** (Big 5 for FBref; primary prior comp for StatsBomb).

This is **associative / indicative** — not a validated forecast model. Small-N leagues are directional only.

---

## StatsBomb (N=60)

### Top prior traits → Y1 minutes

| Abbrev | ρ | p | n |
|---|---:|---:|---:|
| DRB | -0.297 | 0.021 | 60 |
| DIS | 0.287 | 0.026 | 60 |
| PRS | -0.286 | 0.026 | 60 |
| PPC | 0.220 | 0.092 | 60 |
| PATT | -0.212 | 0.104 | 60 |
| XG | -0.166 | 0.204 | 60 |
| TAC | -0.101 | 0.443 | 60 |
| CLR | -0.058 | 0.660 | 60 |

### Source leagues → BL success

| League | N | Mean Y1 min | Mean trait score |
|---|---:|---:|---:|
| FIFA World Cup | 22 | 248.6 | 57.27 |
| Premier League | 3 | 146.2 | 53.57 |
| La Liga | 3 | 220.8 | 49.67 |
| Ligue 1 | 16 | 132.8 | 49.53 |
| UEFA Euro | 15 | 203.0 | 49.46 |
| Serie A | 1 | 58.8 | 47.9 |

---

## FBref Big 5 (N=117)

### Top prior traits → Y1 minutes

| Abbrev | Label | ρ | p | n |
|---|---|---:|---:|---:|
| LOST | Lost Aerial | 0.246 | 0.007 | 117 |
| FINAL | Final Third | 0.243 | 0.008 | 117 |
| SH | Sh Blocks | 0.234 | 0.011 | 117 |
| DEFPE | Def Pen Touches | 0.195 | 0.035 | 117 |
| WONPE | Won percent Aerial | 0.173 | 0.062 | 117 |
| PRGDI | PrgDist Total | 0.166 | 0.073 | 117 |
| MIS | Mis Carries | 0.163 | 0.078 | 117 |
| CLR | Clr | 0.130 | 0.162 | 117 |
| RECOV | Recov | 0.127 | 0.173 | 117 |
| TKLPE | Tkl percent Challenges | 0.104 | 0.265 | 117 |

### Source leagues → BL success

| League | N | Mean Y1 min | Median Y1 min | Mean trait score |
|---|---:|---:|---:|---:|
| Ligue 1 | 52 | 1574.3 | 1460.0 | 51.1 |
| Premier League | 30 | 1508.8 | 1390.5 | 50.22 |
| La Liga | 11 | 1479.7 | 1411.0 | 50.6 |
| Serie A | 24 | 1426.3 | 1252.0 | 52.42 |

### Which league is most predictive per trait? (FBref)

Within each Big-5 feeder, Spearman ρ(prior trait percentile → Y1 minutes). **Best league** = highest ρ for that trait.

| Trait | Best league | ρ | p | n |
|---|---|---:|---:|---:|
| MIS — Mis Carries | La Liga | 0.482 | 0.133 | 11 |
| PRGDI — PrgDist Total | La Liga | 0.446 | 0.170 | 11 |
| CMPPE — Cmp percent Medium | La Liga | 0.446 | 0.170 | 11 |
| FINAL — Final Third | La Liga | 0.436 | 0.180 | 11 |
| DEFPE — Def Pen Touches | Ligue 1 | 0.373 | 0.006 | 52 |
| SH — Sh Blocks | Ligue 1 | 0.360 | 0.009 | 52 |
| INT — Int | Serie A | 0.346 | 0.098 | 24 |
| GLS — Gls Standard | Premier League | 0.336 | 0.070 | 30 |
| LOST — Lost Aerial | Premier League | 0.334 | 0.072 | 30 |
| KP — KP | Premier League | 0.332 | 0.073 | 30 |
| RECOV — Recov | Ligue 1 | 0.331 | 0.016 | 52 |
| TKLD — Tkld Take | Ligue 1 | 0.328 | 0.017 | 52 |
| DEF3R — Def 3rd Tackles | Serie A | 0.304 | 0.148 | 24 |
| CLR — Clr | Ligue 1 | 0.289 | 0.038 | 52 |
| WONPE — Won percent Aerial | Premier League | 0.261 | 0.164 | 30 |
