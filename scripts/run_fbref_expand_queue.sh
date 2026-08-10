#!/bin/bash
# Run FBref feeder scrapes ONE LEAGUE AT A TIME until queue is done.
set -euo pipefail
cd "$(dirname "$0")/.."
LOG=results/fbref_broad_cache/scrape_log.txt
mkdir -p results/fbref_broad_cache

QUEUE=(
  "GER-2.Bundesliga"
  "NED-Eredivisie"
  "AUT-Bundesliga"
  "POR-Primeira Liga"
  "BEL-Pro League"
  "ENG-Championship"
  "SUI-Super League"
  "TUR-Super Lig"
  "DEN-Superliga"
  "SCO-Premiership"
)

echo "==== FBref one-league queue start $(date) ====" | tee -a "$LOG"
for L in "${QUEUE[@]}"; do
  echo "" | tee -a "$LOG"
  echo ">>>> START LEAGUE: $L $(date)" | tee -a "$LOG"
  if python3 -u scripts/run_fbref_one_league.py "$L" >> "$LOG" 2>&1; then
    echo ">>>> OK LEAGUE: $L $(date)" | tee -a "$LOG"
  else
    echo ">>>> FAIL LEAGUE: $L (continuing to next) $(date)" | tee -a "$LOG"
  fi
  # cool-down between leagues
  sleep 15
done
echo "==== FBref queue finished $(date) ====" | tee -a "$LOG"
