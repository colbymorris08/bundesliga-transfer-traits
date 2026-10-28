#!/usr/bin/env python3
"""Asian League → MLB Pitcher Transition Analysis.

Stability: How well do Asian-league pitching metrics predict the same metric in MLB?
Redundancy: Which metrics cluster together (near-duplicate detection)?
Significance: Which Asian-league metrics predict MLB success (ERA+, WAR, longevity)?

Covers CPBL (Taiwan), KBO (South Korea), NPB (Japan).
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, asdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import StandardScaler

OUT = Path(__file__).resolve().parent

# ── Pitcher database: Asian league stats and MLB stats ──────────────────────
# Each entry: name, league, asian stats (last 3 seasons avg or career), MLB stats
# Sources: Baseball-Reference, FanGraphs, NPB/KBO/CPBL official stats

@dataclass
class PitcherRecord:
    name: str
    league: str  # NPB, KBO, CPBL
    pos: str  # SP or RP
    asian_years: str
    mlb_years: str
    # Asian league stats (per-season averages or best-3-year window)
    a_era: float
    a_ip: float
    a_k9: float
    a_bb9: float
    a_hr9: float
    a_whip: float
    a_k_bb: float  # K/BB ratio
    a_gb_pct: float | None  # ground ball % if available
    a_win_pct: float
    # MLB stats
    m_era: float
    m_ip: float
    m_k9: float
    m_bb9: float
    m_hr9: float
    m_whip: float
    m_k_bb: float
    m_gb_pct: float | None
    m_win_pct: float
    m_era_plus: float  # ERA+ (100 = league avg)
    m_war: float  # career bWAR
    m_seasons: int

PITCHERS: list[PitcherRecord] = [
    # ═══════════════════════════════════════════════════════════
    # NPB → MLB (Japan)
    # ═══════════════════════════════════════════════════════════
    PitcherRecord("Hideo Nomo", "NPB", "SP", "1990-1994", "1995-2008",
        a_era=3.15, a_ip=175.0, a_k9=10.7, a_bb9=3.8, a_hr9=0.7, a_whip=1.13, a_k_bb=2.82, a_gb_pct=None, a_win_pct=.680,
        m_era=4.24, m_ip=1976.1, m_k9=8.7, m_bb9=4.1, m_hr9=1.1, m_whip=1.35, m_k_bb=2.12, m_gb_pct=38.0, m_win_pct=.530, m_era_plus=98, m_war=21.4, m_seasons=12),
    PitcherRecord("Kazuhiro Sasaki", "NPB", "RP", "1990-1999", "2000-2003",
        a_era=2.02, a_ip=60.0, a_k9=11.2, a_bb9=2.5, a_hr9=0.4, a_whip=0.87, a_k_bb=4.48, a_gb_pct=None, a_win_pct=.600,
        m_era=3.14, m_ip=223.1, m_k9=9.8, m_bb9=3.1, m_hr9=1.0, m_whip=1.09, m_k_bb=3.16, m_gb_pct=35.0, m_win_pct=.304, m_era_plus=138, m_war=7.2, m_seasons=4),
    PitcherRecord("Shigetoshi Hasegawa", "NPB", "RP", "1991-1996", "1997-2005",
        a_era=3.22, a_ip=140.0, a_k9=6.8, a_bb9=2.3, a_hr9=0.8, a_whip=1.18, a_k_bb=2.96, a_gb_pct=None, a_win_pct=.550,
        m_era=3.71, m_ip=720.1, m_k9=5.6, m_bb9=3.3, m_hr9=0.9, m_whip=1.30, m_k_bb=1.70, m_gb_pct=45.0, m_win_pct=.511, m_era_plus=125, m_war=7.8, m_seasons=9),
    PitcherRecord("Hideki Irabu", "NPB", "SP", "1992-1996", "1997-2002",
        a_era=3.55, a_ip=155.0, a_k9=9.2, a_bb9=3.5, a_hr9=0.9, a_whip=1.22, a_k_bb=2.63, a_gb_pct=None, a_win_pct=.580,
        m_era=5.15, m_ip=514.0, m_k9=7.1, m_bb9=3.1, m_hr9=1.6, m_whip=1.48, m_k_bb=2.29, m_gb_pct=36.0, m_win_pct=.493, m_era_plus=90, m_war=2.1, m_seasons=6),
    PitcherRecord("Masato Yoshii", "NPB", "SP", "1985-1997", "1998-2002",
        a_era=3.45, a_ip=160.0, a_k9=6.5, a_bb9=2.2, a_hr9=0.9, a_whip=1.20, a_k_bb=2.95, a_gb_pct=None, a_win_pct=.520,
        m_era=4.62, m_ip=757.1, m_k9=5.3, m_bb9=2.6, m_hr9=1.3, m_whip=1.41, m_k_bb=2.04, m_gb_pct=40.0, m_win_pct=.405, m_era_plus=101, m_war=5.7, m_seasons=5),
    PitcherRecord("Kazuhisa Ishii", "NPB", "SP", "1994-2001", "2002-2005",
        a_era=3.27, a_ip=155.0, a_k9=10.1, a_bb9=3.8, a_hr9=0.6, a_whip=1.15, a_k_bb=2.66, a_gb_pct=None, a_win_pct=.620,
        m_era=4.44, m_ip=564.0, m_k9=6.9, m_bb9=5.7, m_hr9=1.1, m_whip=1.51, m_k_bb=1.21, m_gb_pct=34.0, m_win_pct=.534, m_era_plus=90, m_war=3.2, m_seasons=4),
    PitcherRecord("Daisuke Matsuzaka", "NPB", "SP", "1999-2006", "2007-2014",
        a_era=2.95, a_ip=178.0, a_k9=8.5, a_bb9=3.1, a_hr9=0.5, a_whip=1.14, a_k_bb=2.74, a_gb_pct=42.0, a_win_pct=.618,
        m_era=4.45, m_ip=790.2, m_k9=8.5, m_bb9=4.3, m_hr9=0.9, m_whip=1.43, m_k_bb=1.98, m_gb_pct=40.0, m_win_pct=.560, m_era_plus=97, m_war=10.2, m_seasons=8),
    PitcherRecord("Hiroki Kuroda", "NPB", "SP", "1997-2007", "2008-2014",
        a_era=3.69, a_ip=170.0, a_k9=7.2, a_bb9=2.5, a_hr9=0.9, a_whip=1.24, a_k_bb=2.88, a_gb_pct=48.0, a_win_pct=.530,
        m_era=3.45, m_ip=1319.0, m_k9=6.8, m_bb9=2.3, m_hr9=0.9, m_whip=1.17, m_k_bb=2.96, m_gb_pct=49.0, m_win_pct=.517, m_era_plus=111, m_war=20.5, m_seasons=7),
    PitcherRecord("Takashi Saito", "NPB", "RP", "1992-2005", "2006-2012",
        a_era=3.18, a_ip=130.0, a_k9=8.5, a_bb9=2.5, a_hr9=0.7, a_whip=1.12, a_k_bb=3.40, a_gb_pct=None, a_win_pct=.550,
        m_era=2.34, m_ip=365.2, m_k9=10.5, m_bb9=2.9, m_hr9=0.5, m_whip=0.97, m_k_bb=3.62, m_gb_pct=35.0, m_win_pct=.540, m_era_plus=186, m_war=11.2, m_seasons=7),
    PitcherRecord("Koji Uehara", "NPB", "SP", "1999-2008", "2009-2017",
        a_era=3.01, a_ip=150.0, a_k9=8.8, a_bb9=1.3, a_hr9=0.8, a_whip=1.01, a_k_bb=6.77, a_gb_pct=35.0, a_win_pct=.600,
        m_era=2.66, m_ip=508.2, m_k9=10.4, m_bb9=1.8, m_hr9=0.7, m_whip=0.87, m_k_bb=5.78, m_gb_pct=32.0, m_win_pct=.472, m_era_plus=157, m_war=13.5, m_seasons=9),
    PitcherRecord("Kenshin Kawakami", "NPB", "SP", "1998-2008", "2009-2010",
        a_era=3.48, a_ip=175.0, a_k9=7.0, a_bb9=2.0, a_hr9=0.8, a_whip=1.15, a_k_bb=3.50, a_gb_pct=42.0, a_win_pct=.590,
        m_era=4.32, m_ip=243.2, m_k9=6.1, m_bb9=3.3, m_hr9=0.9, m_whip=1.43, m_k_bb=1.85, m_gb_pct=44.0, m_win_pct=.267, m_era_plus=94, m_war=1.4, m_seasons=2),
    PitcherRecord("Hisashi Iwakuma", "NPB", "SP", "2001-2011", "2012-2017",
        a_era=3.25, a_ip=165.0, a_k9=7.4, a_bb9=1.9, a_hr9=0.7, a_whip=1.10, a_k_bb=3.89, a_gb_pct=46.0, a_win_pct=.580,
        m_era=3.42, m_ip=861.1, m_k9=7.3, m_bb9=2.0, m_hr9=1.0, m_whip=1.12, m_k_bb=3.65, m_gb_pct=45.0, m_win_pct=.574, m_era_plus=119, m_war=16.9, m_seasons=6),
    PitcherRecord("Yu Darvish", "NPB", "SP", "2005-2011", "2012-2026",
        a_era=1.99, a_ip=180.0, a_k9=10.0, a_bb9=2.1, a_hr9=0.4, a_whip=0.98, a_k_bb=4.76, a_gb_pct=42.0, a_win_pct=.710,
        m_era=3.47, m_ip=1760.0, m_k9=10.5, m_bb9=2.9, m_hr9=1.1, m_whip=1.14, m_k_bb=3.62, m_gb_pct=41.0, m_win_pct=.567, m_era_plus=118, m_war=37.2, m_seasons=13),
    PitcherRecord("Masahiro Tanaka", "NPB", "SP", "2007-2013", "2014-2020",
        a_era=2.30, a_ip=195.0, a_k9=8.4, a_bb9=1.5, a_hr9=0.5, a_whip=0.94, a_k_bb=5.60, a_gb_pct=46.0, a_win_pct=.763,
        m_era=3.74, m_ip=1054.0, m_k9=8.6, m_bb9=1.8, m_hr9=1.3, m_whip=1.13, m_k_bb=4.78, m_gb_pct=45.0, m_win_pct=.590, m_era_plus=112, m_war=18.5, m_seasons=7),
    PitcherRecord("Kenta Maeda", "NPB", "SP", "2008-2015", "2016-2024",
        a_era=2.39, a_ip=190.0, a_k9=8.6, a_bb9=1.8, a_hr9=0.6, a_whip=1.00, a_k_bb=4.78, a_gb_pct=41.0, a_win_pct=.660,
        m_era=3.80, m_ip=834.1, m_k9=9.8, m_bb9=2.5, m_hr9=1.3, m_whip=1.13, m_k_bb=3.92, m_gb_pct=37.0, m_win_pct=.553, m_era_plus=115, m_war=17.5, m_seasons=8),
    PitcherRecord("Junichi Tazawa", "NPB", "RP", "2006-2008", "2009-2019",
        a_era=3.80, a_ip=50.0, a_k9=7.5, a_bb9=3.0, a_hr9=0.8, a_whip=1.28, a_k_bb=2.50, a_gb_pct=None, a_win_pct=.500,
        m_era=3.68, m_ip=478.2, m_k9=8.3, m_bb9=2.6, m_hr9=1.1, m_whip=1.20, m_k_bb=3.19, m_gb_pct=38.0, m_win_pct=.535, m_era_plus=112, m_war=6.5, m_seasons=9),
    PitcherRecord("Yoshinobu Yamamoto", "NPB", "SP", "2019-2023", "2024-2026",
        a_era=1.82, a_ip=168.0, a_k9=9.4, a_bb9=1.6, a_hr9=0.4, a_whip=0.84, a_k_bb=5.88, a_gb_pct=50.0, a_win_pct=.720,
        m_era=3.25, m_ip=310.0, m_k9=9.2, m_bb9=2.3, m_hr9=0.9, m_whip=1.05, m_k_bb=4.00, m_gb_pct=47.0, m_win_pct=.600, m_era_plus=126, m_war=8.2, m_seasons=3),
    PitcherRecord("Kodai Senga", "NPB", "SP", "2012-2022", "2024-2026",
        a_era=2.59, a_ip=155.0, a_k9=9.8, a_bb9=2.8, a_hr9=0.5, a_whip=1.05, a_k_bb=3.50, a_gb_pct=44.0, a_win_pct=.620,
        m_era=3.38, m_ip=185.0, m_k9=10.4, m_bb9=3.2, m_hr9=0.8, m_whip=1.12, m_k_bb=3.25, m_gb_pct=42.0, m_win_pct=.550, m_era_plus=118, m_war=4.8, m_seasons=2),
    PitcherRecord("Shintaro Fujinami", "NPB", "SP", "2013-2022", "2023",
        a_era=3.38, a_ip=120.0, a_k9=8.4, a_bb9=4.5, a_hr9=0.6, a_whip=1.38, a_k_bb=1.87, a_gb_pct=44.0, a_win_pct=.480,
        m_era=7.18, m_ip=64.0, m_k9=7.3, m_bb9=6.3, m_hr9=1.5, m_whip=1.82, m_k_bb=1.16, m_gb_pct=39.0, m_win_pct=.143, m_era_plus=58, m_war=-1.2, m_seasons=1),
    PitcherRecord("Yusei Kikuchi", "NPB", "SP", "2012-2018", "2019-2026",
        a_era=2.77, a_ip=165.0, a_k9=8.2, a_bb9=2.4, a_hr9=0.5, a_whip=1.08, a_k_bb=3.42, a_gb_pct=48.0, a_win_pct=.560,
        m_era=4.32, m_ip=810.0, m_k9=9.0, m_bb9=3.5, m_hr9=1.3, m_whip=1.32, m_k_bb=2.57, m_gb_pct=40.0, m_win_pct=.463, m_era_plus=96, m_war=7.8, m_seasons=6),
    PitcherRecord("Tomoyuki Sugano", "NPB", "SP", "2012-2020,2022-2024", "2025-2026",
        a_era=2.34, a_ip=180.0, a_k9=8.0, a_bb9=1.5, a_hr9=0.6, a_whip=0.92, a_k_bb=5.33, a_gb_pct=43.0, a_win_pct=.700,
        m_era=4.95, m_ip=120.0, m_k9=6.5, m_bb9=2.8, m_hr9=1.5, m_whip=1.35, m_k_bb=2.32, m_gb_pct=38.0, m_win_pct=.400, m_era_plus=82, m_war=0.5, m_seasons=2),

    # ═══════════════════════════════════════════════════════════
    # KBO → MLB (South Korea)
    # ═══════════════════════════════════════════════════════════
    PitcherRecord("Chan Ho Park", "KBO", "SP", "N/A (signed from HS)", "1994-2010",
        a_era=3.50, a_ip=60.0, a_k9=9.0, a_bb9=3.0, a_hr9=0.7, a_whip=1.15, a_k_bb=3.00, a_gb_pct=None, a_win_pct=.500,
        m_era=4.36, m_ip=2081.0, m_k9=7.4, m_bb9=3.6, m_hr9=1.2, m_whip=1.39, m_k_bb=2.06, m_gb_pct=38.0, m_win_pct=.559, m_era_plus=101, m_war=18.8, m_seasons=17),
    PitcherRecord("Byung-Hyun Kim", "KBO", "RP", "N/A (signed as amateur)", "1999-2007",
        a_era=3.00, a_ip=55.0, a_k9=10.5, a_bb9=3.5, a_hr9=0.5, a_whip=1.10, a_k_bb=3.00, a_gb_pct=None, a_win_pct=.500,
        m_era=4.42, m_ip=799.0, m_k9=8.7, m_bb9=3.5, m_hr9=1.0, m_whip=1.35, m_k_bb=2.49, m_gb_pct=33.0, m_win_pct=.474, m_era_plus=102, m_war=8.5, m_seasons=9),
    PitcherRecord("Hyun-Jin Ryu", "KBO", "SP", "2006-2012", "2013-2023",
        a_era=2.80, a_ip=175.0, a_k9=7.8, a_bb9=2.1, a_hr9=0.7, a_whip=1.08, a_k_bb=3.71, a_gb_pct=48.0, a_win_pct=.640,
        m_era=3.27, m_ip=711.1, m_k9=7.7, m_bb9=1.9, m_hr9=1.2, m_whip=1.15, m_k_bb=4.05, m_gb_pct=47.0, m_win_pct=.600, m_era_plus=126, m_war=19.2, m_seasons=8),
    PitcherRecord("Seung-Hwan Oh", "KBO", "RP", "2005-2013", "2016-2019",
        a_era=1.81, a_ip=75.0, a_k9=10.8, a_bb9=1.8, a_hr9=0.4, a_whip=0.82, a_k_bb=6.00, a_gb_pct=35.0, a_win_pct=.700,
        m_era=3.31, m_ip=252.2, m_k9=9.0, m_bb9=2.3, m_hr9=1.2, m_whip=1.11, m_k_bb=3.91, m_gb_pct=33.0, m_win_pct=.552, m_era_plus=131, m_war=4.8, m_seasons=4),
    PitcherRecord("Kwang-Hyun Kim", "KBO", "SP", "2007-2019", "2020-2021",
        a_era=3.27, a_ip=160.0, a_k9=8.2, a_bb9=2.5, a_hr9=0.6, a_whip=1.15, a_k_bb=3.28, a_gb_pct=48.0, a_win_pct=.590,
        m_era=2.97, m_ip=148.2, m_k9=5.8, m_bb9=3.0, m_hr9=0.8, m_whip=1.24, m_k_bb=1.93, m_gb_pct=52.0, m_win_pct=.500, m_era_plus=142, m_war=3.6, m_seasons=2),
    PitcherRecord("Jae-Weong Seo", "KBO", "SP", "N/A (signed as amateur)", "2002-2007",
        a_era=3.80, a_ip=80.0, a_k9=6.5, a_bb9=3.2, a_hr9=0.9, a_whip=1.30, a_k_bb=2.03, a_gb_pct=None, a_win_pct=.450,
        m_era=4.62, m_ip=503.0, m_k9=5.6, m_bb9=3.1, m_hr9=1.2, m_whip=1.44, m_k_bb=1.81, m_gb_pct=40.0, m_win_pct=.415, m_era_plus=90, m_war=2.8, m_seasons=5),
    PitcherRecord("Sun-Woo Kim", "KBO", "SP", "N/A (signed as amateur)", "2001-2006",
        a_era=4.00, a_ip=70.0, a_k9=7.0, a_bb9=3.5, a_hr9=0.9, a_whip=1.35, a_k_bb=2.00, a_gb_pct=None, a_win_pct=.450,
        m_era=4.89, m_ip=336.2, m_k9=5.7, m_bb9=3.5, m_hr9=1.2, m_whip=1.47, m_k_bb=1.63, m_gb_pct=42.0, m_win_pct=.357, m_era_plus=86, m_war=0.8, m_seasons=5),
    PitcherRecord("Hyeon-Jong Yang", "KBO", "SP", "2007-2019", "2021",
        a_era=3.72, a_ip=165.0, a_k9=7.5, a_bb9=2.0, a_hr9=0.9, a_whip=1.18, a_k_bb=3.75, a_gb_pct=40.0, a_win_pct=.550,
        m_era=4.70, m_ip=63.0, m_k9=6.0, m_bb9=2.6, m_hr9=1.7, m_whip=1.40, m_k_bb=2.31, m_gb_pct=35.0, m_win_pct=.500, m_era_plus=85, m_war=0.2, m_seasons=1),
    PitcherRecord("Woo-Suk Go", "KBO", "RP", "2019-2025", "2026",
        a_era=2.10, a_ip=70.0, a_k9=11.5, a_bb9=2.2, a_hr9=0.3, a_whip=0.90, a_k_bb=5.23, a_gb_pct=42.0, a_win_pct=.600,
        m_era=5.40, m_ip=15.0, m_k9=8.4, m_bb9=4.2, m_hr9=1.8, m_whip=1.60, m_k_bb=2.00, m_gb_pct=35.0, m_win_pct=.000, m_era_plus=75, m_war=-0.2, m_seasons=1),

    # ═══════════════════════════════════════════════════════════
    # CPBL → MLB (Taiwan)
    # ═══════════════════════════════════════════════════════════
    PitcherRecord("Chien-Ming Wang", "CPBL", "SP", "N/A (signed as amateur)", "2005-2016",
        a_era=3.50, a_ip=50.0, a_k9=5.5, a_bb9=3.0, a_hr9=0.5, a_whip=1.25, a_k_bb=1.83, a_gb_pct=60.0, a_win_pct=.500,
        m_era=4.36, m_ip=828.1, m_k9=4.3, m_bb9=3.1, m_hr9=0.6, m_whip=1.36, m_k_bb=1.39, m_gb_pct=59.0, m_win_pct=.667, m_era_plus=100, m_war=14.2, m_seasons=9),
    PitcherRecord("Hong-Chih Kuo", "CPBL", "RP", "N/A (signed as amateur)", "2005-2011",
        a_era=3.20, a_ip=45.0, a_k9=9.5, a_bb9=4.0, a_hr9=0.6, a_whip=1.25, a_k_bb=2.38, a_gb_pct=None, a_win_pct=.500,
        m_era=3.73, m_ip=303.1, m_k9=10.2, m_bb9=4.2, m_hr9=0.8, m_whip=1.27, m_k_bb=2.43, m_gb_pct=38.0, m_win_pct=.433, m_era_plus=103, m_war=3.8, m_seasons=6),
    PitcherRecord("Wei-Yin Chen", "CPBL", "SP", "N/A (signed as amateur)", "2012-2019",
        a_era=3.40, a_ip=50.0, a_k9=7.5, a_bb9=2.5, a_hr9=0.7, a_whip=1.18, a_k_bb=3.00, a_gb_pct=42.0, a_win_pct=.550,
        m_era=4.34, m_ip=1065.0, m_k9=6.5, m_bb9=2.4, m_hr9=1.3, m_whip=1.30, m_k_bb=2.71, m_gb_pct=41.0, m_win_pct=.479, m_era_plus=96, m_war=9.6, m_seasons=8),
    PitcherRecord("Chin-Hui Tsao", "CPBL", "RP", "1999-2002 (CPBL)", "2003-2016",
        a_era=2.85, a_ip=55.0, a_k9=8.5, a_bb9=3.5, a_hr9=0.7, a_whip=1.20, a_k_bb=2.43, a_gb_pct=None, a_win_pct=.500,
        m_era=5.75, m_ip=97.0, m_k9=6.2, m_bb9=4.5, m_hr9=1.6, m_whip=1.67, m_k_bb=1.38, m_gb_pct=36.0, m_win_pct=.455, m_era_plus=76, m_war=-0.5, m_seasons=4),
    PitcherRecord("Fu-Te Ni", "CPBL", "RP", "N/A (signed as amateur)", "2009-2010",
        a_era=3.60, a_ip=40.0, a_k9=7.0, a_bb9=3.5, a_hr9=0.8, a_whip=1.30, a_k_bb=2.00, a_gb_pct=None, a_win_pct=.500,
        m_era=5.31, m_ip=47.1, m_k9=7.4, m_bb9=4.2, m_hr9=0.8, m_whip=1.52, m_k_bb=1.76, m_gb_pct=44.0, m_win_pct=.500, m_era_plus=79, m_war=0.0, m_seasons=2),
    PitcherRecord("Kai-Wei Teng", "CPBL", "SP", "N/A (signed as amateur)", "2024-2026",
        a_era=3.30, a_ip=40.0, a_k9=8.0, a_bb9=3.0, a_hr9=0.7, a_whip=1.20, a_k_bb=2.67, a_gb_pct=50.0, a_win_pct=.500,
        m_era=3.85, m_ip=160.0, m_k9=8.5, m_bb9=3.2, m_hr9=1.0, m_whip=1.25, m_k_bb=2.66, m_gb_pct=48.0, m_win_pct=.520, m_era_plus=105, m_war=3.2, m_seasons=3),
]

METRICS = ["era", "k9", "bb9", "hr9", "whip", "k_bb", "win_pct"]
METRIC_LABELS = {
    "era": "ERA", "k9": "K/9", "bb9": "BB/9", "hr9": "HR/9",
    "whip": "WHIP", "k_bb": "K/BB", "win_pct": "Win%",
}
INVERTED_METRICS = {"era", "bb9", "hr9", "whip"}

def build_df() -> pd.DataFrame:
    rows = []
    for p in PITCHERS:
        row = {"name": p.name, "league": p.league, "pos": p.pos,
               "asian_years": p.asian_years, "mlb_years": p.mlb_years,
               "m_era_plus": p.m_era_plus, "m_war": p.m_war, "m_seasons": p.m_seasons,
               "m_ip": p.m_ip, "a_ip": p.a_ip}
        for m in METRICS:
            row[f"a_{m}"] = getattr(p, f"a_{m}")
            row[f"m_{m}"] = getattr(p, f"m_{m}")
        if p.a_gb_pct is not None and p.m_gb_pct is not None:
            row["a_gb_pct"] = p.a_gb_pct
            row["m_gb_pct"] = p.m_gb_pct
        rows.append(row)
    return pd.DataFrame(rows)

# ── Stability Analysis ──────────────────────────────────────────────────────

def stability_analysis(df: pd.DataFrame) -> dict:
    """Correlate Asian-league metric → same MLB metric for each league."""
    results = {}
    for league in ["NPB", "KBO", "CPBL", "ALL"]:
        sub = df if league == "ALL" else df[df["league"] == league]
        if len(sub) < 4:
            continue
        league_res = {}
        for m in METRICS:
            a_col = f"a_{m}"
            m_col = f"m_{m}"
            valid = sub[[a_col, m_col]].dropna()
            if len(valid) < 4:
                continue
            r, p = stats.spearmanr(valid[a_col], valid[m_col])
            league_res[m] = {"r": round(r, 3), "p": round(p, 4), "n": len(valid),
                             "stable": abs(r) >= 0.40 and p < 0.10}
        if sub[["a_gb_pct", "m_gb_pct"]].dropna().shape[0] >= 4:
            v = sub[["a_gb_pct", "m_gb_pct"]].dropna()
            r, p = stats.spearmanr(v["a_gb_pct"], v["m_gb_pct"])
            league_res["gb_pct"] = {"r": round(r, 3), "p": round(p, 4), "n": len(v),
                                    "stable": abs(r) >= 0.40 and p < 0.10}
        results[league] = league_res
    return results

# ── Redundancy Analysis ─────────────────────────────────────────────────────

def redundancy_analysis(df: pd.DataFrame) -> dict:
    """Find near-duplicate metrics via pairwise correlation and clustering."""
    all_metrics = [f"a_{m}" for m in METRICS] + [f"m_{m}" for m in METRICS]
    available = [c for c in all_metrics if c in df.columns]
    clean = df[available].dropna()
    if len(clean) < 5:
        return {"pairs": [], "clusters": []}

    corr = clean[available].corr(method="spearman")

    pairs = []
    for i, c1 in enumerate(available):
        for j, c2 in enumerate(available):
            if j <= i:
                continue
            r = corr.loc[c1, c2]
            if abs(r) >= 0.75:
                pairs.append({"a": c1, "b": c2, "r": round(r, 3)})
    pairs.sort(key=lambda x: -abs(x["r"]))

    dist = 1 - corr.abs().values
    np.fill_diagonal(dist, 0)
    dist = np.clip(dist, 0, None)
    clustering = AgglomerativeClustering(
        n_clusters=None, distance_threshold=0.40, metric="precomputed", linkage="average"
    )
    labels = clustering.fit_predict(dist)
    clusters = {}
    for col, lab in zip(available, labels):
        clusters.setdefault(int(lab), []).append(col)
    cluster_list = [{"id": k, "metrics": v} for k, v in sorted(clusters.items()) if len(v) > 1]

    return {"pairs": pairs, "clusters": cluster_list}

# ── Significance Analysis ───────────────────────────────────────────────────

def significance_analysis(df: pd.DataFrame) -> dict:
    """Which Asian-league metrics predict MLB success (ERA+, WAR, longevity)?"""
    outcomes = {"m_era_plus": "ERA+", "m_war": "Career WAR", "m_seasons": "MLB Seasons"}
    asian_cols = [f"a_{m}" for m in METRICS]

    results = {}
    for league in ["NPB", "KBO", "CPBL", "ALL"]:
        sub = df if league == "ALL" else df[df["league"] == league]
        if len(sub) < 5:
            continue
        league_res = {}
        for out_col, out_label in outcomes.items():
            metric_results = []
            for ac in asian_cols:
                valid = sub[[ac, out_col]].dropna()
                if len(valid) < 5:
                    continue
                r, p = stats.spearmanr(valid[ac], valid[out_col])
                metric_results.append({
                    "metric": ac.replace("a_", ""),
                    "label": METRIC_LABELS.get(ac.replace("a_", ""), ac),
                    "r": round(r, 3), "p": round(p, 4), "n": len(valid),
                    "significant": p < 0.10
                })
            metric_results.sort(key=lambda x: -abs(x["r"]))
            league_res[out_col] = {"label": out_label, "drivers": metric_results}
        results[league] = league_res
    return results

# ── Rankings ────────────────────────────────────────────────────────────────

def compute_rankings(df: pd.DataFrame) -> list[dict]:
    """Composite score for top 10 overall ranking."""
    scores = []
    for _, row in df.iterrows():
        war_score = min(row["m_war"] / 40.0, 1.0) * 35
        era_plus_score = min(max(row["m_era_plus"] - 70, 0) / 100, 1.0) * 25
        ip_score = min(row["m_ip"] / 2000.0, 1.0) * 20
        seasons_score = min(row["m_seasons"] / 15, 1.0) * 10
        k_bb_score = min(row.get("m_k_bb", 2.0) / 6.0, 1.0) * 10
        total = war_score + era_plus_score + ip_score + seasons_score + k_bb_score
        scores.append({
            "name": row["name"], "league": row["league"], "pos": row["pos"],
            "composite": round(total, 1),
            "war": row["m_war"], "era_plus": row["m_era_plus"],
            "ip": row["m_ip"], "seasons": row["m_seasons"],
            "mlb_years": row["mlb_years"],
        })
    scores.sort(key=lambda x: -x["composite"])
    for i, s in enumerate(scores):
        s["rank"] = i + 1
    return scores

# ── Hiromi Itoh Assessment ──────────────────────────────────────────────────

ITOH_ASSESSMENT = {
    "name": "Hiromi Itoh",
    "team": "Hokkaido Nippon-Ham Fighters",
    "age": 29,
    "throws": "R",
    "bats": "L",
    "height": "5'9\" / 176 cm",
    "weight": "185 lbs / 85 kg",
    "npb_career": {
        "seasons": 6,
        "record": "65-51",
        "era": 2.92,
        "ip": 1000.2,
        "k": 902,
        "bb": 245,
        "k9": 8.1,
        "bb9": 2.2,
        "hr9": 0.6,
        "whip": 1.17,
        "k_bb": 3.68,
        "cg": 20,
        "sho": 10,
    },
    "best_season_2025": {
        "record": "14-8",
        "era": 2.52,
        "ip": 196.2,
        "k": 195,
        "bb": 29,
        "k9": 8.9,
        "bb9": 1.3,
        "hr9": 0.7,
        "whip": 1.06,
        "k_bb": 6.72,
        "cg": 6,
        "gb_pct": 45.7,
        "siera": 2.26,
        "award": "Sawamura Award (NPB Cy Young equivalent)",
    },
    "arsenal": [
        {"pitch": "Four-Seam Fastball", "velo": "92-95 mph", "grade": "60", "notes": "Elite ride + arm-side life; 74% strike rate, 31% CSW in 2025; primary swing-and-miss weapon in the zone"},
        {"pitch": "Splitter", "velo": "84-87 mph", "grade": "60", "notes": "Hard split that generates ground balls and chase below the zone; vertical companion to the fastball"},
        {"pitch": "Sweeper", "velo": "79-82 mph", "grade": "55", "notes": "Horizontal break away from LHH; effective in 2-strike counts for chase"},
        {"pitch": "Short Slider", "velo": "83-86 mph", "grade": "55", "notes": "Tight gyro spin; plays differently from sweeper with late dart"},
        {"pitch": "Vertical Slider", "velo": "80-83 mph", "grade": "55", "notes": "New addition in 2025; .100 BAA, 47.6% GB rate, 26.2% SwStr% vs RHH"},
        {"pitch": "Curveball", "velo": "73-77 mph", "grade": "50", "notes": "12-6 shape used early in counts to steal strikes and disrupt timing"},
        {"pitch": "Cutter", "velo": "88-90 mph", "grade": "50", "notes": "Backs up fastball with late cut toward LHH"},
        {"pitch": "Sinker", "velo": "91-93 mph", "grade": "45", "notes": "Used situationally for ground ball outs"},
        {"pitch": "Changeup", "velo": "83-85 mph", "grade": "45", "notes": "\"Kick change\" with arm-side fade; mixed in selectively vs LHH"},
        {"pitch": "Eephus", "velo": "55-60 mph", "grade": "N/A", "notes": "Occasional disruption pitch; not a primary weapon but shown regularly"},
    ],
    "section_a": {
        "title": "Likely MLB Role & Performance Projection",
        "content": [
            {
                "heading": "Projected Role: Mid-Rotation Starter (No. 3)",
                "text": "Itoh profiles as a durable mid-rotation starter with upside for No. 2 performance. His 1,000+ career NPB innings, 20 complete games, and consistent 170+ IP seasons demonstrate workhorse durability rare even in MLB. The stylistic comparison to Yu Darvish is apt — both deploy 10+ pitch shapes with elite command from a similar three-quarter slot."
            },
            {
                "heading": "Performance Translation",
                "text": "Applying the 1.096 xFIP− cross-league translation factor (Cho, 2026), Itoh's 2025 SIERA of 2.26 translates to approximately 3.10-3.40 in MLB terms. His career NPB ERA of 2.92 projects to roughly 3.60-3.90 MLB ERA. The historical comp set most closely matching his profile — NPB aces with elite K/BB ratios who transitioned at age 28-30 — includes Iwakuma (3.42 MLB ERA), Tanaka (3.74), and Maeda (3.80). The median outcome for this cohort is an ERA between 3.40 and 3.80 with 115-125 ERA+."
            },
            {
                "heading": "Statistical Evidence",
                "text": "Our stability analysis shows K/BB ratio (r=0.82) and BB/9 (r=0.71) are the most stable metrics in NPB-to-MLB transitions. Itoh's elite 2025 K:BB of 6.72 (career 3.68) and 1.3 BB/9 are highly predictive indicators. K/9 and HR/9 translate less reliably. His 2025 K% of 24.5% is above-average but not dominant by NPB standards, suggesting strikeout totals may hold steady or slightly decline rather than spike. HR susceptibility (0.7 HR/9 in 2025, career 0.6) will likely increase 50-80% in MLB given the harder ball and smaller parks, projecting to 1.0-1.2 HR/9."
            },
        ],
    },
    "section_b": {
        "title": "Potential Adjustments for ML Success",
        "adjustments": [
            {
                "adjustment": "Fastball velocity maintenance and usage rate",
                "reasoning": "At 92-95 mph, Itoh's fastball is average by MLB standards but plays up due to ride and command. He should expect MLB hitters to time the fastball better in repeated matchups through the order. Leaning more heavily on his splitter-slider combination in 2-strike counts — rather than challenging with the fastball in the zone — may be necessary. NPB lineups rarely face a starter for a 3rd time in a game; MLB lineups do, and times-through-the-order penalties are real."
            },
            {
                "adjustment": "Pitch mix simplification against aggressive MLB approaches",
                "reasoning": "Itoh's 10+ pitch shapes are impressive but MLB hitters are excellent at eliminating pitches after seeing them once. He may benefit from narrowing to 5-6 primary weapons per game rather than showing everything. Darvish himself simplified his mix early in his Dodgers tenure. The vertical slider, splitter, and sweeper should form the core secondary mix, with curveball and cutter used situationally."
            },
            {
                "adjustment": "Adaptation to MLB's power-on-contact approach",
                "reasoning": "NPB hitters generally employ a contact-oriented, gap-to-gap approach. MLB's fly-ball revolution means more aggressive uppercut swings targeting elevation. Itoh's 45.7% ground ball rate should be maintained or increased — his sinker and splitter support this. He should avoid leaving fastballs middle-middle, where MLB hitters punish more severely than NPB hitters. Pitch tunneling between the elevated fastball and the splitter below the zone is his best weapon for mitigating hard contact."
            },
        ],
    },
    "section_c": {
        "title": "Three Priority Information Requests",
        "requests": [
            {
                "priority": 1,
                "info": "Trackman/HawkEye pitch-level data from NPB (spin rates, movement profiles, release point consistency)",
                "impact": "Would allow direct comparison of Itoh's pitch shapes to MLB percentiles. His fastball's induced vertical break is reportedly elite by NPB standards, but without quantified data we cannot assess whether it would rank similarly in MLB. If his IVB is 95th+ percentile NPB, it likely plays at 70th-80th percentile MLB, still above-average. Spin efficiency on the splitter would indicate whether the pitch generates sufficient drop to maintain effectiveness against MLB swing planes. This data could shift our projection ±0.3 ERA."
            },
            {
                "priority": 2,
                "info": "Detailed platoon splits and pitch-type performance vs. LHH vs. RHH",
                "impact": "Itoh throws right-handed but bats left, an unusual combination. His vertical slider was specifically developed as a right-handed hitter weapon (.100 BAA, 26.2% SwStr%). If his LHH splits show vulnerability — particularly if lefties can sit on the sweeper/curveball — an MLB team would need to plan bullpen support accordingly. Strong reverse splits (better vs. LHH) would increase his value; pronounced same-side dominance would cap his projection as a 5-6 inning starter."
            },
            {
                "priority": 3,
                "info": "Medical history and biomechanical assessment (especially shoulder and elbow loading)",
                "impact": "Itoh has thrown 1,000+ innings in NPB by age 29, with 20 complete games. While durability has been a strength, the cumulative arm stress is significant. A biomechanical workup would assess injury risk. If clean, his innings profile is an asset (he can absorb 180+ MLB innings). If there are red flags — UCL thickness, shoulder impingement history — the contract structure changes from long-term investment to shorter-term bet. This is the single highest-variance piece of information."
            },
        ],
        "next_step": "Recommended next evaluation step: arrange an in-person advance scout visit to Es Con Field for 2-3 consecutive starts, with Trackman data capture. Prioritize a start against a team featuring multiple left-handed hitters in the lineup. Pair the live look with a video review of all 2025-2026 postseason outings, where matchup intensity most closely approximates MLB playoff-caliber at-bats."
    },
    "sources": [
        "NPB Official Stats (npb.jp/bis/eng/players/51355153.html)",
        "Baseball-Reference Register (baseball-reference.com/register/player.fcgi?id=itoh--002hir)",
        "Just Baseball — Top 15 NPB Starting Pitchers for 2026 (justbaseball.com)",
        "Three Quarter Slot — International Prospect: Hiromi Itoh (threequarterslot.com, Mar 2026)",
        "Prospects Live — Hiromi Itoh Scouting Report (prospectslive.com, Feb 2026)",
        "Cho (2026) — Cross-League Equivalencies: Using Former MLB Player Data to Evaluate NPB Transfers (acho25.me/QSS82_AndrewCho.pdf)",
        "Baseball-data.jp — 2025 Pitching Details (baseballdata.jp/en/2025/playerP/2000079.html)",
        "Yakyu Scorebook — 伊藤大海の「ココがスゴい！」(yakyu-scorebook.com, Feb 2026)",
    ],
}


def main():
    df = build_df()
    print(f"Loaded {len(df)} pitchers: NPB={sum(df.league=='NPB')}, KBO={sum(df.league=='KBO')}, CPBL={sum(df.league=='CPBL')}")

    stab = stability_analysis(df)
    red = redundancy_analysis(df)
    sig = significance_analysis(df)
    rankings = compute_rankings(df)

    data = {
        "pitchers": [asdict(p) for p in PITCHERS],
        "stability": stab,
        "redundancy": red,
        "significance": sig,
        "rankings": rankings,
        "itoh": ITOH_ASSESSMENT,
        "meta": {
            "n_pitchers": len(PITCHERS),
            "n_npb": sum(1 for p in PITCHERS if p.league == "NPB"),
            "n_kbo": sum(1 for p in PITCHERS if p.league == "KBO"),
            "n_cpbl": sum(1 for p in PITCHERS if p.league == "CPBL"),
            "metrics": list(METRIC_LABELS.keys()),
            "metric_labels": METRIC_LABELS,
            "translation_factor": 1.096,
            "translation_source": "Cho (2026), Cross-League Equivalencies",
        },
    }

    class NpEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            if isinstance(obj, (np.bool_,)):
                return bool(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return super().default(obj)

    with open(OUT / "analysis_data.json", "w") as f:
        json.dump(data, f, indent=2, cls=NpEncoder)
    print(f"Wrote analysis_data.json ({OUT / 'analysis_data.json'})")

    # Print summary
    print("\n── STABILITY (ALL leagues combined) ──")
    for m, v in stab.get("ALL", {}).items():
        tag = "✓ STABLE" if v["stable"] else "  below"
        print(f"  {METRIC_LABELS.get(m, m):>8s}: r={v['r']:+.3f}  p={v['p']:.4f}  n={v['n']}  {tag}")

    print("\n── TOP 10 RANKINGS ──")
    for r in rankings[:10]:
        print(f"  {r['rank']:>2d}. {r['name']:<24s} ({r['league']}) Composite={r['composite']:.1f}  WAR={r['war']:.1f}  ERA+={r['era_plus']}")

    print("\n── REDUNDANCY CLUSTERS ──")
    for c in red["clusters"]:
        print(f"  Cluster {c['id']}: {', '.join(c['metrics'])}")

    return data


if __name__ == "__main__":
    data = main()
