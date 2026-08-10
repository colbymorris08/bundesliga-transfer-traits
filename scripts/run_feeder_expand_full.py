#!/usr/bin/env python3
"""Expand FBref feeders with FULL advanced stats via soccerdata (seleniumbase).

Monkeypatches soccerdata to allow passing/possession/defense (same URL pattern).
Sequential · cached · long pause — safe for a laptop.

Usage:
  python3 scripts/run_feeder_expand_full.py
"""
from __future__ import annotations

import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
CACHE = OUT / "fbref_broad_cache"
CACHE.mkdir(parents=True, exist_ok=True)

# High-volume BL feeders — keep short
# Priority feeders for Bundesliga inbound (full category advanced stats)
FEEDERS = [
    "GER-2.Bundesliga",   # largest BL feeder — do first
    "NED-Eredivisie",
    "AUT-Bundesliga",
    "POR-Primeira Liga",
    "BEL-Pro League",
    "ENG-Championship",
]
SEASONS = ["2122", "2223", "2324", "2425"]
# Full category coverage
STAT_TYPES = ["standard", "shooting", "passing", "possession", "defense", "misc"]
PAUSE = 6.0  # slightly longer — reduce IP/CAPTCHA risk

# Patch soccerdata to accept advanced pages (URLs already work the same way)
EXTRA_STATS = ["passing", "possession", "defense", "gca", "passing_types"]


def patch_soccerdata():
    import soccerdata.fbref as fbref_mod

    orig = fbref_mod.FBref.read_player_season_stats

    def read_player_season_stats(self, stat_type: str = "standard"):
        player_stats = [
            "standard", "keeper", "shooting", "playing_time", "misc", *EXTRA_STATS
        ]
        filemask = "players_{}_{}_{}.html"
        if stat_type not in player_stats:
            raise TypeError(f"Invalid argument: stat_type should be in {player_stats}")
        if stat_type == "standard":
            page = "stats"
        elif stat_type == "playing_time":
            page = "playingtime"
        elif stat_type == "keeper":
            page = "keepers"
        else:
            page = stat_type

        from lxml import etree, html as lhtml

        seasons = self.read_seasons()
        players = []
        for (lkey, skey), season in seasons.iterrows():
            big_five = lkey == "Big 5 European Leagues Combined"
            filepath = self.data_dir / filemask.format(lkey, skey, stat_type)
            url = (
                fbref_mod.FBREF_API
                + "/".join(season.url.split("/")[:-1])
                + f"/{page}"
                + ("/players/" if big_five else "/")
                + season.url.split("/")[-1]
            )
            reader = self.get(url, filepath)
            tree = lhtml.parse(reader)
            for elem in tree.xpath("//td[@data-stat='comp_level']//span"):
                elem.getparent().remove(elem)
            if big_five:
                (html_table,) = tree.xpath(f"//table[@id='stats_{stat_type}']")
                df_table = fbref_mod._parse_table(html_table)
            else:
                (el,) = tree.xpath(f"//comment()[contains(.,'div_stats_{stat_type}')]")
                parser = etree.HTMLParser(recover=True)
                (html_table,) = etree.fromstring(el.text, parser).xpath(
                    f"//table[contains(@id, 'stats_{stat_type}')]"
                )
                df_table = fbref_mod._parse_table(html_table)
            df_table[("meta", "league")] = lkey
            df_table[("meta", "season")] = skey
            players.append(df_table)
        if not players:
            return pd.DataFrame()
        out = pd.concat(players)
        # flatten columns if MultiIndex
        if isinstance(out.columns, pd.MultiIndex):
            out.columns = [
                "_".join([str(c) for c in col if str(c) and not str(c).startswith("Unnamed")]).strip("_")
                if isinstance(col, tuple) else str(col)
                for col in out.columns
            ]
        return out.reset_index(drop=True)

    fbref_mod.FBref.read_player_season_stats = read_player_season_stats


def scrape_one(league: str, season: str, stat: str) -> Path | None:
    import os
    import signal
    import subprocess
    import sys

    safe = league.replace(" ", "_").replace(".", "")
    pq = CACHE / f"{safe}_{season}_{stat}.parquet"
    if pq.exists() and pq.stat().st_size > 2000:
        print(f"  cache {pq.name}", flush=True)
        return pq
    print(f"  SCRAPE {league} {season} {stat}", flush=True)

    TIMEOUT = 200
    worker = Path(__file__).resolve().parent / "_fbref_scrape_worker.py"
    proc = None
    try:
        # New session so we can kill the whole Chrome/selenium tree on timeout
        proc = subprocess.Popen(
            [sys.executable, "-u", str(worker), league, season, stat, str(pq)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        try:
            out, _ = proc.communicate(timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                proc.wait(timeout=5)
            except Exception:
                pass
            print(f"    TIMEOUT {TIMEOUT}s — kill worker & continue", flush=True)
            time.sleep(PAUSE)
            return None
        out = out or ""
        for line in out.strip().splitlines()[-8:]:
            print(f"    | {line}", flush=True)
        if proc.returncode == 0 and pq.exists() and pq.stat().st_size > 2000:
            print(f"    ok saved {pq.name}", flush=True)
            time.sleep(PAUSE)
            return pq
        print(f"    FAIL code={proc.returncode}", flush=True)
        time.sleep(PAUSE)
        return None
    except Exception as e:
        if proc is not None and proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except Exception:
                pass
        print(f"    FAIL: {e}", flush=True)
        traceback.print_exc()
        time.sleep(PAUSE)
        return None


def main():
    patch_soccerdata()
    ok, fail = 0, 0
    for league in FEEDERS:
        for season in SEASONS:
            for stat in STAT_TYPES:
                path = scrape_one(league, season, stat)
                if path:
                    ok += 1
                else:
                    fail += 1
    print(f"\nDONE ok={ok} fail={fail} cache={CACHE}", flush=True)
    # write manifest
    files = sorted(CACHE.glob("*.parquet"))
    pd.DataFrame({"file": [f.name for f in files], "bytes": [f.stat().st_size for f in files]}).to_csv(
        CACHE / "manifest.csv", index=False
    )
    print(f"parquet files: {len(files)}")


if __name__ == "__main__":
    main()
