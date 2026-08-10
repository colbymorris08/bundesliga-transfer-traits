#!/usr/bin/env python3
"""Slim FBref caches to BL inbound players (+ all 1.BL peers for percentiles).

- Big5 CSVs → results/fbref_cache_slim/ (Bundesliga rows + inbound URLs elsewhere)
- Feeder parquets → results/fbref_inbound_feeder_slim/ (name-matched inbounds only)
Optionally deletes fat originals after successful write (--delete-originals).
"""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
ROSTER = OUT / "fbref_inbound_roster.csv"
BIG5 = OUT / "fbref_cache"
BIG5_SLIM = OUT / "fbref_cache_slim"
BROAD = OUT / "fbref_broad_cache"
BROAD_SLIM = OUT / "fbref_inbound_feeder_slim"


def is_bl1(comp: str) -> bool:
    c = str(comp)
    return ("Bundesliga" in c) and ("2." not in c)


def norm_name(s: str) -> str:
    s = str(s).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def load_inbound() -> tuple[set[str], set[str]]:
    r = pd.read_csv(ROSTER)
    urls = set(r["Url"].astype(str))
    names = set(r["name_key"].astype(str).map(norm_name))
    # also from pairs
    pairs = OUT / "fbref_inbound_pairs.csv"
    if pairs.exists():
        p = pd.read_csv(pairs)
        urls |= set(p["player_id"].astype(str))
        names |= set(p["player"].astype(str).map(norm_name))
    return urls, names


def slim_big5(urls: set[str]) -> int:
    BIG5_SLIM.mkdir(parents=True, exist_ok=True)
    kept = 0
    for path in sorted(BIG5.glob("*.csv")):
        df = pd.read_csv(path, low_memory=False)
        if "Url" not in df.columns or "Comp" not in df.columns:
            shutil.copy2(path, BIG5_SLIM / path.name)
            continue
        mask = df["Comp"].map(is_bl1) | df["Url"].astype(str).isin(urls)
        slim = df.loc[mask].copy()
        slim.to_csv(BIG5_SLIM / path.name, index=False)
        kept += len(slim)
        print(f"  {path.name}: {len(df)} → {len(slim)}")
    return kept


def player_col(df: pd.DataFrame) -> str | None:
    for c in df.columns:
        cl = str(c).lower()
        if cl in {"player", "player_player"} or cl.endswith("_player") or "player" == cl:
            return c
        if isinstance(c, str) and c.lower() == "player":
            return c
    # multiindex flatten leftovers
    for c in df.columns:
        if "player" in str(c).lower() and "nation" not in str(c).lower():
            return c
    return None


def slim_broad(names: set[str]) -> int:
    BROAD_SLIM.mkdir(parents=True, exist_ok=True)
    kept_files = 0
    for pq in sorted(BROAD.glob("*.parquet")):
        if pq.name.startswith("GER-Bundesliga"):
            # leftover BL scrapes — skip or keep as peer? Prefer Big5 BL.
            continue
        try:
            df = pd.read_parquet(pq)
        except Exception as e:
            print(f"  skip {pq.name}: {e}")
            continue
        pc = player_col(df)
        if not pc:
            print(f"  no player col {pq.name} cols={list(df.columns)[:8]}")
            continue
        keys = df[pc].astype(str).map(norm_name)
        slim = df.loc[keys.isin(names)].copy()
        if len(slim) == 0:
            # still write empty? skip to save space
            print(f"  {pq.name}: {len(df)} → 0 (drop)")
            continue
        out = BROAD_SLIM / pq.name
        slim.to_parquet(out, index=False)
        kept_files += 1
        print(f"  {pq.name}: {len(df)} → {len(slim)}")
    return kept_files


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--delete-originals", action="store_true")
    args = ap.parse_args()

    if not ROSTER.exists():
        raise SystemExit("Run build_inbound_roster.py first")

    urls, names = load_inbound()
    print(f"Inbound URLs={len(urls)} names={len(names)}")

    print("Slimming Big5…")
    slim_big5(urls)
    print("Slimming feeder parquets…")
    n = slim_broad(names)
    print(f"Feeder slim files kept: {n}")

    if args.delete_originals:
        # delete fat Big5 originals (replaced by slim)
        for p in BIG5.glob("*.csv"):
            p.unlink()
        # delete fat feeder league parquets
        for p in BROAD.glob("*.parquet"):
            p.unlink()
        print("Deleted originals (use fbref_cache_slim / fbref_inbound_feeder_slim)")

    print("Done.")


if __name__ == "__main__":
    main()
