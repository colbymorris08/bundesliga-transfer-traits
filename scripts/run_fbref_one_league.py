#!/usr/bin/env python3
"""Scrape ONE FBref feeder league fully, then exit.

Run repeatedly (or via run_fbref_expand_queue.sh) — one league per process
so a crash doesn't wipe the whole queue.

Usage:
  python3 scripts/run_fbref_one_league.py GER-2.Bundesliga
  python3 scripts/run_fbref_one_league.py NED-Eredivisie
"""
from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_feeder_expand_full import (  # noqa: E402
    CACHE,
    PAUSE,
    SEASONS,
    STAT_TYPES,
    patch_soccerdata,
    scrape_one,
)

# Default queue order (biggest BL feeders first)
QUEUE = [
    "GER-2.Bundesliga",
    "NED-Eredivisie",
    "AUT-Bundesliga",
    "POR-Primeira Liga",
    "BEL-Pro League",
    "ENG-Championship",
    "SUI-Super League",
    "TUR-Super Lig",
    "DEN-Superliga",
    "SCO-Premiership",
]


def league_done(league: str) -> bool:
    safe = league.replace(" ", "_").replace(".", "")
    need = len(SEASONS) * len(STAT_TYPES)
    have = 0
    for season in SEASONS:
        for stat in STAT_TYPES:
            pq = CACHE / f"{safe}_{season}_{stat}.parquet"
            # also accept alternate naming from earlier runs
            alts = list(CACHE.glob(f"*{season}_{stat}.parquet"))
            alts = [p for p in alts if league.split("-")[0] in p.name or safe[:6] in p.name]
            if (pq.exists() and pq.stat().st_size > 2000) or any(
                p.stat().st_size > 2000 for p in alts if league.replace(" ", "_").replace(".", "") in p.name
                or league.replace("-", "_") in p.name
            ):
                # stricter: exact safe prefix
                if pq.exists() and pq.stat().st_size > 2000:
                    have += 1
                else:
                    # fuzzy match for NED-Eredivisie style
                    for p in CACHE.glob(f"*_{season}_{stat}.parquet"):
                        stem = p.stem
                        if stem.endswith(f"_{season}_{stat}") and (
                            safe in stem.replace("-", "_") or league.replace(" ", "_").replace(".", "") in stem
                        ):
                            # check league token
                            prefix = stem[: -(len(season) + len(stat) + 2)]
                            if safe.replace("-", "_") == prefix.replace("-", "_") or prefix.replace("_", "-") == league.replace(" ", "-"):
                                have += 1
                                break
    return have >= need


def scrape_league(league: str) -> tuple[int, int]:
    patch_soccerdata()
    ok = fail = 0
    print(f"\n=== LEAGUE {league} · seasons={SEASONS} · stats={STAT_TYPES} ===", flush=True)
    for season in SEASONS:
        for stat in STAT_TYPES:
            path = scrape_one(league, season, stat)
            if path:
                ok += 1
            else:
                fail += 1
            time.sleep(1)  # extra breath between calls
    print(f"=== DONE {league}: ok={ok} fail={fail} ===", flush=True)
    return ok, fail


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) > 1:
        leagues = sys.argv[1:]
    else:
        # next incomplete league in queue
        leagues = []
        for L in QUEUE:
            # quick exact check
            safe = L.replace(" ", "_").replace(".", "")
            need = len(SEASONS) * len(STAT_TYPES)
            have = sum(
                1
                for season in SEASONS
                for stat in STAT_TYPES
                if (CACHE / f"{safe}_{season}_{stat}.parquet").exists()
                and (CACHE / f"{safe}_{season}_{stat}.parquet").stat().st_size > 2000
            )
            print(f"queue {L}: {have}/{need}", flush=True)
            if have < need:
                leagues = [L]
                break
        if not leagues:
            print("All queued leagues complete.", flush=True)
            return

    for L in leagues:
        try:
            scrape_league(L)
        except Exception as e:
            print(f"FATAL {L}: {e}", flush=True)
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
