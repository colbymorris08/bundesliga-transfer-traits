#!/usr/bin/env python3
"""Build Bundesliga inbound roster from Big5 FBref dumps + existing pairs.

Inbound = first 1. Bundesliga season with minutes > 0 (not 2. Bundesliga).
Writes results/fbref_inbound_roster.csv for player-first scrapes / cache slimming.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
CACHE = OUT / "fbref_cache"
PAIRS = OUT / "fbref_inbound_pairs.csv"


def is_bl1(comp: str) -> bool:
    c = str(comp)
    return ("Bundesliga" in c) and ("2." not in c) and ("2." not in c)


def load_big5_standard() -> pd.DataFrame:
    frames = []
    for p in sorted(CACHE.glob("standard_*.csv")):
        df = pd.read_csv(p, low_memory=False)
        df["season_end"] = int(p.stem.split("_")[1])
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    alld = load_big5_standard()
    alld["Url"] = alld["Url"].astype(str)
    alld["minutes"] = pd.to_numeric(alld.get("Min_Playing"), errors="coerce").fillna(0)

    bl = alld[alld["Comp"].map(is_bl1)].copy()
    first = (
        bl.groupby("Url", as_index=False)
        .agg(first_bl_season=("season_end", "min"), player=("Player", "first"))
    )
    # minutes in first BL season
    fm = bl.merge(first[["Url", "first_bl_season"]], on="Url")
    fm = fm[fm["season_end"] == fm["first_bl_season"]]
    fm = fm.groupby("Url", as_index=False)["minutes"].sum().rename(columns={"minutes": "first_bl_minutes"})
    first = first.merge(fm, on="Url")
    first = first[first["first_bl_minutes"] >= 1].copy()

    # Y1 squad / minutes
    y1 = bl.merge(first[["Url", "first_bl_season"]], on="Url")
    y1 = y1[y1["season_end"] == y1["first_bl_season"]]
    y1 = (
        y1.sort_values("minutes", ascending=False)
        .groupby("Url", as_index=False)
        .agg(
            y1_squad=("Squad", "first"),
            y1_minutes=("minutes", "sum"),
            y1_pos=("Pos", "first"),
        )
    )
    roster = first.merge(y1, on="Url", how="left")

    # Prior comps from Big5 before first BL
    prior = alld.merge(roster[["Url", "first_bl_season"]], on="Url")
    prior = prior[(prior["season_end"] < prior["first_bl_season"]) & (~prior["Comp"].map(is_bl1))]
    prior_agg = (
        prior.groupby("Url")
        .apply(
            lambda g: "; ".join(
                f"{c}({int(m)})"
                for c, m in g.groupby("Comp")["minutes"].sum().sort_values(ascending=False).items()
            ),
            include_groups=False,
        )
        .rename("prior_big5_summary")
        .reset_index()
    )
    roster = roster.merge(prior_agg, on="Url", how="left")

    # Merge known pairs (may have cleaner prior comps / minutes gates)
    if PAIRS.exists():
        pairs = pd.read_csv(PAIRS)
        pairs["Url"] = pairs["player_id"].astype(str)
        roster["in_stability_pairs"] = roster["Url"].isin(set(pairs["Url"]))
        # Prefer pair prior info when present
        pmap = pairs.set_index("Url")
        roster["prior_comp_pairs"] = roster["Url"].map(
            lambda u: pmap.loc[u, "prior_comp"] if u in pmap.index else None
        )
        roster["prior_minutes_pairs"] = roster["Url"].map(
            lambda u: pmap.loc[u, "prior_minutes"] if u in pmap.index else None
        )
    else:
        roster["in_stability_pairs"] = False

    roster["player_id"] = roster["Url"]
    roster["name_key"] = roster["player"].str.strip().str.lower()
    roster = roster.sort_values(["first_bl_season", "player"]).reset_index(drop=True)

    out = OUT / "fbref_inbound_roster.csv"
    roster.to_csv(out, index=False)
    print(f"Wrote {out} N={len(roster)}")
    print(f"  in stability pairs: {int(roster['in_stability_pairs'].sum())}")
    print(f"  with Big5 prior rows: {int(roster['prior_big5_summary'].notna().sum())}")


if __name__ == "__main__":
    main()
