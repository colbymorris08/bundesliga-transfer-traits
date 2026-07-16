# FBref stability — Bundesliga inbound (Big 5)

**Source:** FBref Big 5 via worldfootballR load_fb_big5_advanced_season_stats
**Seasons (end years):** 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025
**Minutes:** prior ≥ 450 · BL Y1 ≥ 450
**Stability gate (Step 2):** **r ≥ 0.50**
**Paired inbound N:** **117**
**Metrics tested:** 103
**Passed r ≥ 0.40:** 71
**Passed r ≥ 0.50:** **61**
**Passed r ≥ 0.70:** **35**
**Redundancy pairs (among r≥0.50):** **193**
**Auto shortlist:** **18**

## Metrics that passed r ≥ 0.50

| Abbrev | Metric | Category | r | N |
|---|---|---|---:|---:|
| DEFPE | Def Pen Touches | Defending | 0.920 | 114 |
| PRGC | PrgC Progression | Passing | 0.891 | 117 |
| PRGDI | PrgDist Total | Passing | 0.865 | 117 |
| ATTLO | Att Long | Other | 0.851 | 117 |
| XG | xG Per | Attacking | 0.849 | 117 |
| PRGR | PrgR Progression | Passing | 0.843 | 117 |
| SHPER | Sh/90 Standard | Attacking | 0.836 | 117 |
| XGPLU | xG+xAG Per | Passing | 0.833 | 117 |
| NPXG | npxG Per | Attacking | 0.831 | 117 |
| NPXGP | npxG+xAG Per | Passing | 0.821 | 117 |
| CMPLO | Cmp Long | Passing | 0.812 | 117 |
| TOTDI | TotDist Total | Passing | 0.797 | 117 |
| DEF3R | Def 3rd Touches | Defending | 0.795 | 114 |
| SOTPE | SoT/90 Standard | Attacking | 0.790 | 117 |
| ATTME | Att Medium | Other | 0.790 | 117 |
| CMPME | Cmp Medium | Passing | 0.782 | 117 |
| ATT | Att Total | Other | 0.773 | 117 |
| PRGRR | PrgR Receiving | Carrying | 0.769 | 114 |
| PRGC | PrgC Carries | Carrying | 0.759 | 114 |
| KP | KP | Passing | 0.756 | 117 |
| CMP | Cmp Total | Passing | 0.752 | 117 |
| ATTPE | Att Pen Touches | Carrying | 0.738 | 114 |
| ATT3R | Att 3rd Touches | Carrying | 0.733 | 114 |
| CLR | Clr | Defending | 0.723 | 114 |
| GPLUS | G+A Per | Other | 0.720 | 117 |
| GLS | Gls Per | Attacking | 0.715 | 117 |
| GLS | Gls Standard | Attacking | 0.714 | 117 |
| GPLUS | G+A minus PK Per | Attacking | 0.713 | 117 |
| CPA | CPA Carries | Carrying | 0.712 | 114 |
| SUCC | Succ Take | Carrying | 0.712 | 114 |
| TKLD | Tkld Take | Defending | 0.709 | 114 |
| WON | Won Aerial | Defending | 0.709 | 114 |
| PPA | PPA | Other | 0.706 | 117 |
| GMINU | G minus PK Per | Attacking | 0.706 | 117 |
| ATT | Att Take | Carrying | 0.702 | 114 |
| FINAL | Final Third | Passing | 0.698 | 117 |
| ATTSH | Att Short | Attacking | 0.695 | 117 |
| SH | Sh Blocks | Defending | 0.690 | 114 |
| CMPPE | Cmp percent Medium | Passing | 0.688 | 117 |
| CMPSH | Cmp Short | Passing | 0.686 | 117 |
| MIS | Mis Carries | Carrying | 0.675 | 114 |
| PRGP | PrgP Progression | Passing | 0.672 | 117 |
| FINAL | Final Third Carries | Passing | 0.664 | 114 |
| CRSPA | CrsPA | Passing | 0.662 | 117 |
| PROG | Prog | Passing | 0.657 | 56 |
| INT | Int | Defending | 0.648 | 114 |
| LOST | Lost Aerial | Defending | 0.644 | 114 |
| XAG | xAG Per | Passing | 0.640 | 117 |
| CMPPE | Cmp percent Total | Passing | 0.640 | 117 |
| CRS | Crs | Passing | 0.638 | 114 |
| XA | xA | Passing | 0.633 | 77 |
| CMPPE | Cmp percent Short | Passing | 0.632 | 117 |
| OFF | Off | Other | 0.630 | 114 |
| DIS | Dis Carries | Carrying | 0.602 | 114 |
| FLD | Fld | Other | 0.592 | 114 |
| TKLPL | Tkl+Int | Defending | 0.583 | 114 |
| WONPE | Won percent Aerial | Defending | 0.567 | 114 |
| DEF3R | Def 3rd Tackles | Defending | 0.543 | 114 |
| PRGP | PrgP | Passing | 0.540 | 34 |
| TKLPE | Tkl percent Challenges | Defending | 0.511 | 110 |
| RECOV | Recov | Defending | 0.503 | 114 |

