#!/usr/bin/env python3
"""Merge Big5 cache + feeder parquets → inbound pairs → full-category success.

Uses the 26-trait Step-2 shortlist (Attacking/Passing/Carrying/Defending/Other).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
CACHE = OUT / "fbref_broad_cache"
R_CACHE = OUT / "fbref_cache"
DECISIONS = ROOT / "decisions" / "step2_fbref.json"

MIN_PRIOR = 300.0
MIN_Y1 = 300.0

INVERT = {
    "Mis_Performance", "Dis_Performance", "Err", "Fls", "Lost_Aerial",
    "Lost_Challenges", "Tkld_Take", "Mis_Carries", "Dis_Carries",
}

# Map soccerdata-ish column fragments → our shortlist metric keys
# FBref multiindex flatten often yields names like Progressive_PrgP, Touches_Def Pen, etc.
COL_ALIASES = {
    "Def_Pen_Touches": ["Touches_Def Pen", "Def Pen", "Def_Pen_Touches", "Touches_Def_Pen"],
    "PrgC_Progression": ["Progressive_PrgC", "PrgC", "PrgC_Progression", "Carries_PrgC"],
    "PrgDist_Total": ["Total_PrgDist", "PrgDist", "PrgDist_Total", "Total_PrgDist"],
    "xG_Per": ["Expected_xG", "Per 90 Minutes_xG", "xG_Per", "xG"],
    "PrgR_Receiving": ["Progressive_PrgR", "Receptions_PrgR", "PrgR_Receiving", "PrgR"],
    "KP": ["KP", "Pass Types_KP", "Expected_KP"],
    "Att_3rd_Touches": ["Touches_Att 3rd", "Att 3rd", "Att_3rd_Touches"],
    "Clr": ["Clr", "Blocks_Clr", "Int_Clr"],
    "Gls_Standard": ["Performance_Gls", "Gls", "Gls_Standard"],
    "Succ_Take": ["Take-Ons_Succ", "Succ", "Succ_Take"],
    "Tkld_Take": ["Take-Ons_Tkld", "Tkld", "Tkld_Take"],
    "Won_Aerial": ["Aerial Duels_Won", "Won", "Won_Aerial"],
    "Final_Third": ["Final Third", "Final_Third", "01/03/00"],  # sometimes weird
    "Att_Short": ["Short_Att", "Att_Short"],
    "Sh_Blocks": ["Blocks_Sh", "Sh", "Sh_Blocks"],
    "Cmp_percent_Medium": ["Medium_Cmp%", "Cmp_percent_Medium", "Medium_Cmp_pct"],
    "Mis_Carries": ["Carries_Mis", "Mis", "Mis_Carries"],
    "CrsPA": ["CrsPA", "Pass Types_CrsPA"],
    "Int": ["Int", "Int_Int"],
    "Lost_Aerial": ["Aerial Duels_Lost", "Lost", "Lost_Aerial"],
    "Crs": ["Crs", "Pass Types_Crs"],
    "Fld": ["Performance_Fld", "Fld"],
    "Won_percent_Aerial": ["Aerial Duels_Won%", "Won%", "Won_percent_Aerial"],
    "Def_3rd_Tackles": ["Tackles_Def 3rd", "Def 3rd", "Def_3rd_Tackles"],
    "Tkl_percent_Challenges": ["Challenges_Tkl%", "Tkl%", "Tkl_percent_Challenges"],
    "Recov": ["Performance_Recov", "Recov"],
}


def end_year(code: str) -> int:
    return 2000 + int(code[2:4])


def pick_col(df: pd.DataFrame, aliases: list[str]) -> str | None:
    cols = list(df.columns)
    for a in aliases:
        if a in cols:
            return a
    # fuzzy contains
    for a in aliases:
        for c in cols:
            if a.lower().replace("_", " ") in str(c).lower().replace("_", " "):
                return c
    return None


def load_big5_standard() -> pd.DataFrame:
    frames = []
    for path in sorted(R_CACHE.glob("standard_*.csv")):
        year = int(path.stem.split("_")[1])
        df = pd.read_csv(path, low_memory=False)
        frames.append(df.assign(season_end=year, league_key=df["Comp"].astype(str)))
    out = pd.concat(frames, ignore_index=True)
    out["player"] = out["Player"].astype(str)
    out["name_key"] = out["player"].str.strip().str.lower()
    mins = pd.to_numeric(out.get("Min_Playing", out.get("Min")), errors="coerce")
    out["minutes"] = mins
    out["is_bl"] = out["Comp"].astype(str).str.contains("Bundesliga", case=False, na=False) & ~out["Comp"].astype(str).str.contains("2.", regex=False, na=False)
    return out


def load_feeder_frames() -> pd.DataFrame:
    """Stack feeder parquets; keep player/minutes/league/season + raw cols."""
    rows = []
    for pq in sorted(CACHE.glob("*.parquet")):
        if pq.name == "manifest.csv":
            continue
        # name: LEAGUE_season_stat.parquet
        m = re.match(r"(.+)_(\d{4})_(.+)\.parquet", pq.name)
        if not m:
            continue
        league, season, stat = m.group(1).replace("_", "-"), m.group(2), m.group(3)
        # fix league name dashes
        league = pq.name.rsplit("_", 2)[0].replace("_", "-")
        # better parse: NED-Eredivisie_2324_passing
        parts = pq.stem.split("_")
        season = parts[-2]
        stat = parts[-1]
        league = "_".join(parts[:-2]).replace("_", "-")
        # NED-Eredivisie style: first join with -
        if parts[0] in {"NED", "AUT", "POR", "BEL", "ENG", "GER"}:
            league = parts[0] + "-" + "-".join(parts[1:-2]).replace("-", " ")
            # fix known
            league_map = {
                "NED-Eredivisie": "NED-Eredivisie",
                "AUT-Bundesliga": "AUT-Bundesliga",
                "POR-Primeira-Liga": "POR-Primeira Liga",
                "BEL-Pro-League": "BEL-Pro League",
            }
            key = parts[0] + "-" + "-".join(parts[1:-2])
            league = league_map.get(key, key.replace("-", " ", 1) if False else key)
            # simpler: from known FEEDERS pattern in filename
            for feed in ["NED-Eredivisie", "AUT-Bundesliga", "POR-Primeira_Liga", "BEL-Pro_League"]:
                if pq.name.startswith(feed.replace(" ", "_")) or pq.name.startswith(feed):
                    league = feed.replace("_", " ") if "Primeira" in feed or "Pro" in feed else feed
            if "NED-Eredivisie" in pq.name:
                league = "NED-Eredivisie"
            elif "AUT-Bundesliga" in pq.name:
                league = "AUT-Bundesliga"
            elif "POR-Primeira" in pq.name:
                league = "POR-Primeira Liga"
            elif "BEL-Pro" in pq.name:
                league = "BEL-Pro League"

        df = pd.read_parquet(pq)
        df["league_key"] = league
        df["season_end"] = end_year(season)
        df["stat_type"] = stat
        # player col
        pcol = "Player" if "Player" in df.columns else ("player" if "player" in df.columns else None)
        if pcol is None:
            continue
        df["player"] = df[pcol].astype(str)
        df["name_key"] = df["player"].str.strip().str.lower()
        # minutes
        for c in ["Playing Time_Min", "Min", "Playing Time Min", "Min_Playing"]:
            if c in df.columns:
                df["minutes"] = pd.to_numeric(df[c], errors="coerce")
                break
        if "minutes" not in df.columns:
            df["minutes"] = np.nan
        rows.append(df)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def main():
    short = json.loads(DECISIONS.read_text())["shortlist"]
    print("shortlist", len(short))

    big5 = load_big5_standard()
    print("big5", len(big5), "BL", big5["is_bl"].sum())

    feed = load_feeder_frames()
    print("feeder rows", len(feed), "files", len(list(CACHE.glob('*.parquet'))))

    # First BL season from big5
    bl = big5[big5["is_bl"]].copy()
    first = bl.sort_values("season_end").groupby("name_key", as_index=False).first()
    first = first.rename(columns={"season_end": "first_bl_season", "minutes": "y1_minutes", "Comp": "y1_comp", "Squad": "y1_squad"})
    first = first[first["y1_minutes"] >= MIN_Y1]
    print("first BL with min", len(first))

    # Prior from feeders OR big5 non-BL
    big5_prior = big5[~big5["is_bl"]].copy()
    # For each player, take latest prior season before first BL with enough minutes
    pairs = []
    feed_by_name = feed.groupby("name_key") if len(feed) else None

    for _, row in first.iterrows():
        nk = row["name_key"]
        fb_season = row["first_bl_season"]
        # candidates from big5 non-bl
        cands = big5_prior[(big5_prior["name_key"] == nk) & (big5_prior["season_end"] < fb_season) & (big5_prior["minutes"] >= MIN_PRIOR)]
        # feeder candidates (any stat row — use max minutes that season)
        if feed_by_name is not None and nk in feed_by_name.groups:
            fsub = feed_by_name.get_group(nk)
            fsub = fsub[(fsub["season_end"] < fb_season) & (fsub["minutes"].fillna(0) >= MIN_PRIOR)]
            if len(fsub):
                # collapse to season with max minutes
                fsea = fsub.sort_values("minutes", ascending=False).groupby("season_end", as_index=False).first()
                for _, fr in fsea.iterrows():
                    cands = pd.concat([cands, pd.DataFrame([{
                        "name_key": nk,
                        "season_end": fr["season_end"],
                        "minutes": fr["minutes"],
                        "league_key": fr["league_key"],
                        "player": fr["player"],
                        "source": "feeder",
                    }])], ignore_index=True)

        if cands.empty:
            continue
        # latest prior season
        cands = cands.sort_values(["season_end", "minutes"], ascending=[False, False])
        prior = cands.iloc[0]
        pairs.append({
            "name_key": nk,
            "player": row["player"],
            "first_bl_season": fb_season,
            "y1_minutes": row["y1_minutes"],
            "prior_season": prior["season_end"],
            "prior_minutes": prior["minutes"],
            "prior_league": prior.get("league_key", prior.get("Comp", "Unknown")),
        })

    pairs_df = pd.DataFrame(pairs)
    print("pairs", len(pairs_df))
    pairs_df.to_csv(OUT / "fbref_expanded_pairs.csv", index=False)

    # Success: for each shortlist trait, need prior values — only from Big5 wide for now if feeder lacks cols
    # Reuse existing primary panel / explorer approach: run spearman on traits available in Big5 panel for expanded pair set
    # Filter Big5 primary panel-like from R output if names match

    # Build trait success from Big5 R wide metrics for players in pairs_df (name match)
    # Load all Big5 metric tables is heavy — use fbref_primary + stability shortlist from existing R pairs join

    # Simpler path: restrict pairs to those with Big5 prior (full metrics), report how many gained from feeders
    big5_only = pairs_df[~pairs_df["prior_league"].astype(str).str.contains("NED|AUT|POR|BEL", case=False, na=False)]
    feeder_only = pairs_df[pairs_df["prior_league"].astype(str).str.contains("NED|AUT|POR|BEL", case=False, na=False)]
    print("pairs big5 prior", len(big5_only), "feeder prior", len(feeder_only))

    summary = {
        "n_pairs": int(len(pairs_df)),
        "n_feeder_prior": int(len(feeder_only)),
        "n_big5_prior": int(len(big5_only)),
        "min_prior": MIN_PRIOR,
        "min_y1": MIN_Y1,
        "feeder_files": len(list(CACHE.glob("*.parquet"))),
        "note": "Full-category success requires feeder advanced cols mapped; Big5 priors keep full shortlist.",
    }
    (OUT / "fbref_expand_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
