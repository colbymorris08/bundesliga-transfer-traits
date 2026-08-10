#!/bin/bash
# Keep FBref feeder expand alive: auto-restart if the Python job dies mid-queue.
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p results/fbref_broad_cache
LOG=results/fbref_broad_cache/supervisor.log
HB=results/fbref_broad_cache/supervisor.heartbeat

# Single-instance lock
LOCK=results/fbref_broad_cache/supervisor.lock
if [[ -f "$LOCK" ]]; then
  old=$(cat "$LOCK" 2>/dev/null || true)
  if [[ -n "${old:-}" ]] && kill -0 "$old" 2>/dev/null; then
    echo "supervisor already running pid=$old — exit" | tee -a "$LOG"
    exit 0
  fi
fi
echo $$ > "$LOCK"
trap 'rm -f "$LOCK"' EXIT

echo "supervisor start $(date) pid=$$" | tee -a "$LOG"
while true; do
  date '+%Y-%m-%d %H:%M:%S' > "$HB"

  # Stop when progress says all done
  if [[ -f results/fbref_broad_cache/queue_progress.json ]]; then
    if python3 - <<'PY'
import json
from pathlib import Path
p = Path('results/fbref_broad_cache/queue_progress.json')
s = json.loads(p.read_text())
q = s.get('queue') or []
res = s.get('results') or []
# Full pass completed (even if some leagues partial/failed)
if q and len(res) >= len(q):
    raise SystemExit(0)
raise SystemExit(1)
PY
    then
      echo "supervisor: full queue pass finished $(date)" | tee -a "$LOG"
      break
    fi
  fi

  # Avoid stacking duplicate python queue runners (match Python only, not shell echoes)
  if pgrep -f '[P]ython.*run_fbref_all_feeders\.py' >/dev/null 2>&1; then
    echo "supervisor: queue already running — wait $(date)" | tee -a "$LOG"
    sleep 60
    continue
  fi

  echo "supervisor: launching run_fbref_all_feeders.py $(date)" | tee -a "$LOG"
  python3 -u scripts/run_fbref_all_feeders.py >> results/fbref_broad_cache/scrape_log.txt 2>&1
  code=$?
  echo "supervisor: python exited code=$code $(date)" | tee -a "$LOG"
  sleep 30
done
echo "supervisor exit $(date)" | tee -a "$LOG"
