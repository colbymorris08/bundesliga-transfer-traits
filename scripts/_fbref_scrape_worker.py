#!/usr/bin/env python3
"""Single FBref season/stat scrape worker (for subprocess timeout)."""
from __future__ import annotations

import sys
from pathlib import Path

league, season, stat, out_path = sys.argv[1:5]

# ensure project scripts importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_feeder_expand_full import patch_soccerdata  # noqa: E402
import soccerdata as sd  # noqa: E402

patch_soccerdata()
fb = sd.FBref(leagues=league, seasons=season)
df = fb.read_player_season_stats(stat_type=stat)
if df is None or len(df) < 5:
    print("empty", flush=True)
    sys.exit(2)
Path(out_path).parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(out_path, index=False)
print(f"ok:{len(df)}:{df.shape[1]}", flush=True)
