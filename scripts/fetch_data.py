#!/usr/bin/env python3
"""
Fetch market data for an Indian listed stock and build chart SVGs.

Everything here is deterministic and verifiable - no guessing, no LLM.
If a figure can't be fetched, it comes back as None and the page shows
"not verified" rather than a made-up number.

Usage:
    python scripts/fetch_data.py TATACOMM --peer BHARTIARTL --out build/
"""
import argparse
import json
import os
import sys

INK = "#1b1a17"
MINT = "#0a7c52"
RED = "#c0392b"
YELLOW = "#F9D55A"
BLUE = "#93C5FD"
PINK = "#F9A8B4"

PERIODS = {"3M": 91, "6M": 182, "1Y": 365, "3Y": 1095, "5Y": 1826}


def anchor_weekly(s):
    """Weekly resample that keeps the window's TRUE first observation.

    resample('W').last() takes the last value in each week, so the first
    bucket can open well above or below the window's real starting price.
    That makes a rebased chart disagree with the returns table - a bug
    that once showed a 5-year chart at +29% against a table saying +41%.
    """
    import pandas as pd
    w = s.resample("W").last().dropna()
    first = pd.Series([s.iloc[0]], index=[s.index[0]])
    w = pd.concat([first, w])
    return w[~w.index.duplicated(keep="first")].sort_index()


def load(sym):
    import yfinance as yf
    try:
        t = yf.Ticker(sym)
        h = t.history(period="max")["Close"].dropna()
        if not len(h):
            return None, None, None
        h.index = h.index.tz_localize(None)
        div = t.dividends
        if len(div):
            div.index = div.index.tz_localize(None)
        splits = t.splits
        if len(splits):
            splits.index = splits.index.tz_localize(None)
        return h, div, splits
    except Exception as e:
        print(f"  ! could not load {sym}: {e}", file=sys.stderr)
        return None, None, None


def pct(s, days, end):
    import pandas as pd
    sl = s[s.index >= end - pd.Timedelta(days=days)]
    if len(sl) < 2:
        return None
    return float((sl.iloc[-1] / sl.iloc[0] - 1) * 100)


