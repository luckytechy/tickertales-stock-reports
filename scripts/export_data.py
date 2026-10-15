"""Write one clean data file per report for the Ticker Tales website (StockSense).

docs/data/<TICKER>.json  - everything a website needs to show the report:
    facts (verified market numbers), analysis (the written sections),
    charts (raw date/value points) and when it was generated.
docs/data/index.json     - a list of every report, for the StockSense home grid.

Both are served publicly by GitHub Pages, e.g.
https://luckytechy.github.io/tickertales-stock-reports/data/index.json
"""
import argparse, glob, json, os
from datetime import datetime, timezone

SCHEMA_VERSION = 1


def slugify(ticker):
    """Same rule as the website's slugify: M&M -> m-and-m, BAJAJ-AUTO -> bajaj-auto."""
    import re
    s = ticker.lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", help="report to export; omit with --index-only")
    ap.add_argument("--index-only", action="store_true", help="just rebuild index.json from the files present")
    ap.add_argument("--build", default="build")
    ap.add_argument("--out", default="docs/data")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    if a.index_only:
        n = build_index(a.out)
        print(f"Index rebuilt ({n} reports)")
        return
    load = lambda n: json.load(open(os.path.join(a.build, n)))
    facts, analysis = load("facts.json"), load("analysis.json")
    charts = load("charts.json") if os.path.exists(os.path.join(a.build, "charts.json")) else {}
    tk = a.ticker.upper()
    # No quality rating on StockSense.
    analysis.pop("quality", None)
    analysis.pop("quality_why", None)

    report = {
        "schema_version": SCHEMA_VERSION,
        "ticker": tk,
        "slug": slugify(tk),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data_as_of": facts.get("last_date"),
        "has_narrative": not str(analysis.get("whats_happening", "")).startswith("Not generated"),
        "facts": facts,
        "analysis": analysis,
        "charts": charts,
    }
    json.dump(report, open(os.path.join(a.out, f"{tk}.json"), "w"), indent=2)
    n = build_index(a.out)
    print(f"Exported {tk} ({n} reports in index)")


def build_index(out):
    items = []
    for f in sorted(glob.glob(os.path.join(out, "*.json"))):
        if os.path.basename(f) == "index.json":
            continue
        r = json.load(open(f))
        fx, an = r.get("facts", {}), r.get("analysis", {})
        if an.pop("quality", None) is not None or an.pop("quality_why", None) is not None:
            json.dump(r, open(f, "w"), indent=2)  # strip ratings from older reports
        items.append({
            "ticker": r["ticker"],
            "slug": slugify(r["ticker"]),
            "one_liner": an.get("one_liner"),
            "tags": an.get("tags", []),
            "last_close": fx.get("last_close"),
            "return_1y_pct": (fx.get("returns_pct", {}).get("1Y") or {}).get("stock"),
            "dividend_yield_pct": fx.get("dividend_yield_pct"),
            "data_as_of": r.get("data_as_of"),
            "generated_at": r.get("generated_at"),
            "has_narrative": r.get("has_narrative"),
        })
    json.dump({"schema_version": SCHEMA_VERSION, "count": len(items),
               "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "reports": items}, open(os.path.join(out, "index.json"), "w"), indent=2)
    return len(items)


if __name__ == "__main__":
    main()
