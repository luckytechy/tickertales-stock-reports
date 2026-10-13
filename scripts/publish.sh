#!/usr/bin/env bash
# Save the report just built (by run_report.sh) to main, safely.
#   bash scripts/publish.sh "commit message"
# Starts from the latest main every time, drops this report in, and rebuilds
# the shared files (index.json, usage log) fresh - so runs that were queued
# behind each other can never clash. Retries if someone pushed in between.
set -euo pipefail
MSG="$1"
T="$(cat build/ticker.txt)"
HEADER="date,ticker,model,input,output,cache_read,cache_write,total,turns,seconds,api_equiv_usd"

for attempt in 1 2 3 4 5; do
  git fetch -q origin main
  git reset -q --hard origin/main
  cp build/report.json "docs/data/$T.json"
  python scripts/export_data.py --index-only --out docs/data/
  mkdir -p logs
  [ -f logs/usage.csv ] || echo "$HEADER" > logs/usage.csv
  if [ -s build/usage_line.csv ]; then cat build/usage_line.csv >> logs/usage.csv; fi
  git add docs/data logs
  if git diff --staged --quiet; then echo "Nothing new to publish."; exit 0; fi
  git commit -q -m "$MSG"
  if git push -q origin HEAD:main; then echo "Published $T."; exit 0; fi
  echo "Push rejected (someone published first) - retrying ($attempt)."
  sleep $((attempt * 5))
done
echo "::error::Could not publish $T after 5 attempts."
exit 1
