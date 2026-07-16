#!/usr/bin/env python3
"""Broader FBref stability: Bundesliga inbound from many feeder leagues via soccerdata."""
from __future__ import annotations

import json
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

ROOT = Path("/Users/colbymorris/bundesliga-transfer-traits")
OUT = ROOT / "results"
CACHE = OUT / "fbref_broad_cache"
CACHE.mkdir(parents=True, exist_ok=True)

# Seasons as soccerdata codes
SEASONS = ["1718", "1819", "1920", "2021", "2122", "2223", "2324", "2425"]
STAT_TYPES = ["standard"]  # breadth first; expand later if needed

# All configured leagues that aren't destination-only
# Destination + Big 5 still pulled via soccerdata for consistent schema;
# non-Big-5 feeders are the expansion beyond the earlier N=117 run.
BIG5 = [
    "GER-Bundesliga",
    "ENG-Premier League",
    "ESP-La Liga",
    "ITA-Serie A",
    "FRA-Ligue 1",
]
FEEDERS = [
    "GER-2.Bundesliga",
    "ENG-Championship",
    "ESP-Segunda",
    "ITA-Serie B",
    "FRA-Ligue 2",
    "NED-Eredivisie",
    "POR-Primeira Liga",
    "BEL-Pro League",
    "AUT-Bundesliga",
    "TUR-Super Lig",
    "SUI-Super League",
    "DEN-Superliga",
    "SCO-Premiership",
    "POL-Ekstraklasa",
    "CZE-First League",
    "CRO-Football League",
    "GRE-Super League",
    "USA-MLS",
    "MEX-Liga MX",
    "RUS-Premier League",
    "UKR-Premier League",
    "SWE-Allsvenskan",
    "NOR-Eliteserien",
]
ALL_LEAGUES = BIG5 + FEEDERS

MIN_PRIOR = 450.0
MIN_Y1 = 450.0
STABILITY_GATE = 0.40
REDUNDANCY_GATE = 0.70
MIN_PAIRS = 25


def season_end_year(code: str) -> int:
    # '2324' -> 2024
    return 2000 + int(code[2:4])


def fetch_league_season(league: str, season: str, stat: str) -> pd.DataFrame | None:
    safe = league.replace(" ", "_").replace(".", "")
    path = CACHE / f"{safe}_{season}_{stat}.parquet"
    if path.exists():
        return pd.read_parquet(path)

    import soccerdata as sd

    try:
        fb = sd.FBref(leagues=league, seasons=season)
        df = fb.read_player_season_stats(stat_type=stat)
    except Exception as e:
        print(f"  FAIL {league} {season} {stat}: {e}")
        return None

    if df is None or len(df) == 0:
        return None

    # Flatten multiindex
    out = df.reset_index()
    out["league_key"] = league
    out["season_code"] = season
    out["season_end"] = season_end_year(season)
    out["stat_type"] = stat
    # save
    out.to_parquet(path, index=False)
    print(f"  saved {league} {season} {stat}: {len(out)} rows")
    time.sleep(1.5)
    return out