def spark(series, label, is_first, use_weekly):
    """One timeframe sparkline panel."""
    w = anchor_weekly(series) if use_weekly else series
    lo, hi = float(w.min()), float(w.max())
    rng = (hi - lo) or 1
    n = len(w)
    pts = [(round(8 + 624 * i / (n - 1), 1), round(8 + 114 * (1 - (v - lo) / rng), 1))
           for i, v in enumerate(w.values)]
    line = "M " + " L ".join(f"{x},{y}" for x, y in pts)
    area = line + f" L {pts[-1][0]},130 L {pts[0][0]},130 Z"
    r = float((w.iloc[-1] / w.iloc[0] - 1) * 100)
    col = MINT if r > 0 else RED
    cls = "pos" if r > 0 else "neg"
    act = " active" if is_first else ""
    return f'''<div class="tfpanel{act}" id="tf{label}">
  <div class="tfhead"><div><span class="tfret {cls}">{r:+.1f}%</span><span class="tflab">{label}</span></div>
  <div class="tfrange">LOW &#8377;{lo:.0f} &middot; HIGH &#8377;{hi:.0f}</div></div>
  <svg viewBox="0 0 640 130" preserveAspectRatio="none" class="spark">
    <path d="{area}" fill="{col}" opacity=".28"/><path d="{line}" fill="none" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/>
  </svg>
  <div class="tffoot"><span>&#8377;{w.iloc[0]:.0f} &middot; {w.index[0].date()}</span><span>&#8377;{w.iloc[-1]:.0f} &middot; {w.index[-1].date()}</span></div>
</div>'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ticker", help="NSE symbol, e.g. TATACOMM")
    ap.add_argument("--peer", default=None)
    ap.add_argument("--out", default="build")
    a = ap.parse_args()

    import pandas as pd

    os.makedirs(a.out, exist_ok=True)
    tk = a.ticker.upper().replace(".NS", "")

    print(f"Fetching {tk}.NS ...")
    s, div, splits = load(tk + ".NS")
    if s is None:
        sys.exit(f"FAILED: no price data for {tk}.NS. Check the NSE symbol.")

    nifty, _, _ = load("^NSEI")
    peer, _, _ = load(a.peer.upper() + ".NS") if a.peer else (None, None, None)

    end = s.index[-1]
    px = float(s.iloc[-1])
    listed = s.index[0]
    years_listed = (end - listed).days / 365.25

    # Short-history mode: a recent IPO has no 3Y/5Y to show.
    short_history = years_listed < 3
    if short_history:
        use = {"3M": 91, "6M": 182, "1Y": 365, "ALL": 99999}
    else:
        use = {"3M": 91, "1Y": 365, "3Y": 1095, "5Y": 1826}

    # ---- timeframe panels ----
    panels = []
    for i, (lbl, d) in enumerate(use.items()):
        win = s if d > 90000 else s[s.index >= end - pd.Timedelta(days=d)]
        panels.append(spark(win, lbl, i == 0, d > 200))
    open(os.path.join(a.out, "timeframes.html"), "w").write("\n".join(panels))

    # ---- rebased comparison vs Nifty (+ peer) ----
    comp_window = listed if short_history else end - pd.Timedelta(days=1826)
    series = {}
    sw = anchor_weekly(s[s.index >= comp_window])
    series["Stock"] = sw / sw.iloc[0] * 100
    if nifty is not None:
        nw = anchor_weekly(nifty[nifty.index >= comp_window])
        series["Nifty"] = nw / nw.iloc[0] * 100
    if peer is not None:
        pw = anchor_weekly(peer[peer.index >= comp_window])
        series["Peer"] = pw / pw.iloc[0] * 100

    # Drop a peer that would flatten the chart (e.g. one up 2600%)
    peer_dropped = False
    if "Peer" in series and series["Peer"].max() > 4 * series["Stock"].max():
        del series["Peer"]
        peer_dropped = True

    allv = pd.concat(series.values())
    LO, HI = float(allv.min()), float(allv.max())
    yt = lambda v: 8 + 144 * (1 - (v - LO) / ((HI - LO) or 1))
    ticks = "".join(
        f'<line x1="24" y1="{yt(v):.1f}" x2="640" y2="{yt(v):.1f}" stroke="{INK}" stroke-opacity=".15" stroke-dasharray="2 4"/>'
        f'<text x="18" y="{yt(v)+3:.1f}" fill="{INK}" font-size="8" text-anchor="end" font-family="JetBrains Mono">{v}</text>'
        for v in [25, 50, 75, 100, 125, 150, 200, 250, 300, 400] if LO <= v <= HI)

    def path(ser, col, wd):
        n = len(ser)
        pts = " L ".join(f"{8+624*i/(n-1):.1f},{yt(v):.1f}" for i, v in enumerate(ser.values))
        return f'<path d="M {pts}" fill="none" stroke="{col}" stroke-width="{wd}"/>'

    body = ""
    if "Nifty" in series:
        body += path(series["Nifty"], BLUE, 1.7)
    if "Peer" in series:
        body += path(series["Peer"], RED, 1.7)
    body += path(series["Stock"], INK, 2.5)
    open(os.path.join(a.out, "compare.html"), "w").write(
        f'<svg viewBox="0 0 640 170" class="cmp">{ticks}{body}</svg>')

    # ---- returns table rows ----
    rows = ""
    for lbl, d in use.items():
        if d > 90000:
            r_stock = float((s.iloc[-1] / s.iloc[0] - 1) * 100)
            r_nifty = pct(nifty, (end - listed).days, end) if nifty is not None else None
            r_peer = pct(peer, (end - listed).days, end) if peer is not None else None
            lbl_disp = "Since listing"
        else:
            r_stock = pct(s, d, end)
            r_nifty = pct(nifty, d, end) if nifty is not None else None
            r_peer = pct(peer, d, end) if peer is not None else None
            lbl_disp = lbl

        def cell(v):
            if v is None:
                return '<td class="rt">&mdash;</td>'
            cls = "pos" if v > 0 else "neg"
            return f'<td class="rt {cls}">{v:+.1f}%</td>'

        rows += f"<tr><td>{lbl_disp}</td>{cell(r_stock)}{cell(r_nifty)}{cell(r_peer)}</tr>"
    open(os.path.join(a.out, "returns_rows.html"), "w").write(rows)

    # ---- dividends ----
    div_rows, div_recent, div_ttm = "", [], None
    if div is not None and len(div):
        last12 = div[div.index >= end - pd.Timedelta(days=365)]
        div_ttm = float(last12.sum()) if len(last12) else 0.0
        for d_date, d_amt in list(div.items())[-8:][::-1]:
            div_rows += f'<tr><td>{d_date.date()}</td><td class="rt">&#8377;{float(d_amt):.2f}</td></tr>'
            div_recent.append({"date": str(d_date.date()), "amount": float(d_amt)})
    open(os.path.join(a.out, "dividend_rows.html"), "w").write(div_rows or
        '<tr><td colspan="2">No dividend history found</td></tr>')

    # ---- corporate actions: ALWAYS check before calling a fall a "crash" ----
    split_list = []
    if splits is not None and len(splits):
        split_list = [{"date": str(k.date()), "ratio": float(v)} for k, v in splits.items()]

    y1 = s[s.index >= end - pd.Timedelta(days=365)]
    facts = {
        "ticker": tk,
        "last_close": round(px, 2),
        "last_date": str(end.date()),
        "listed_from": str(listed.date()),
        "years_listed": round(years_listed, 2),
        "short_history_mode": short_history,
        "peak": round(float(s.max()), 2),
        "peak_date": str(s.idxmax().date()),
        "drawdown_from_peak_pct": round(float(px / s.max() - 1) * 100, 1),
        "low_52w": round(float(y1.min()), 2),
        "high_52w": round(float(y1.max()), 2),
        "at_52w_low": bool(px <= float(y1.min()) * 1.02),
        "at_52w_high": bool(px >= float(y1.max()) * 0.98),
        "returns_pct": {},
        "dividend_ttm": round(div_ttm, 2) if div_ttm is not None else None,
        "dividend_yield_pct": round(div_ttm / px * 100, 2) if div_ttm else None,
        "recent_dividends": div_recent,
        "splits": split_list,
        "has_corporate_action": len(split_list) > 0,
        "peer": a.peer.upper() if a.peer else None,
        "peer_dropped_from_chart": peer_dropped,
        "rebased_end_values": {k: round(float(v.iloc[-1]), 1) for k, v in series.items()},
    }
    for lbl, d in use.items():
        days = (end - listed).days if d > 90000 else d
        facts["returns_pct"][lbl] = {
            "stock": round(pct(s, days, end), 2) if pct(s, days, end) is not None else None,
            "nifty": round(pct(nifty, days, end), 2) if nifty is not None and pct(nifty, days, end) is not None else None,
            "peer": round(pct(peer, days, end), 2) if peer is not None and pct(peer, days, end) is not None else None,
        }

    json.dump(facts, open(os.path.join(a.out, "facts.json"), "w"), indent=2)
    print(json.dumps(facts, indent=2))
    print(f"\nWrote data + charts to {a.out}/")
    if short_history:
        print("NOTE: short-history mode - under 3 years listed, 3Y/5Y views suppressed.")
    if split_list:
        print(f"NOTE: {len(split_list)} corporate action(s) found - price falls may be adjustments, not crashes.")


if __name__ == "__main__":
    main()
