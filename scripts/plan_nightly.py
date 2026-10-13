#!/usr/bin/env python3
"""Pick tonight's StockSense work: refreshes first, then new companies.

Prints one line per stock:  TICKER PEER REASON   (PEER is '-' when none)

1. Refresh - a published report is due once the company has announced
   quarterly results AND at least RESULTS_LAG_DAYS have passed since, and the
   report was made before those results. If no results date can be found, a
   report older than STALE_DAYS is refreshed anyway as a safety net.
2. New - the next companies in queue/nifty100.json without a report yet.
"""
import argparse, glob, json, os, sys
from datetime import datetime, timedelta, timezone

RESULTS_LAG_DAYS = 3
STALE_DAYS = 100
DATA = "docs/data"
QUEUE = "queue/nifty100.json"


def parse_dt(s):
    try:
        d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def last_results_date(ticker, now):
    """Most recent past results announcement, from Yahoo's earnings calendar."""
    try:
        import yfinance as yf
        df = yf.Ticker(ticker + ".NS").get_earnings_dates(limit=8)
        if df is None or not len(df):
            return None
        past = [d.to_pydatetime() for d in df.index if d.to_pydatetime() <= now]
        past = [d if d.tzinfo else d.replace(tzinfo=timezone.utc) for d in past]
        return max(past) if past else None
    except Exception as e:
        print(f"  ! no results date for {ticker}: {e}", file=sys.stderr)
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=3)
    a = ap.parse_args()
    now = datetime.now(timezone.utc)

    queue = json.load(open(QUEUE))["companies"]
    peers = {c["ticker"]: c.get("peer") or "" for c in queue}

    published = {}
    for f in glob.glob(os.path.join(DATA, "*.json")):
        if os.path.basename(f) == "index.json":
            continue
        r = json.load(open(f))
        published[r["ticker"]] = parse_dt(r.get("generated_at"))

    due = []
    for t, made in published.items():
        rd = last_results_date(t, now)
        if rd and made and made < rd and now >= rd + timedelta(days=RESULTS_LAG_DAYS):
            due.append((rd, t, f"refresh-after-results-{rd.date()}"))
        elif not rd and made and now - made > timedelta(days=STALE_DAYS):
            due.append((made, t, "refresh-stale"))
        else:
            print(f"  {t}: up to date (results {rd.date() if rd else 'unknown'}, report {made.date() if made else '?'})", file=sys.stderr)
    due.sort()

    plan = [(t, why) for _, t, why in due]
    for c in queue:
        if len(plan) >= a.max:
            break
        if c["ticker"] not in published and c["ticker"] not in dict(plan):
            plan.append((c["ticker"], "new"))
    plan = plan[: a.max]

    if len(due) > a.max:
        print(f"::warning::{len(due)} reports are due a refresh but only {a.max} run per night - "
              "raise STOCKS_PER_NIGHT during results season.", file=sys.stderr)

    for t, why in plan:
        print(f"{t} {peers.get(t) or '-'} {why}")


if __name__ == "__main__":
    main()
