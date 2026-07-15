# Analysis results — Bundesliga inbound traits (StatsBomb)

**Stability threshold:** r ≥ **0.4**  
**Metrics tested:** 16  
**Metrics that go through:** **11**  
**Redundancy pairs among passers (|r|≥0.7):** **3**  
**Auto shortlist (suggestion):** `['dispossessed', 'pass_progressive', 'pressures', 'tackles', 'clearances', 'xg', 'dribbles_completed', 'passes_into_final_third', 'carries']`  
**Cohort N:** 60

## Metrics that passed stability (r≥0.4)

| Metric | r | n pairs | Category |
|---|---:|---:|---|
| dispossessed | 0.787 | 60 | Other |
| pass_progressive | 0.7195 | 60 | Passing |
| pressures | 0.677 | 60 | Defending |
| passes | 0.5318 | 60 | Passing |
| tackles | 0.5318 | 60 | Defending |
| clearances | 0.4914 | 60 | Defending |
| xg | 0.4825 | 60 | Attacking |
| shots | 0.4474 | 60 | Attacking |
| dribbles_completed | 0.4393 | 60 | Carrying |
| passes_into_final_third | 0.4314 | 60 | Passing |
| carries | 0.413 | 60 | Carrying |

## Step 2 — redundancy (your pick)

Review `redundancy_high_pairs_step2.csv`. Default auto shortlist used for rankings/pizzas: `['dispossessed', 'pass_progressive', 'pressures', 'tackles', 'clearances', 'xg', 'dribbles_completed', 'passes_into_final_third', 'carries']`.

| Metric A | Metric B | r |
|---|---|---:|
| pass_progressive | passes | 0.7928 |
| passes | carries | 0.9304 |
| xg | shots | 0.8648 |

## Top targets (mean Y1 pctile on auto shortlist)

| Rank | Player | Pos | Score | Source |
|---:|---|---|---:|---|
| 1 | Konrad Laimer | Full Back | 72.39 | UEFA Euro |
| 2 | Piero Martín Hincapié Reyna | Central Defender | 71.41 | FIFA World Cup |
| 3 | Eric Dier | Central Defender | 68.57 | Premier League |
| 4 | Josip Juranović | Full Back | 68.31 | FIFA World Cup |
| 5 | Dayotchanculle Upamecano | Central Defender | 68.01 | FIFA World Cup |
| 6 | Josip Stanišić | Central Defender | 67.01 | FIFA World Cup |
| 7 | Emiliano Adrián Insúa Zapata | Full Back | 66.61 | La Liga |
| 8 | Lovro Majer | Central Midfielder | 65.61 | Ligue 1 |
| 9 | Min Jae Kim | Central Defender | 64.26 | FIFA World Cup |
| 10 | Noussair Mazraoui | Full Back | 64.21 | FIFA World Cup |
| 11 | Ellyes Joris Skhiri | Central Midfielder | 63.88 | Ligue 1 |
| 12 | Franck Honorat | Full Back | 63.58 | Ligue 1 |
| 13 | Nico Schlotterbeck | Central Defender | 63.13 | FIFA World Cup |
| 14 | David Raum | Full Back | 61.8 | FIFA World Cup |
| 15 | Serge Gnabry | Winger | 61.54 | FIFA World Cup |
