# Political Party Shift Predictor

**PITF-inspired model for forecasting when incumbent parties lose elections.**

Inspired by the CIA's Political Instability Task Force (1994–2018), which predicted state failures using just 4 variables. This model applies the same structural-forecasting philosophy to a different question: **when does a ruling party lose power through elections?**

## Motivation

The original PITF predicted coups, civil wars, and regime collapse. But in the modern era, the more policy-relevant question for diplomats and analysts is: *which elections will produce power transfers?* Predicting party shifts helps:
- Anticipate policy discontinuity in partner countries
- Identify democratic systems under stress
- Understand structural drivers of democratic accountability

## PITF Variables (adapted)

| Original PITF Variable | Our Adaptation |
|---|---|
| Regime type (partial democracy) | Voice/Accountability score + partial democracy indicator |
| Infant mortality | Infant mortality rate from World Bank |
| Conflict-ridden neighborhood | Count of bordering states with major armed conflict |
| State-led discrimination | Control of corruption + governance quality |
| — | GDP growth (economic voting theory) |
| — | Incumbent tenure length (anti-incumbency fatigue) |

## Data Sources

- **World Bank (WDI)**: Infant mortality, GDP growth, GDP per capita, unemployment, inflation
- **Worldwide Governance Indicators**: Voice/accountability, political stability, rule of law
- **Hand-coded turnovers**: 262 executive party shift events across 48 countries (1970–2024)
- **Conflict database**: Major armed conflicts by country-year (coded from UCDP/ACLED)
- **Border adjacency graph**: Land borders for computing neighborhood instability

## Model Architecture

Three-model ensemble (mimicking PITF's later ensemble approach):
1. **Logistic Regression** — interpretable coefficients
2. **Random Forest** — captures nonlinear interactions
3. **Gradient Boosting** — sequential error correction

Evaluation: time-series split (train pre-2010, test 2010+) to prevent data leakage.

## Results

| Model | ROC-AUC | PR-AUC | Brier Score |
|---|---|---|---|
| Logistic Regression | 0.514 | 0.137 | 0.315 |
| Random Forest | **0.726** | **0.341** | 0.219 |
| Gradient Boosting | 0.700 | 0.243 | **0.119** |
| Ensemble | 0.662 | 0.212 | 0.173 |

### Top Predictive Features

1. **Tenure years** — longer incumbents are more likely to lose
2. **Unemployment** — economic pain drives electoral accountability
3. **Infant mortality** — state capacity proxy (PITF-aligned)
4. **GDP growth (lagged)** — voters punish economic decline retrospectively
5. **Population** — larger democracies have more competitive elections
6. **Neighbors in conflict** — regional instability spills over

### Notable Predictions (2024)

The model correctly identified **UK 2024** (Labour victory over Tories) as high-probability shift (0.58). It also flagged India, Hungary, and Turkey as elevated risk — all countries where incumbents faced unusually strong opposition challenges.

## Usage

```bash
pip install -r political_shift_model/requirements.txt
cd political_shift_model
python3 run_model.py
```

Output files land in `political_shift_model/output/`.

## Extensions

To improve this model further:
- Add V-Dem dataset (requires manual download from v-dem.net) for richer regime classification
- Add ACLED event-level data for more precise conflict coding
- Add electoral system variables (PR vs majoritarian affects turnover frequency)
- Implement the full PITF split-population duration model
- Add rolling forecast windows (6-month ahead like later PITF)

## References

- Goldstone et al. (2010). "A Global Model for Forecasting Political Instability." *AJPS* 54(1).
- Ulfelder & Lustik (2007). "Modelling Transitions to and from Democracy." *Democratisation* 14(3).
- Ward et al. (2016). "Lessons from near real-time forecasting of irregular leadership changes." *JPR*.
