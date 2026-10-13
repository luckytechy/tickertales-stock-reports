#!/usr/bin/env bash
# Tell tickertales.in that new reports are out, so they show straight away.
# Waits until GitHub Pages is serving the new index (deploys take 1-3 min),
# then calls the site's refresh endpoint. Never fails the run: worst case the
# site picks the reports up on its own within the hour.
set -uo pipefail
INDEX_URL="https://luckytechy.github.io/tickertales-stock-reports/data/index.json"
REFRESH_URL="https://www.tickertales.in/api/stocksense/refresh"

want=$(python -c "import json; print(json.load(open('docs/data/index.json'))['updated_at'])")
echo "Waiting for GitHub Pages to serve index updated_at=$want"
for i in $(seq 1 40); do
  got=$(curl -fsS "$INDEX_URL" 2>/dev/null | python -c "import json,sys; print(json.load(sys.stdin).get('updated_at',''))" 2>/dev/null || true)
  if [ "$got" = "$want" ]; then echo "Pages is live."; break; fi
  sleep 15
done

for i in 1 2 3; do
  if out=$(curl -fsS -X POST "$REFRESH_URL"); then echo "Site refreshed: $out"; exit 0; fi
  sleep 20
done
echo "::warning::Could not refresh tickertales.in - it will update on its own within the hour."