def main():
    frames = []
    for league in ALL_LEAGUES:
        for season in SEASONS:
            for stat in STAT_TYPES:
                print(f"pull {league} {season} {stat}")
                df = fetch_league_season(league, season, stat)
                if df is not None:
                    frames.append(df)

    if not frames:
        raise SystemExit("No data pulled")

    raw = pd.concat(frames, ignore_index=True)
    print("raw rows", len(raw), "cols", list(raw.columns)[:30])

    # Normalize column names (soccerdata varies)
    colmap = {}
    for c in raw.columns:
        cl = str(c).lower()
        if c in ("player", "Player"):
            colmap[c] = "player"
        elif c in ("team", "Squad", "squad"):
            colmap[c] = "squad"
        elif "min" == cl or cl.endswith("minutes") or cl == ("playing time", "min"):
            pass
    # minutes often MultiIndex flattened oddly
    # Find minutes column
    min_candidates = [c for c in raw.columns if "min" in str(c).lower() and "90" not in str(c).lower()]
    print("min candidates", min_candidates[:10])

    # soccerdata standard often has columns like ('Playing Time','Min') flattened to Playing Time_Min or similar
    df = raw.copy()
    # flatten tuple colnames if any
    newcols = []
    for c in df.columns:
        if isinstance(c, tuple):
            newcols.append("_".join(str(x) for x in c if x and str(x) != "nan"))
        else:
            newcols.append(str(c))
    df.columns = newcols

    # rename basics
    rename = {}
    for c in df.columns:
        cl = c.lower()
        if cl == "player":
            rename[c] = "player"
        elif cl in ("team", "squad"):
            rename[c] = "squad"
        elif cl == "league":
            rename[c] = "league"
        elif cl == "pos":
            rename[c] = "pos"
        elif cl in ("nation",):
            rename[c] = "nation"
    df = df.rename(columns=rename)

    # minutes
    min_col = None
    for c in df.columns:
        cl = c.lower().replace(" ", "_")
        if cl in ("playing_time_min", "min", "minutes", "playingtime_min"):
            min_col = c
            break
        if "playing_time" in cl and cl.endswith("min"):
            min_col = c
            break
    if min_col is None:
        # try any column ending with Min
        for c in df.columns:
            if str(c).endswith("Min") or str(c).endswith("_Min"):
                min_col = c
                break
    print("minutes col", min_col)
    if min_col is None:
        raise SystemExit(f"No minutes col in {list(df.columns)}")

    df["minutes"] = pd.to_numeric(df[min_col], errors="coerce")
    df["player"] = df["player"].astype(str)
    df["squad"] = df.get("squad", pd.Series(["unknown"] * len(df))).astype(str)
    df["is_bl"] = df["league_key"].eq("GER-Bundesliga")

    # player id: name lower (soccerdata may not give url consistently)
    df["player_id"] = df["player"].str.strip().str.lower()

    # Metric columns: numeric except ids
    skip = {
        "player", "squad", "league", "league_key", "season_code", "season_end",
        "stat_type", "pos", "nation", "age", "born", "minutes", "player_id",
        "is_bl", "team", min_col,
    }
    metric_cols = []
    for c in df.columns:
        if c in skip or c == min_col:
            continue
        if df[c].dtype == object:
            # try numeric
            conv = pd.to_numeric(df[c], errors="coerce")
            if conv.notna().mean() < 0.3:
                continue
            df[c] = conv
        if pd.api.types.is_numeric_dtype(df[c]):
            metric_cols.append(c)

    print("metric cols", len(metric_cols), metric_cols[:20])

    # First Bundesliga season
    bl = df[df["is_bl"] & df["minutes"].gt(0)].copy()
    first_bl = (
        bl.groupby("player_id", as_index=False)
        .agg(first_bl_season=("season_end", "min"), player=("player", "first"))
    )
    print("players with any BL row", len(first_bl))

    # Y1
    y1 = bl.merge(first_bl, on="player_id")
    y1 = y1[y1["season_end"].eq(y1["first_bl_season"]) & y1["minutes"].ge(MIN_Y1)]
    y1 = y1.sort_values("minutes").groupby("player_id", as_index=False).tail(1)
    print("Y1 with mins", len(y1))

    # Prior: last non-BL season before first BL
    prior = df[~df["is_bl"] & df["minutes"].ge(MIN_PRIOR)].merge(first_bl, on="player_id")
    prior = prior[prior["season_end"] < prior["first_bl_season"]]
    prior = (
        prior.sort_values(["player_id", "season_end", "minutes"])
        .groupby("player_id", as_index=False)
        .tail(1)
    )
    print("priors", len(prior))

    pairs = y1.merge(prior, on="player_id", suffixes=("_y1", "_prior"))
    print("PAIRS", len(pairs))
    print(pairs["league_key_prior"].value_counts().head(20))

    # Stability
    rows = []
    for m in metric_cols:
        # prefer per90 if column looks like rate; else convert counts
        x = pairs[f"{m}_prior"].astype(float)
        y = pairs[f"{m}_y1"].astype(float)
        # if looks like counting stat (large ints) convert both to per90
        name = m.lower()
        already_rate = any(k in name for k in ["per_90", "per90", "/90", "pct", "%", "percent"])
        if not already_rate:
            # heuristic: if median > 3 and values look like counts, per90
            med = np.nanmedian(np.concatenate([x.values, y.values]))
            if np.isfinite(med) and med > 2.5:
                x = x / pairs["minutes_prior"] * 90
                y = y / pairs["minutes_y1"] * 90
        ok = np.isfinite(x) & np.isfinite(y)
        n = int(ok.sum())
        if n < MIN_PAIRS:
            continue
        if np.nanstd(x[ok]) < 1e-8 or np.nanstd(y[ok]) < 1e-8:
            continue
        r = float(np.corrcoef(x[ok], y[ok])[0, 1])
        if not np.isfinite(r):
            continue
        rows.append({
            "metric": m,
            "n_pairs": n,
            "stability_r": r,
            "passes_0_40": r >= STABILITY_GATE,
            "passes_0_70": r >= 0.70,
        })

    stab = pd.DataFrame(rows).sort_values("stability_r", ascending=False)
    print("tested", len(stab), "pass040", int(stab["passes_0_40"].sum()))

    def categorize(m: str) -> str:
        ml = m.lower()
        if any(k in ml for k in ["tkl", "int", "block", "clr", "aerial", "def", "chall"]):
            return "Defending"
        if any(k in ml for k in ["pass", "prgp", "cmp", "xa", "xag", "kp", "prog"]):
            return "Passing"
        if any(k in ml for k in ["carr", "prgc", "prgr", "touch", "take", "drb", "mis", "dis"]):
            return "Carrying"
        if any(k in ml for k in ["gls", "ast", "xg", "npxg", "sh", "sot", "sca", "gca"]):
            return "Attacking"
        return "Other"

    stab["category"] = stab["metric"].map(categorize)
    stab["abbrev"] = stab["metric"].str.replace(r"[^A-Za-z0-9]", "", regex=True).str.upper().str[:5]
    stab["label"] = stab["metric"]

    passed = stab[stab["passes_0_40"]]
    pass_mets = passed["metric"].tolist()

    # redundancy on Y1
    red_rows = []
    if len(pass_mets) >= 2:
        mat = []
        for m in pass_mets:
            y = pairs[f"{m}_y1"].astype(float)
            name = m.lower()
            already_rate = any(k in name for k in ["per_90", "per90", "/90", "pct", "%", "percent"])
            if not already_rate:
                med = np.nanmedian(y.values)
                if np.isfinite(med) and med > 2.5:
                    y = y / pairs["minutes_y1"] * 90
            mat.append(y.values)
        mat = np.vstack(mat)
        # pairwise
        for i, a in enumerate(pass_mets):
            for j in range(i):
                b = pass_mets[j]
                aa, bb = mat[i], mat[j]
                ok = np.isfinite(aa) & np.isfinite(bb)
                if ok.sum() < MIN_PAIRS:
                    continue
                r = float(np.corrcoef(aa[ok], bb[ok])[0, 1])
                if np.isfinite(r) and abs(r) >= REDUNDANCY_GATE:
                    red_rows.append({"metric_a": b, "metric_b": a, "r": r})
    red = pd.DataFrame(red_rows).sort_values("r", key=lambda s: s.abs(), ascending=False) if red_rows else pd.DataFrame(columns=["metric_a","metric_b","r"])

    # auto shortlist
    auto = list(pass_mets)
    if len(red):
        drop = set()
        rmap = dict(zip(passed["metric"], passed["stability_r"]))
        for _, row in red.iterrows():
            a, b = row["metric_a"], row["metric_b"]
            if a in drop or b in drop:
                continue
            if rmap.get(a, 0) >= rmap.get(b, 0):
                drop.add(b)
            else:
                drop.add(a)
        auto = [m for m in auto if m not in drop]

    # Save
    stab.to_csv(OUT / "fbref_stability_all_metrics.csv", index=False)
    passed.to_csv(OUT / "fbref_stability_passed_r040.csv", index=False)
    stab[stab["passes_0_70"]].to_csv(OUT / "fbref_stability_passed_r070.csv", index=False)
    red.to_csv(OUT / "fbref_redundancy_high_pairs_step2.csv", index=False)
    pd.DataFrame({"metric": auto, "note": "AUTO keep higher-stability side of each |r|>=0.70 pair"}).to_csv(
        OUT / "fbref_redundancy_auto_shortlist_suggestion.csv", index=False
    )

    pairs_out = pd.DataFrame({
        "player_id": pairs["player_id"],
        "player": pairs["player_y1"],
        "prior_season": pairs["season_end_prior"],
        "prior_league": pairs["league_key_prior"],
        "prior_squad": pairs["squad_prior"],
        "prior_minutes": pairs["minutes_prior"],
        "y1_season": pairs["season_end_y1"],
        "y1_squad": pairs["squad_y1"],
        "y1_minutes": pairs["minutes_y1"],
    })
    pairs_out.to_csv(OUT / "fbref_inbound_pairs.csv", index=False)

    summary = {
        "source": "FBref via soccerdata (broad feeder leagues + Bundesliga)",
        "leagues": ALL_LEAGUES,
        "seasons": SEASONS,
        "min_prior_minutes": MIN_PRIOR,
        "min_y1_minutes": MIN_Y1,
        "n_pairs": int(len(pairs)),
        "n_metrics_tested": int(len(stab)),
        "n_pass_0_40": int(stab["passes_0_40"].sum()),
        "n_pass_0_70": int(stab["passes_0_70"].sum()),
        "n_redundancy_pairs": int(len(red)),
        "auto_shortlist_n": int(len(auto)),
        "auto_shortlist": auto,
        "prior_league_counts": pairs["league_key_prior"].value_counts().to_dict(),
        "statsbomb_comparison_n": 60,
    }
    (OUT / "fbref_cohort_summary.json").write_text(json.dumps(summary, indent=2))

    md = [
        "# FBref stability — broad inbound (many feeder leagues)",
        "",
        f"**Paired inbound N:** **{len(pairs)}** (was 117 Big-5-only)",
        f"**StatsBomb analysis cohort (for comparison):** **60**",
        f"**Minutes:** prior ≥ {int(MIN_PRIOR)} · BL Y1 ≥ {int(MIN_Y1)}",
        f"**Metrics tested:** {len(stab)}",
        f"**Passed r ≥ 0.40:** **{int(stab['passes_0_40'].sum())}**",
        f"**Passed r ≥ 0.70:** **{int(stab['passes_0_70'].sum())}**",
        f"**Redundancy pairs:** {len(red)}",
        f"**Auto shortlist:** {len(auto)}",
        "",
        "## Prior leagues feeding the pairs",
        "",
    ]
    for k, v in pairs["league_key_prior"].value_counts().items():
        md.append(f"- {k}: {v}")
    md += ["", "## Top passers (r ≥ 0.40)", "", "| Metric | r | N |", "|---|---:|---:|"]
    for _, r in passed.head(30).iterrows():
        md.append(f"| {r['metric']} | {r['stability_r']:.3f} | {r['n_pairs']} |")
    (OUT / "FBREF_RESULTS.md").write_text("\n".join(md) + "\n")

    print("DONE", summary["n_pairs"], "pass", summary["n_pass_0_40"], "auto", summary["auto_shortlist_n"])


if __name__ == "__main__":
    main()
