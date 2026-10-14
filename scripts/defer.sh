#!/usr/bin/env bash
# Record that a stock hit its spending cap, so the nightly run skips it for a
# week and moves on. Also logs what the stopped run cost.
#   bash scripts/defer.sh TICKER
set -euo pipefail
T="$1"
HEADER="date,ticker,model,input,output,cache_read,cache_write,total,turns,seconds,api_equiv_usd"
for attempt in 1 2 3 4 5; do
  git fetch -q origin main
  git reset -q --hard origin/main
  mkdir -p logs
  python - "$T" <<'PY'
import json, os, sys, datetime
f = "logs/deferred.json"
d = json.load(open(f)) if os.path.exists(f) else {}
e = d.get(sys.argv[1], {"times": 0})
reason = open("build/over_budget.txt").read().strip() if os.path.exists("build/over_budget.txt") else "failed"
d[sys.argv[1]] = {"last": datetime.date.today().isoformat(), "times": e["times"] + 1, "reason": reason}
json.dump(d, open(f, "w"), indent=2, sort_keys=True)
PY
  [ -f logs/usage.csv ] || echo "$HEADER" > logs/usage.csv
  if [ -s build/usage_line.csv ]; then sed "s/,$T,/,$T (over cap),/" build/usage_line.csv >> logs/usage.csv; fi
  git add logs
  git commit -q -m "Defer $T: over the spending cap"
  if git push -q origin HEAD:main; then echo "Deferred $T for 7 days."; exit 0; fi
  sleep $((attempt * 5))
done
echo "::warning::Could not record deferral for $T."
