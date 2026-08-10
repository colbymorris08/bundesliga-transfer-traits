#!/bin/bash
# Periodically wipe soccerdata FBref HTML cache so long scrapes don't fill the disk.
# Parquets in results/fbref_broad_cache are the durable cache.
set -uo pipefail
cd "$(dirname "$0")/.."
LOG=results/fbref_broad_cache/cache_janitor.log
HTML=/Users/colbymorris/soccerdata/data/FBref

echo "cache_janitor start $(date)" >> "$LOG"
while true; do
  # Stop if queue finished
  if [[ -f results/fbref_broad_cache/queue_progress.json ]]; then
    if python3 - <<'PY'
import json
from pathlib import Path
s = json.loads(Path('results/fbref_broad_cache/queue_progress.json').read_text())
q, res = s.get('queue') or [], s.get('results') or []
raise SystemExit(0 if q and len(res) >= len(q) else 1)
PY
    then
      echo "cache_janitor: queue done $(date)" >> "$LOG"
      break
    fi
  fi

  # Stop if supervisor gone
  if ! pgrep -f 'run_fbref_supervisor\.sh' >/dev/null 2>&1; then
    echo "cache_janitor: supervisor gone $(date)" >> "$LOG"
    break
  fi

  if [[ -d "$HTML" ]]; then
    used=$(du -sm "$HTML" 2>/dev/null | awk '{print $1}')
    free=$(df -m /System/Volumes/Data | awk 'NR==2{print $4}')
    if [[ "${used:-0}" -gt 200 ]] || [[ "${free:-9999}" -lt 1500 ]]; then
      rm -rf "$HTML"/*
      echo "cache_janitor: cleared FBref HTML used=${used}MB free=${free}MB $(date)" >> "$LOG"
    fi
  fi
  sleep 300
done
