# Ticker Tales - StockSense reports

Generates the plain-English Nifty 100 reports shown on
[tickertales.in/stocksense](https://www.tickertales.in/stocksense).

Each report is a JSON file in `docs/data/`, served by GitHub Pages. The website
reads them from there and shows them on the matching company card.

## How it runs

**Nightly (automatic)** - `.github/workflows/nightly.yml`, 01:11 IST.
1. Refreshes any published report whose company announced quarterly results
   3+ days ago (results dates come from Yahoo's earnings calendar; if none is
   found, a report older than 100 days is refreshed anyway).
2. Fills the remaining slots with the next companies in `queue/nifty100.json`.
3. Tells tickertales.in to refresh, so new reports show straight away.

Stocks per night: repo variable `STOCKS_PER_NIGHT` (Settings -> Secrets and
variables -> Actions -> Variables). Default 3. Raise it during results season.

**On demand** - Actions -> *Generate Stock Report* -> enter a ticker. The peer
defaults to the one in the queue file.

If Claude can't write the analysis (usage limit, outage), nothing is
published for that stock - it is retried the next night.

## Files

```
queue/nifty100.json        build order + comparison peer for each company
scripts/plan_nightly.py    picks tonight's stocks (refreshes first, then new)
scripts/run_report.sh      fetch data -> write analysis -> export JSON
scripts/fetch_data.py      market data and charts (deterministic)
scripts/write_analysis.py  the written sections, via Claude
scripts/export_data.py     docs/data/<TICKER>.json + index.json
scripts/notify_site.sh     waits for Pages, then pings the site refresh hook
docs/data/                 published data - do not edit by hand
```

Keep `queue/nifty100.json` in step with `src/lib/nifty100.ts` on the website
when NSE reshuffles the index (March and September).

## Disclaimer

Generated automatically and may contain errors. Not investment advice. The
author is not a SEBI-registered Investment Adviser.
