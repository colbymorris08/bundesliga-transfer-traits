#!/usr/bin/env python3
"""Durable FBref feeder expand: ONE league at a time until every BL-feeder option is done.

Skips GER-Bundesliga (destination). Big-5 1st tiers already live in results/fbref_cache/;
we still scrape 2nd tiers + non-Big-5 leagues that commonly feed the Bundesliga.

Resume-safe: skips season/stat parquet files that already exist.
"""
from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_feeder_expand_full import CACHE, PAUSE, SEASONS, STAT_TYPES, patch_soccerdata, scrape_one  # noqa: E402

PROGRESS = CACHE / "queue_progress.json"
LOG = CACHE / "scrape_log.txt"

# Ordered by typical Bundesliga inbound volume / value
PRIORITY = [
    "NED-Eredivisie",       # already partially cached — finish first
    "AUT-Bundesliga",
    "POR-Primeira Liga",
    "BEL-Pro League",
    "SUI-Super League",
    "GER-2.Bundesliga",     # often CAPTCHA-heavy — after warm leagues
    "TUR-Super Lig",
    "ENG-Championship",
    "FRA-Ligue 2",
    "ESP-Segunda",
    "ITA-Serie B",
    "DEN-Superliga",
    "POL-Ekstraklasa",
    "CZE-First League",
    "CRO-Football League",
    "GRE-Super League",
    "SCO-Premiership",
    "SWE-Allsvenskan",
    "NOR-Eliteserien",
    "USA-MLS",
    "MEX-Liga MX",
    "RUS-Premier League",
    "UKR-Premier League",
]

SKIP = {
    "GER-Bundesliga",  # destination
    # Top Big-5 already in worldfootballR Big5 dump (results/fbref_cache)
    "ENG-Premier League",
    "ESP-La Liga",
    "ITA-Serie A",
    "FRA-Ligue 1",
    # Tournament pages often break season scrape
    "INT-World Cup",
    "INT-European Championship",
}


def load_league_dict() -> list[str]:
    paths = [
        Path("/Users/colbymorris/soccerdata/config/league_dict.json"),
        Path("/opt/homebrew/lib/python3.13/site-packages/soccerdata/config/league_dict.json"),
    ]
    keys: list[str] = []
    for p in paths:
        if p.exists():
            keys = sorted(json.loads(p.read_text()).keys())
            break
    # priority first, then any remaining from dict
    ordered = [L for L in PRIORITY if L not in SKIP]
    for L in keys:
        if L not in SKIP and L not in ordered:
            ordered.append(L)
    return ordered


def safe_name(league: str) -> str:
    return league.replace(" ", "_").replace(".", "")


def league_progress(league: str) -> tuple[int, int]:
    safe = safe_name(league)
    need = len(SEASONS) * len(STAT_TYPES)
    have = 0
    for season in SEASONS:
        for stat in STAT_TYPES:
            pq = CACHE / f"{safe}_{season}_{stat}.parquet"
            if pq.exists() and pq.stat().st_size > 2000:
                have += 1
    return have, need


def save_progress(state: dict) -> None:
    PROGRESS.write_text(json.dumps(state, indent=2))


def log(msg: str) -> None:
    line = msg if msg.endswith("\n") else msg + "\n"
    print(line, end="", flush=True)
    with LOG.open("a") as f:
        f.write(line)


def scrape_league(league: str) -> dict:
    have0, need = league_progress(league)
    if have0 >= need:
        log(f"SKIP (complete) {league} {have0}/{need}")
        return {"league": league, "status": "already_done", "ok": have0, "fail": 0, "need": need}

    log(f"\n>>>> START {league} ({have0}/{need} cached) {time.strftime('%Y-%m-%d %H:%M:%S')}")
    ok = fail = 0
    for season in SEASONS:
        for stat in STAT_TYPES:
            try:
                path = scrape_one(league, season, stat)
                if path:
                    ok += 1
                else:
                    fail += 1
            except Exception as e:
                fail += 1
                log(f"    EXC {league} {season} {stat}: {e}")
                traceback.print_exc()
            time.sleep(1)
    have1, _ = league_progress(league)
    status = "done" if have1 >= need else "partial"
    log(f">>>> {status.upper()} {league}: ok={ok} fail={fail} files={have1}/{need}")
    time.sleep(12)  # cool-down between leagues
    return {"league": league, "status": status, "ok": ok, "fail": fail, "have": have1, "need": need}


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    patch_soccerdata()
    queue = load_league_dict()
    log(f"\n==== FULL FEEDER QUEUE ({len(queue)} leagues) {time.strftime('%Y-%m-%d %H:%M:%S')} ====")
    log("Queue: " + " → ".join(queue))

    state = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "results": [], "queue": queue}
    save_progress(state)

    for i, league in enumerate(queue, 1):
        log(f"\n--- [{i}/{len(queue)}] ---")
        try:
            res = scrape_league(league)
        except Exception as e:
            res = {"league": league, "status": "fatal", "error": str(e)}
            log(f">>>> FATAL {league}: {e}")
            traceback.print_exc()
            time.sleep(20)
        state["results"].append(res)
        state["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        save_progress(state)

    log(f"\n==== ALL LEAGUES FINISHED {time.strftime('%Y-%m-%d %H:%M:%S')} ====")
    done = sum(1 for r in state["results"] if r.get("status") in ("done", "already_done"))
    partial = sum(1 for r in state["results"] if r.get("status") == "partial")
    log(f"Summary: done={done} partial={partial} total={len(state['results'])}")
    save_progress(state)


if __name__ == "__main__":
    main()
