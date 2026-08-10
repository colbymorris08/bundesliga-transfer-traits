#!/usr/bin/env python3
"""Scrape FBref career stats for BL inbound players only (soccerdata/selenium).

For each player URL in fbref_inbound_roster.csv, fetch the player page once and
parse domestic league season tables for standard / shooting / passing /
possession / defense / misc. Resume-safe via per-player parquet cache.
"""
from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

OUT = ROOT / "results"
ROSTER = OUT / "fbref_inbound_roster.csv"
CACHE = OUT / "fbref_inbound_player_cache"
CACHE.mkdir(parents=True, exist_ok=True)
PROGRESS = CACHE / "progress.json"
LOG = CACHE / "scrape_log.txt"

STAT_TYPES = ["standard", "shooting", "passing", "possession", "defense", "misc"]
PAUSE = 3.0  # rate-limit; was 5s
HTML_CACHE = Path("/Users/colbymorris/soccerdata/data/FBref")
# Keep recent domestic seasons only in the saved parquet (cuts disk ~3–5×)
KEEP_SEASON_FROM = 2017


def log(msg: str) -> None:
    line = msg if msg.endswith("\n") else msg + "\n"
    print(line, end="", flush=True)
    with LOG.open("a") as f:
        f.write(line)


def load_progress() -> dict:
    if PROGRESS.exists():
        return json.loads(PROGRESS.read_text())
    return {"done": [], "failed": []}


def save_progress(state: dict) -> None:
    PROGRESS.write_text(json.dumps(state, indent=2))


def wipe_html_cache() -> None:
    if not HTML_CACHE.exists():
        return
    for p in HTML_CACHE.iterdir():
        try:
            if p.is_dir():
                import shutil

                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink(missing_ok=True)
        except Exception:
            pass


def slim_player_df(df: pd.DataFrame) -> pd.DataFrame:
    """Drop ancient / career aggregate noise to shrink stored HTML-derived tables."""
    if df.empty:
        return df
    out = df.copy()
    # prefer the main scout tables
    if "stat_type" in out.columns:
        out = out[out["stat_type"].isin(STAT_TYPES + ["playing_time"])]
    season_col = next(
        (c for c in out.columns if str(c).lower() in {"season", "season_end_year"}),
        None,
    )
    if season_col is not None:
        # FBref seasons like "2021-2022" or "2021"
        years = (
            out[season_col]
            .astype(str)
            .str.extract(r"(20\d{2})")[0]
            .astype(float)
        )
        keep = years.isna() | (years >= KEEP_SEASON_FROM)
        out = out.loc[keep]
    return out.reset_index(drop=True)


def parse_player_tables(html_path: Path, player_url: str, player_name: str) -> pd.DataFrame:
    """Parse FBref player page tables into long-form season rows."""
    from lxml import etree, html as lhtml

    tree = lhtml.parse(str(html_path))
    rows = []
    # Player pages expose tables directly (and sometimes inside HTML comments)
    table_els = tree.xpath("//table[contains(@id,'stats_')]")
    for el in tree.xpath("//comment()[contains(.,'stats_')]"):
        try:
            frag = etree.fromstring(el.text, etree.HTMLParser(recover=True))
            table_els.extend(frag.xpath("//table[contains(@id,'stats_')]"))
        except Exception:
            continue

    seen = set()
    for table in table_els:
        tid = table.get("id") or ""
        if tid in seen:
            continue
        seen.add(tid)
        stat = "other"
        for s in STAT_TYPES + ["playing_time"]:
            if f"stats_{s}" in tid:
                stat = s
                break
        try:
            df = pd.read_html(etree.tostring(table, encoding="unicode"))[0]
        except Exception:
            continue
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [
                "_".join([str(c) for c in col if str(c) and not str(c).startswith("Unnamed")]).strip("_")
                for col in df.columns
            ]
        df = df.copy()
        df["stat_type"] = stat
        df["table_id"] = tid
        df["player_url"] = player_url
        df["player"] = player_name
        season_col = next(
            (c for c in df.columns if str(c).lower() in {"season", "season_end_year"}),
            None,
        )
        if season_col:
            df = df[~df[season_col].astype(str).str.contains("Seasons|Career", case=False, na=False)]
        rows.append(df)

    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def player_urls(player_url: str) -> list[str]:
    """Root scout page first (smaller HTML); all_comps only as fallback."""
    urls = [player_url]
    if "/players/" in player_url and "/all_comps/" not in player_url:
        parts = player_url.rstrip("/").split("/")
        if len(parts) >= 2:
            name = parts[-1]
            pid = parts[-2]
            urls.append(
                f"https://fbref.com/en/players/{pid}/all_comps/{name}-Stats---All-Competitions"
            )
    return urls


