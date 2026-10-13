#!/usr/bin/env bash
# Build one StockSense report and write it into docs/data/ for the website.
#   bash scripts/run_report.sh TICKER [PEER]
# Fails (and publishes nothing) if Claude could not write the analysis, so a
# usage limit or outage never replaces a good report with a data-only one.
set -euo pipefail
T="$(echo "$1" | tr '[:lower:]' '[:upper:]' | tr -d ' ' | sed 's/\.NS$//')"
PEER="${2:-}"

rm -rf build && mkdir -p build
python scripts/fetch_data.py "$T" ${PEER:+--peer "$PEER"} --out build/
python scripts/write_analysis.py --facts build/facts.json --out build/

if python -c "import json,sys; a=json.load(open('build/analysis.json')); sys.exit(0 if str(a.get('whats_happening','')).startswith('Not generated') else 1)"; then
  echo "::error::No written analysis for $T (Claude step failed). Not publishing."
  exit 1
fi

python scripts/export_data.py --ticker "$T" --build build/ --out docs/data/

# Keep a running log of Claude usage per report.
mkdir -p logs
[ -f logs/usage.csv ] || echo "date,ticker,model,input,output,cache_read,cache_write,total,turns,seconds,api_equiv_usd" > logs/usage.csv
python - "$T" >> logs/usage.csv <<'PY'
import json, os, sys, datetime
u = json.load(open("build/usage.json")) if os.path.exists("build/usage.json") else {}
g = lambda k: u.get(k, "")
print(",".join(str(x) for x in [datetime.date.today(), sys.argv[1], (g("model") or "").replace(",", "+"),
      g("input_tokens"), g("output_tokens"), g("cache_read_input_tokens"), g("cache_creation_input_tokens"),
      g("total_tokens"), g("turns"), g("duration_s"), g("api_equivalent_usd")]))
PY
