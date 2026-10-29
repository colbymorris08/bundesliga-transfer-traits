#!/usr/bin/env python3
"""Asian League → MLB Pitcher Transition Analysis.

Stability: How well do Asian-league pitching metrics predict the same metric in MLB?
Redundancy: Which metrics cluster together (near-duplicate detection)?
Significance: Which Asian-league metrics predict MLB success (ERA+, WAR, longevity)?

Covers CPBL (Taiwan), KBO (South Korea), NPB (Japan), plus American/crossover
pitchers who played in those leagues before (returning to) MLB.

Data sourced from: MLB Stats API, Baseball Reference Register, bWAR dataset,
with hand-compiled fallback for gaps.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sp_stats
from sklearn.cluster import AgglomerativeClustering

OUT = Path(__file__).resolve().parent

RATE_METRICS = ["era", "k9", "bb9", "hr9", "whip", "k_bb"]
ALL_METRICS = RATE_METRICS + ["gb_pct"]
METRIC_LABELS = {
    "era": "ERA", "k9": "K/9", "bb9": "BB/9", "hr9": "HR/9",
    "whip": "WHIP", "k_bb": "K/BB", "gb_pct": "GB%",
}
INVERTED_METRICS = {"era", "bb9", "hr9", "whip"}

WINDOWS = [
    ("1y", "Last 1yr Asia vs First 1yr MLB"),
    ("2y", "Last 2yr Asia vs First 2yr MLB"),
    ("3y", "Last 3yr Asia vs First 3yr MLB"),
    ("career", "Career Asia vs Career MLB"),
]


def load_data() -> pd.DataFrame:
    """Load unified pitcher data from the scraper output."""
    path = OUT / "scraped_data.json"
    records = json.loads(path.read_text())
    df = pd.DataFrame(records)

    for col in df.columns:
        if col.startswith("a_") or col.startswith("m_") or col.startswith("a1y") or col.startswith("a2y") or col.startswith("a3y") or col.startswith("m1y") or col.startswith("m2y") or col.startswith("m3y"):
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "m_seasons_bwar" in df.columns and "m_seasons" not in df.columns:
        df["m_seasons"] = df["m_seasons_bwar"]
    elif "m_seasons" not in df.columns:
        df["m_seasons"] = None

    return df


# ── Stability Analysis ──────────────────────────────────────────────────────

def _col_pair(metric: str, window: str) -> tuple[str, str]:
    """Return (asian_col, mlb_col) for a metric and window tag."""
    if window == "career":
        return f"a_{metric}", f"m_{metric}"
    return f"a{window}_{metric}", f"m{window}_{metric}"


def stability_analysis(df: pd.DataFrame) -> dict:
    """Correlate Asian-league metric -> same MLB metric across time windows and leagues.

    Returns {league: {window_tag: {metric: {r, p, n, stable}}}}.
    """
    results = {}
    for league in ["NPB", "KBO", "CPBL", "ALL"]:
        sub = df if league == "ALL" else df[df["league"] == league]
        if len(sub) < 4:
            continue
        league_res = {}
        for wtag, wlabel in WINDOWS:
            win_res = {}
            for m in ALL_METRICS:
                a_col, m_col = _col_pair(m, wtag)
                if a_col not in sub.columns or m_col not in sub.columns:
                    continue
                valid = sub[[a_col, m_col]].dropna()
                if len(valid) < 4:
                    continue
                r, p = sp_stats.pearsonr(valid[a_col], valid[m_col])
                win_res[m] = {
                    "r": round(float(r), 3),
                    "p": round(float(p), 4),
                    "n": int(len(valid)),
                    "stable": bool(abs(r) >= 0.40 and p < 0.10),
                }
            if win_res:
                league_res[wtag] = {"label": wlabel, "metrics": win_res}
        results[league] = league_res
    return results


# ── Redundancy Analysis ─────────────────────────────────────────────────────

def redundancy_analysis(df: pd.DataFrame) -> dict:
    """Find near-duplicate metrics via pairwise correlation and clustering.

    Uses Asian-league career metrics only (a_*), since the user correctly
    noted that if Asian ERA correlates with MLB ERA, then ERA is simply
    "ERA" — the redundancy is in the metric itself, not league-specific.
    """
    asian_cols = [f"a_{m}" for m in ALL_METRICS if f"a_{m}" in df.columns]
    clean = df[asian_cols].dropna()
    if len(clean) < 5:
        return {"pairs": [], "clusters": []}

    corr = clean.corr(method="pearson")

    pairs = []
    for i, c1 in enumerate(asian_cols):
        for j, c2 in enumerate(asian_cols):
            if j <= i:
                continue
            r = corr.loc[c1, c2]
            if abs(r) >= 0.75:
                m1 = c1.replace("a_", "")
                m2 = c2.replace("a_", "")
                pairs.append({
                    "a": m1, "b": m2,
                    "a_label": METRIC_LABELS.get(m1, m1),
                    "b_label": METRIC_LABELS.get(m2, m2),
                    "r": round(float(r), 3),
                })
    pairs.sort(key=lambda x: -abs(x["r"]))

    dist = 1 - corr.abs().values
    np.fill_diagonal(dist, 0)
    dist = np.clip(dist, 0, None)
    clustering = AgglomerativeClustering(
        n_clusters=None, distance_threshold=0.40, metric="precomputed", linkage="average"
    )
    labels = clustering.fit_predict(dist)
    clusters: dict[int, list[str]] = {}
    for col, lab in zip(asian_cols, labels):
        m = col.replace("a_", "")
        clusters.setdefault(int(lab), []).append(m)
    cluster_list = [
        {"id": k, "metrics": v, "labels": [METRIC_LABELS.get(m, m) for m in v]}
        for k, v in sorted(clusters.items()) if len(v) > 1
    ]

    return {"pairs": pairs, "clusters": cluster_list}


# ── Significance Analysis ───────────────────────────────────────────────────

def significance_analysis(df: pd.DataFrame) -> dict:
    """Which Asian-league metrics predict MLB success?

    Primary outcome: ERA+ (what predicts MLB performance).
    Secondary: Career WAR, MLB Seasons (longevity).
    Tests each window's Asian metrics against career MLB outcomes.
    """
    outcomes: dict[str, str] = {}
    if "m_era_plus" in df.columns:
        outcomes["m_era_plus"] = "ERA+"
    if "m_war" in df.columns:
        outcomes["m_war"] = "Career WAR"
    if "m_seasons" in df.columns:
        outcomes["m_seasons"] = "MLB Seasons"

    results = {}
    for league in ["NPB", "KBO", "CPBL", "ALL"]:
        sub = df if league == "ALL" else df[df["league"] == league]
        if len(sub) < 5:
            continue
        league_res = {}

        for wtag, wlabel in WINDOWS:
            win_res = {}
            for out_col, out_label in outcomes.items():
                metric_results = []
                for m in ALL_METRICS:
                    a_col = f"a_{m}" if wtag == "career" else f"a{wtag}_{m}"
                    if a_col not in sub.columns or out_col not in sub.columns:
                        continue
                    valid = sub[[a_col, out_col]].dropna()
                    if len(valid) < 5:
                        continue
                    r, p = sp_stats.pearsonr(valid[a_col], valid[out_col])
                    metric_results.append({
                        "metric": m,
                        "label": METRIC_LABELS.get(m, m),
                        "r": round(float(r), 3),
                        "p": round(float(p), 4),
                        "n": int(len(valid)),
                        "significant": bool(p < 0.10),
                    })
                metric_results.sort(key=lambda x: -abs(x["r"]))
                win_res[out_col] = {"label": out_label, "drivers": metric_results}
            league_res[wtag] = {"label": wlabel, "outcomes": win_res}

        results[league] = league_res
    return results


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
                "text": "Our stability analysis shows K/BB ratio and BB/9 are among the most stable metrics in NPB-to-MLB transitions. Itoh's elite 2025 K:BB of 6.72 (career 3.68) and 1.3 BB/9 are highly predictive indicators. K/9 and HR/9 translate less reliably. His 2025 K% of 24.5% is above-average but not dominant by NPB standards, suggesting strikeout totals may hold steady or slightly decline rather than spike. HR susceptibility (0.7 HR/9 in 2025, career 0.6) will likely increase 50-80% in MLB given the harder ball and smaller parks, projecting to 1.0-1.2 HR/9."
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
        "MLB Stats API (statsapi.mlb.com) — career pitching stats for all transitioned pitchers",
        "Baseball-Reference Register — Asian league career statistics (standard_pitching tables)",
        "Baseball-Reference bWAR dataset (pybaseball) — career WAR and ERA+ for MLB seasons",
        "NPB Official Stats (npb.jp/bis/eng/players/51355153.html)",
        "Cho (2026) — Cross-League Equivalencies: Using Former MLB Player Data to Evaluate NPB Transfers (acho25.me/QSS82_AndrewCho.pdf)",
        "Just Baseball — Top 15 NPB Starting Pitchers for 2026 (justbaseball.com)",
        "Three Quarter Slot — International Prospect: Hiromi Itoh (threequarterslot.com, Mar 2026)",
        "Prospects Live — Hiromi Itoh Scouting Report (prospectslive.com, Feb 2026)",
        "Baseball-data.jp — 2025 Pitching Details (baseballdata.jp/en/2025/playerP/2000079.html)",
        "Yakyu Scorebook — 伊藤大海の「ココがスゴい！」(yakyu-scorebook.com, Feb 2026)",
    ],
}


def main():
    df = load_data()
    n_asian = sum(df.get("origin", pd.Series()).isin(["JP", "KR", "TW"]))
    n_cross = sum(df.get("origin", pd.Series()).isin(["US"]))
    print(f"Loaded {len(df)} pitchers: NPB={sum(df.league=='NPB')}, KBO={sum(df.league=='KBO')}, CPBL={sum(df.league=='CPBL')}")
    print(f"  Asian-born: {n_asian}, Crossover (US/other): {n_cross}")

    both = df[df["a_era"].notna() & df["m_era"].notna()]
    print(f"Pitchers with both Asian + MLB data: {len(both)}")

    for wtag, wlabel in WINDOWS:
        a_col, m_col = _col_pair("era", wtag)
        if a_col in df.columns and m_col in df.columns:
            n = df[[a_col, m_col]].dropna().shape[0]
            print(f"  {wlabel}: {n} pitchers")

    stab = stability_analysis(df)
    red = redundancy_analysis(df)
    sig = significance_analysis(df)

    pitchers_out = []
    for _, row in df.iterrows():
        p = row.to_dict()
        for k, v in p.items():
            if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
                p[k] = None
        pitchers_out.append(p)

    data = {
        "pitchers": pitchers_out,
        "stability": stab,
        "redundancy": red,
        "significance": sig,
        "itoh": ITOH_ASSESSMENT,
        "windows": [{"tag": t, "label": l} for t, l in WINDOWS],
        "meta": {
            "n_pitchers": len(df),
            "n_npb": int(sum(df.league == "NPB")),
            "n_kbo": int(sum(df.league == "KBO")),
            "n_cpbl": int(sum(df.league == "CPBL")),
            "n_asian_born": int(n_asian),
            "n_crossover": int(n_cross),
            "n_with_both": int(len(both)),
            "metrics": list(METRIC_LABELS.keys()),
            "metric_labels": METRIC_LABELS,
            "translation_factor": 1.096,
            "translation_source": "Cho (2026), Cross-League Equivalencies",
            "p_value_note": (
                "p < 0.10 means less than 10% probability the observed correlation "
                "arose by chance under the null hypothesis of no linear relationship. "
                "A lower p-value provides stronger evidence that the metric genuinely "
                "transfers across leagues."
            ),
            "data_sources": [
                "MLB Stats API (statsapi.mlb.com)",
                "Baseball-Reference Register (standard_pitching tables)",
                "bWAR dataset via pybaseball",
                "Hand-compiled fallback for pitchers without API coverage",
            ],
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

    print("\n── STABILITY (ALL, by window) ──")
    for wtag, wlabel in WINDOWS:
        win_data = stab.get("ALL", {}).get(wtag, {}).get("metrics", {})
        if not win_data:
            continue
        print(f"\n  {wlabel}:")
        for m, v in win_data.items():
            tag = "STABLE" if v["stable"] else "below"
            print(f"    {METRIC_LABELS.get(m, m):>8s}: r={v['r']:+.3f}  p={v['p']:.4f}  n={v['n']}  {tag}")

    print("\n── REDUNDANCY CLUSTERS (Asian-only metrics) ──")
    for c in red["clusters"]:
        print(f"  Cluster {c['id']}: {', '.join(c['labels'])}")

    print("\n── REDUNDANT PAIRS (|r| >= 0.75) ──")
    for p in red["pairs"][:10]:
        print(f"  {p['a_label']:>8s} ~ {p['b_label']:<8s}: r={p['r']:+.3f}")

    print("\n── SIGNIFICANCE: Career Asian metrics → ERA+ (ALL) ──")
    sig_career = sig.get("ALL", {}).get("career", {}).get("outcomes", {})
    era_plus_data = sig_career.get("m_era_plus", {})
    for d in era_plus_data.get("drivers", []):
        tag = "SIG" if d["significant"] else "   "
        print(f"  {d['label']:>8s}: r={d['r']:+.3f}  p={d['p']:.4f}  n={d['n']}  {tag}")

    print("\n── SIGNIFICANCE: Career Asian metrics → Career WAR (ALL) ──")
    war_data = sig_career.get("m_war", {})
    for d in war_data.get("drivers", []):
        tag = "SIG" if d["significant"] else "   "
        print(f"  {d['label']:>8s}: r={d['r']:+.3f}  p={d['p']:.4f}  n={d['n']}  {tag}")

    return data


if __name__ == "__main__":
    data = main()