def fetch_html_via_worker(url: str, html_path: Path, timeout: int = 120) -> bool:
    """Isolated Chrome UC fetch — hard-killed on hang (soccerdata rate_limit=7s + retries can stall)."""
    import os
    import signal
    import subprocess

    worker = ROOT / "scripts" / "_inbound_player_worker.py"
    html_path.parent.mkdir(parents=True, exist_ok=True)
    if html_path.exists():
        html_path.unlink(missing_ok=True)
    proc = subprocess.Popen(
        [sys.executable, "-u", str(worker), url, str(html_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    try:
        out, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        log(f"    TIMEOUT {timeout}s {url}")
        return False
    if out:
        for line in out.strip().splitlines()[-3:]:
            log(f"    | {line}")
    return proc.returncode == 0 and html_path.exists() and html_path.stat().st_size > 20000


def fetch_player(player_url: str, player_name: str, out_pq: Path, fb=None) -> bool:
    html_path = out_pq.with_suffix(".html")
    try:
        df = pd.DataFrame()
        for u in player_urls(player_url):
            log(f"    GET {u.split('/')[-1][:48]}")
            if not fetch_html_via_worker(u, html_path):
                continue
            df = parse_player_tables(html_path, player_url, player_name)
            if len(df) >= 1:
                break

        if df is None or len(df) < 1:
            log(f"  empty parse {player_name}")
            return False
        df = slim_player_df(df)
        df.to_parquet(out_pq, index=False)
        try:
            html_path.unlink(missing_ok=True)
        except Exception:
            pass
        wipe_html_cache()
        log(f"  ok {player_name} rows={len(df)} size={out_pq.stat().st_size // 1024}KB")
        return True
    except Exception as e:
        log(f"  FAIL {player_name}: {e}")
        traceback.print_exc()
        return False
    finally:
        time.sleep(PAUSE)


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--pairs-only",
        action="store_true",
        help="Only scrape the 137 Big-5 stability pairs (usually redundant)",
    )
    ap.add_argument(
        "--feeder-new-only",
        action="store_true",
        help="Scrape roster inbounds in feeder slim who are NOT in the 137 pairs",
    )
    ap.add_argument(
        "--no-big5-prior",
        action="store_true",
        help="Only players with no Big-5 prior summary (true feeder-expansion targets)",
    )
    ap.add_argument(
        "--not-in-feeder-slim",
        action="store_true",
        help="Skip players already present in fbref_inbound_feeder_slim (avoid redundant scrapes)",
    )
    ap.add_argument(
        "--min-bl-season",
        type=int,
        default=0,
        help="Only first-BL seasons >= this year (e.g. 2021 for feeder window)",
    )
    ap.add_argument("--limit", type=int, default=0, help="Optional cap")
    args = ap.parse_args()

    if not ROSTER.exists():
        raise SystemExit("Run build_inbound_roster.py first")

    roster = pd.read_csv(ROSTER)

    def load_feeder_slim_names() -> set[str]:
        slim = OUT / "fbref_inbound_feeder_slim"
        names: set[str] = set()
        for pq in slim.glob("*_standard.parquet"):
            try:
                df = pd.read_parquet(pq)
            except Exception:
                continue
            pc = next(
                (
                    c
                    for c in df.columns
                    if "player" in str(c).lower() and "nation" not in str(c).lower()
                ),
                None,
            )
            if pc is None:
                continue
            names |= set(df[pc].astype(str).str.strip().str.lower())
        return names

    if args.feeder_new_only:
        # Names present in slim feeder standard tables
        feeder_names = load_feeder_slim_names()

        pairs_path = OUT / "fbref_inbound_pairs.csv"
        pair_urls = set()
        if pairs_path.exists():
            pair_urls = set(pd.read_csv(pairs_path)["player_id"].astype(str))

        roster = roster[
            roster["name_key"].astype(str).str.strip().str.lower().isin(feeder_names)
            & ~roster["Url"].astype(str).isin(pair_urls)
            & (roster["in_stability_pairs"] != True)  # noqa: E712
        ].copy()
        # Prefer players with no Big5 prior (true expansion targets)
        roster["_no_big5"] = roster["prior_big5_summary"].isna().astype(int)
        roster = roster.sort_values(
            ["_no_big5", "first_bl_season"], ascending=[False, False]
        ).reset_index(drop=True)
    elif args.pairs_only:
        roster = roster[roster["in_stability_pairs"] == True].copy()  # noqa: E712
        roster = roster.sort_values(
            ["in_stability_pairs", "first_bl_season"], ascending=[False, False]
        ).reset_index(drop=True)
    elif args.no_big5_prior:
        roster = roster[roster["prior_big5_summary"].isna()].copy()
        roster = roster.sort_values("first_bl_season", ascending=False).reset_index(drop=True)
    else:
        # Default: expansion targets first (no Big5 prior), then newest BL seasons
        roster = roster.copy()
        roster["_no_big5"] = roster["prior_big5_summary"].isna().astype(int)
        roster = roster.sort_values(
            ["_no_big5", "first_bl_season"], ascending=[False, False]
        ).reset_index(drop=True)

    if args.min_bl_season:
        roster = roster[roster["first_bl_season"] >= args.min_bl_season].copy()

    # Drop anyone already covered by finished feeder-league slim tables
    if args.not_in_feeder_slim:
        feeder_names = load_feeder_slim_names()
        before = len(roster)
        roster = roster[
            ~roster["name_key"].astype(str).str.strip().str.lower().isin(feeder_names)
        ].copy()
        log(
            f"not-in-feeder-slim: kept {len(roster)}/{before} "
            f"(excluded {before - len(roster)} already in slim cache)"
        )

    if args.limit and args.limit > 0:
        roster = roster.head(args.limit)

    state = load_progress()
    done = set(state.get("done") or [])
    failed = set(state.get("failed") or [])

    # Skip already-cached before counting work
    def pid_of(url: str, i: int) -> str:
        return url.rstrip("/").split("/")[-2] if "/players/" in url else str(i)

    todo = []
    for i, row in roster.iterrows():
        url = str(row["Url"])
        pid = pid_of(url, int(i) if isinstance(i, int) else 0)
        out_pq = CACHE / f"{pid}.parquet"
        if out_pq.exists() and out_pq.stat().st_size > 1000:
            done.add(url)
            continue
        todo.append((i, row))
    save_progress({"done": sorted(done), "failed": sorted(failed), "updated": time.strftime("%Y-%m-%d %H:%M:%S")})

    log(
        f"\n==== INBOUND PLAYER SCRAPE {time.strftime('%Y-%m-%d %H:%M:%S')} "
        f"roster={len(roster)} todo={len(todo)} cached={len(done)} "
        f"(worker Chrome UC · root URL first · HTML wiped) ===="
    )

    for n, (i, row) in enumerate(todo, 1):
        url = str(row["Url"])
        name = str(row["player"])
        pid = pid_of(url, int(i) if isinstance(i, int) else 0)
        out_pq = CACHE / f"{pid}.parquet"

        log(f"[{n}/{len(todo)}] {name} (BL{row.get('first_bl_season','?')})")
        ok = fetch_player(url, name, out_pq)
        if ok:
            done.add(url)
            failed.discard(url)
        else:
            failed.add(url)
        state = {
            "done": sorted(done),
            "failed": sorted(failed),
            "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "todo_remaining": len(todo) - n,
        }
        save_progress(state)

    log(f"==== DONE done={len(done)} failed={len(failed)} ====")


if __name__ == "__main__":
    main()
