#!/usr/bin/env python3
"""SAFE feeder expand — few leagues, sequential, cached, long pauses.

Only scrapes standard + misc (soccerdata). Enough to enlarge N for aerial /
volume traits. Does NOT pull passing/defense/possession (avoids chromote crash).

Usage:
  python3 scripts/run_feeder_expand_safe.py
"""
from __future__ import annotations

import time
import traceback
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
CACHE = OUT / "fbref_broad_cache"
CACHE.mkdir(parents=True, exist_ok=True)

# Keep this SHORT — each league×season is a live scrape
FEEDERS = [
    "NED-Eredivisie",
    "AUT-Bundesliga",
    "POR-Primeira Liga",
]
SEASONS = ["1819", "1920", "2021", "2122", "2223", "2324", "2425"]
STAT_TYPES = ["standard", "misc"]  # soccerdata-supported only
PAUSE_SEC = 4.0


def end_year(code: str) -> int:
    return 2000 + int(code[2:4])


def scrape(league: str, season: str, stat: str) -> pd.DataFrame | None:
    import soccerdata as sd

    pq = CACHE / f"{league.replace(' ', '_').replace('.', '')}_{season}_{stat}.parquet"
    if pq.exists() and pq.stat().st_size > 500:
        print(f"  cache {pq.name}")
        return pd.read_parquet(pq)
    print(f"  SCRAPE {league} {season} {stat}", flush=True)
    try:
        fb = sd.FBref(leagues=league, seasons=season)
        df = fb.read_player_season_stats(stat_type=stat)
        if df is None or len(df) == 0:
            return None
        df = df.reset_index()
        df.to_parquet(pq, index=False)
        time.sleep(PAUSE_SEC)
        return df
    except Exception as e:
        print(f"    fail: {e}")
        traceback.print_exc()
        time.sleep(PAUSE_SEC)
        return None


def main():
    n_ok = 0
    for league in FEEDERS:
        for season in SEASONS:
            for stat in STAT_TYPES:
                df = scrape(league, season, stat)
                if df is not None:
                    n_ok += 1
                    print(f"    rows={len(df)}")
    print(f"\nDone. Cached frames ok={n_ok}. Next: merge into Big5 rebuild (optional).")
    print("For primary-trait p-values on Big5 alone, run Rscript + run_primary_success.py first.")


if __name__ == "__main__":
    main()
