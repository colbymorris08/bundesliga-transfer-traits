#!/usr/bin/env python3
"""Scrape remaining feeder leagues with a hard ~3GB footprint.

Strategy:
  - Scrape one league×season×stat at a time (subprocess timeout)
  - Immediately keep ONLY inbound-roster player rows
  - Write slim parquet to results/fbref_inbound_feeder_slim/
  - Delete temp full parquet + wipe soccerdata FBref HTML after each request
  - Abort if tracked dirs exceed MAX_BYTES (default 3 GiB)
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
import traceback
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_feeder_expand_full import PAUSE, SEASONS, STAT_TYPES, patch_soccerdata  # noqa: E402

OUT = ROOT / "results"
SLIM = OUT / "fbref_inbound_feeder_slim"
TMP = OUT / "fbref_tmp_full"
ROSTER = OUT / "fbref_inbound_roster.csv"
PAIRS = OUT / "fbref_inbound_pairs.csv"
PROGRESS = OUT / "fbref_broad_cache" / "remaining_lean_progress.json"
LOG = OUT / "fbref_broad_cache" / "remaining_lean_log.txt"
HTML_CACHE = Path("/Users/colbymorris/soccerdata/data/FBref")
WORKER = ROOT / "scripts" / "_fbref_scrape_worker.py"

MAX_BYTES = 3 * 1024**3  # 3 GiB hard ceiling for tracked dirs
TIMEOUT = 420  # CZE+ timed out at 200s; give FBref more headroom

# Queue leftovers (POL already slimmed — will skip complete cells)
REMAINING = [
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


def log(msg: str) -> None:
    line = msg if msg.endswith("\n") else msg + "\n"
    print(line, end="", flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as f:
        f.write(line)


def dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for p in path.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except OSError:
                pass
    return total


def tracked_bytes() -> int:
    return (
        dir_size(SLIM)
        + dir_size(OUT / "fbref_inbound_player_cache")
        + dir_size(TMP)
        + dir_size(HTML_CACHE)
        + dir_size(OUT / "fbref_broad_cache")
    )


def wipe_html() -> None:
    if HTML_CACHE.exists():
        for p in HTML_CACHE.iterdir():
            try:
                if p.is_dir():
                    shutil.rmtree(p, ignore_errors=True)
                else:
                    p.unlink(missing_ok=True)
            except Exception:
                pass


def safe_name(league: str) -> str:
    return league.replace(" ", "_").replace(".", "")


def load_inbound_names() -> set[str]:
    names: set[str] = set()
    if ROSTER.exists():
        r = pd.read_csv(ROSTER)
        names |= set(r["name_key"].astype(str).str.strip().str.lower())
        names |= set(r["player"].astype(str).str.strip().str.lower())
    if PAIRS.exists():
        p = pd.read_csv(PAIRS)
        names |= set(p["player"].astype(str).str.strip().str.lower())
    return names


def player_col(df: pd.DataFrame) -> str | None:
    for c in df.columns:
        if "player" in str(c).lower() and "nation" not in str(c).lower():
            return c
    return None


def slim_path(league: str, season: str, stat: str) -> Path:
    return SLIM / f"{safe_name(league)}_{season}_{stat}.parquet"


def already_slim(league: str, season: str, stat: str) -> bool:
    p = slim_path(league, season, stat)
    return p.exists() and p.stat().st_size > 500


def scrape_full(league: str, season: str, stat: str, tmp_pq: Path) -> bool:
    tmp_pq.parent.mkdir(parents=True, exist_ok=True)
    if tmp_pq.exists():
        tmp_pq.unlink()
    proc = subprocess.Popen(
        [sys.executable, "-u", str(WORKER), league, season, stat, str(tmp_pq)],
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
        log(f"    TIMEOUT {TIMEOUT}s")
        return False
    if out:
        for line in out.strip().splitlines()[-6:]:
            log(f"    | {line}")
    return proc.returncode == 0 and tmp_pq.exists() and tmp_pq.stat().st_size > 2000


def slim_and_store(tmp_pq: Path, league: str, season: str, stat: str, names: set[str]) -> int:
    df = pd.read_parquet(tmp_pq)
    pc = player_col(df)
    if pc is None:
        log(f"    no player col — drop")
        return 0
    keys = df[pc].astype(str).str.strip().str.lower()
    slim = df.loc[keys.isin(names)].copy()
    out = slim_path(league, season, stat)
    out.parent.mkdir(parents=True, exist_ok=True)
    if len(slim) == 0:
        # write tiny marker so we don't re-scrape endlessly
        slim.to_parquet(out, index=False)
        log(f"    slim 0 inbound rows (marker saved)")
        return 0
    slim.to_parquet(out, index=False)
    log(f"    slim {len(df)} → {len(slim)} → {out.name}")
    return len(slim)


def enforce_budget() -> None:
    wipe_html()
    used = tracked_bytes()
    log(f"  budget used={used/1024**3:.2f} GiB / {MAX_BYTES/1024**3:.1f} GiB")
    if used > MAX_BYTES:
        raise SystemExit(f"Over 3 GiB budget ({used} bytes) — stop")


def main() -> None:
    SLIM.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    patch_soccerdata()
    names = load_inbound_names()
    log(f"\n==== REMAINING LEAN SCRAPE {time.strftime('%Y-%m-%d %H:%M:%S')} ====")
    log(f"Leagues: {' → '.join(REMAINING)}")
    log(f"Inbound name keys: {len(names)}")
    enforce_budget()

    state = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "results": []}
    for li, league in enumerate(REMAINING, 1):
        ok = fail = skip = 0
        log(f"\n--- [{li}/{len(REMAINING)}] {league} ---")
        for season in SEASONS:
            for stat in STAT_TYPES:
                if already_slim(league, season, stat):
                    skip += 1
                    continue
                log(f"  SCRAPE {league} {season} {stat}")
                tmp = TMP / f"{safe_name(league)}_{season}_{stat}.parquet"
                try:
                    if scrape_full(league, season, stat, tmp):
                        slim_and_store(tmp, league, season, stat, names)
                        ok += 1
                    else:
                        fail += 1
                        log(f"    FAIL scrape")
                except Exception as e:
                    fail += 1
                    log(f"    EXC {e}")
                    traceback.print_exc()
                finally:
                    try:
                        tmp.unlink(missing_ok=True)
                    except Exception:
                        pass
                    wipe_html()
                    # drop any accidental full files in broad_cache
                    for junk in (OUT / "fbref_broad_cache").glob(f"{safe_name(league)}_{season}_{stat}.parquet"):
                        junk.unlink(missing_ok=True)
                time.sleep(1)
                if tracked_bytes() > MAX_BYTES * 0.9:
                    wipe_html()
                if tracked_bytes() > MAX_BYTES:
                    log("ABORT: over 3 GiB budget")
                    state["results"].append(
                        {"league": league, "status": "aborted_budget", "ok": ok, "fail": fail, "skip": skip}
                    )
                    PROGRESS.write_text(json.dumps(state, indent=2))
                    raise SystemExit(2)
        have = sum(1 for season in SEASONS for stat in STAT_TYPES if already_slim(league, season, stat))
        need = len(SEASONS) * len(STAT_TYPES)
        status = "done" if have >= need else "partial"
        log(f">>>> {status.upper()} {league}: ok={ok} fail={fail} skip={skip} files={have}/{need}")
        state["results"].append(
            {"league": league, "status": status, "ok": ok, "fail": fail, "skip": skip, "have": have, "need": need}
        )
        state["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        PROGRESS.write_text(json.dumps(state, indent=2))
        time.sleep(8)

    # cleanup temp
    shutil.rmtree(TMP, ignore_errors=True)
    wipe_html()
    enforce_budget()
    log(f"==== ALL REMAINING FINISHED {time.strftime('%Y-%m-%d %H:%M:%S')} ====")


if __name__ == "__main__":
    main()
