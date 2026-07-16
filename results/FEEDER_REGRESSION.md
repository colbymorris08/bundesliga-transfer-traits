# Feeder league regression — why some leagues look “best”

## Next phase (this analysis)

Descriptive “best feeder” rankings are not enough — we run **OLS regression** to estimate
how much each Big-5 league adds on BL outcomes vs **Serie A** (reference), controlling for
prior minutes and (where available) position and prior trait percentiles.

This is the bridge to full prediction: same features could enter train/test ML later.

**Headline:** League differences modest after controls.

---

## M1 · Y1 minutes ~ feeder league + controls

- R² = 0.086 · adj R² = 0.027 · n = 117

| League (vs Serie A) | Δ Y1 minutes | p |
|---|---:|---:|
| La Liga | +48 | 0.856 |
| Ligue 1 | +163 | 0.375 |
| Premier League | +88 | 0.661 |

Positive = more Year-1 minutes than Serie A arrivals, holding prior minutes & position.

## M2 · Stable-trait score ~ feeder league

- R² = 0.090 · adj R² = 0.058

## M3 · Do prior traits explain the league gap?

- R² = 0.215 · adj R² = 0.141

Key prior trait coefficients (standardized direction):

| Prior trait pct | Δ Y1 minutes | p |
|---|---:|---:|
| Final Third | +5 | 0.158 |
| Def Pen Touches | +5 | 0.189 |
| Lost Aerial | +9 | 0.002 |
| Sh Blocks | +2 | 0.565 |
| PrgDist Total | -4 | 0.249 |
| xG Per | +2 | 0.430 |
| minutes | +0 | 0.036 |

If league dummy coefficients **shrink** from M1 → M3, those traits partially mediate feeder-league differences.

## M4 · Holdout check (exploratory)

- 80/20 split · holdout correlation(pred, actual Y1 minutes) = **0.355**

Not a validated forecast — shows feasibility of Phase-3 ML.