## Redundancy pairs (|r|≥0.70 among r≥0.50)

| A | B | r |
|---|---|---:|
| PrgP_Progression | PrgP | 1.000 |
| Gls_Per | Gls_Standard | 1.000 |
| Att_Short | Cmp_Short | 0.995 |
| xG_plus_xAG_Per | npxG_plus_xAG_Per | 0.993 |
| G_plus_A_Per | G_plus_A_minus_PK_Per | 0.993 |
| Att_Medium | Cmp_Medium | 0.992 |
| Gls_Standard | G_minus_PK_Per | 0.990 |
| xG_Per | npxG_Per | 0.990 |
| Gls_Per | G_minus_PK_Per | 0.989 |
| Att_Total | Cmp_Total | 0.986 |
| TotDist_Total | Cmp_Medium | 0.968 |
| TotDist_Total | Att_Medium | 0.963 |
| xAG_Per | xA | 0.957 |
| TotDist_Total | Cmp_Total | 0.955 |
| TotDist_Total | Att_Total | 0.946 |
| xG_Per | xG_plus_xAG_Per | 0.943 |
| xG_plus_xAG_Per | npxG_Per | 0.943 |
| Tkld_Take | Att_Take | 0.942 |
| Att_Medium | Cmp_Total | 0.940 |
| Cmp_Medium | Cmp_Total | 0.937 |
| npxG_Per | npxG_plus_xAG_Per | 0.937 |
| Sh_per_90_Standard | SoT_per_90_Standard | 0.936 |
| PrgP_Progression | Prog | 0.936 |
| xG_plus_xAG_Per | G_plus_A_Per | 0.936 |
| Succ_Take | Att_Take | 0.934 |
| npxG_Per | SoT_per_90_Standard | 0.934 |
| Att_Medium | Att_Total | 0.932 |
| npxG_plus_xAG_Per | G_plus_A_Per | 0.929 |
| Att_Long | Cmp_Long | 0.929 |
| npxG_plus_xAG_Per | G_plus_A_minus_PK_Per | 0.927 |
| xG_Per | Gls_Standard | 0.926 |
| xG_Per | Gls_Per | 0.926 |
| xG_plus_xAG_Per | G_plus_A_minus_PK_Per | 0.921 |
| xG_Per | npxG_plus_xAG_Per | 0.921 |
| npxG_Per | Gls_Standard | 0.920 |
| G_plus_A_Per | Gls_Standard | 0.920 |
| npxG_Per | Gls_Per | 0.920 |
| G_plus_A_Per | Gls_Per | 0.920 |
| G_plus_A_Per | G_minus_PK_Per | 0.917 |
| xG_Per | SoT_per_90_Standard | 0.916 |

## Auto shortlist

- Def_Pen_Touches
- PrgC_Progression
- PrgDist_Total
- xG_Per
- KP
- Clr
- Succ_Take
- Won_Aerial
- Final_Third
- Cmp_percent_Medium
- CrsPA
- Int
- Crs
- Fld
- Won_percent_Aerial
- Def_3rd_Tackles
- Tkl_percent_Challenges
- Recov
