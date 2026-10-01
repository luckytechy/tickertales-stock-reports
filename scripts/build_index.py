#!/usr/bin/env python3
"""Rebuild the homepage listing every report generated so far."""
import datetime
import glob
import html
import json
import os

OUT = "docs"
META = "docs/stocks/_meta"


def esc(x):
    return html.escape(str(x)) if x is not None else ""


def main():
    cards = []
    entries = []
    for f in sorted(glob.glob(os.path.join(META, "*.json"))):
        try:
            entries.append(json.load(open(f)))
        except Exception:
            pass

    entries.sort(key=lambda e: e.get("generated", ""), reverse=True)
    palette = ["mint", "yellow", "blue", "orange", "pink"]

    for i, e in enumerate(entries):
        r = e.get("return_1y")
        rtxt = f"{r:+.1f}% 1yr" if r is not None else "&mdash;"
        rcls = "pos" if (r or 0) > 0 else "neg"
        cards.append(f"""<a class="card {palette[i % len(palette)]}" href="stocks/{esc(e['ticker'])}.html">
  <div class="row"><span class="tickpill">NSE:{esc(e['ticker'])}</span>
  <span class="ret {rcls}">{rtxt}</span></div>
  <h3>{esc(e['ticker'])}</h3>
  <p>{esc(e.get('one_liner',''))[:150]}</p>
  <div class="foot"><span>&#8377;{e.get('last_close','')} &middot; {esc(e.get('last_date',''))}</span>
  <span>Quality: {esc(e.get('quality','&mdash;'))}</span></div>
</a>""")

    logo = ""
    if os.path.exists("templates/logo.txt"):
        logo = open("templates/logo.txt").read().strip()

    page = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Ticker Tales - Stock Deep Dives</title>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,700;12..96,800&family=Hanken+Grotesk:wght@400;500;600&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet"/>
<style>
:root{{--ink:#1b1a17;--ink2:#3a3832;--bg:#F5F1EB;--white:#FFFFFF;--yellow:#F9D55A;
--orange:#FFAA78;--pink:#F9A8B4;--blue:#93C5FD;--mint:#6AE9B8;
--sans:'Hanken Grotesk',system-ui,sans-serif;--head:'Bricolage Grotesque',system-ui,sans-serif;
--mono:'JetBrains Mono','Courier New',monospace;}}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background-color:var(--bg);background-image:linear-gradient(rgba(27,26,23,.055) 1px,transparent 1px),
linear-gradient(90deg,rgba(27,26,23,.055) 1px,transparent 1px);background-size:34px 34px;
font-family:var(--sans);color:var(--ink);}}
.wrap{{max-width:860px;margin:0 auto;padding:30px 16px 60px;}}
.mast{{display:flex;align-items:center;gap:9px;margin-bottom:26px;}}
.logo-mark{{height:38px;border-radius:8px;}}
.logo{{font-family:var(--head);font-weight:800;font-size:24px;letter-spacing:-.03em;}}
.logo span{{background:var(--yellow);border:2px solid var(--ink);border-radius:6px;padding:0 6px;box-shadow:3px 3px 0 0 var(--ink);}}
h1{{font-family:var(--head);font-weight:800;font-size:34px;line-height:1.1;letter-spacing:-.03em;margin-bottom:10px;}}
.lede{{font-size:15px;color:var(--ink2);margin-bottom:26px;max-width:60ch;}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:16px;}}
.card{{border:2px solid var(--ink);border-radius:16px;padding:18px;box-shadow:5px 5px 0 0 var(--ink);
text-decoration:none;color:var(--ink);transition:.12s;display:block;}}
.card:hover{{transform:translate(-2px,-2px);box-shadow:7px 7px 0 0 var(--ink);}}
.card.mint{{background:var(--mint);}}.card.yellow{{background:var(--yellow);}}
.card.blue{{background:var(--blue);}}.card.orange{{background:var(--orange);}}.card.pink{{background:var(--pink);}}
.card h3{{font-family:var(--head);font-weight:800;font-size:20px;margin:8px 0 6px;}}
.card p{{font-size:13px;line-height:1.5;margin-bottom:12px;}}
.row{{display:flex;justify-content:space-between;align-items:center;gap:8px;}}
.tickpill{{font-family:var(--mono);font-size:10px;font-weight:700;border:2px solid var(--ink);
border-radius:6px;padding:2px 7px;background:rgba(255,255,255,.75);}}
.ret{{font-family:var(--mono);font-size:11px;font-weight:700;}}
.ret.pos{{color:#0a5c3e;}}.ret.neg{{color:#8c2d1f;}}
.foot{{display:flex;justify-content:space-between;font-family:var(--mono);font-size:10px;
border-top:1.5px solid var(--ink);padding-top:8px;gap:8px;flex-wrap:wrap;}}
.empty{{background:var(--white);border:2px dashed var(--ink);border-radius:16px;padding:28px;text-align:center;}}
.disc{{background:var(--white);border:2px dashed var(--ink);border-radius:12px;padding:16px;
font-size:11.5px;color:var(--ink2);line-height:1.6;margin-top:30px;}}
@media(max-width:640px){{h1{{font-size:26px;}}}}
</style></head><body><div class="wrap">
<div class="mast">{'<img src="' + logo + '" class="logo-mark" alt="Ticker Tales"/>' if logo else ''}<div class="logo"><span>Ticker Tales</span></div></div>
<h1>Stock Deep Dives</h1>
<p class="lede">Auto-generated fundamental analysis of Indian listed companies.
Live market data, honest about what it can and cannot verify. Educational only - not investment advice.</p>
<div class="grid">
{"".join(cards) if cards else '<div class="empty"><b>No reports yet.</b><br>Run the <i>Generate Stock Report</i> workflow from the Actions tab to create one.</div>'}
</div>
<div class="disc">
These pages are generated automatically and may contain errors. Nothing here is investment advice,
a buy/sell/hold recommendation, or personalised financial advice. The author is not a SEBI-registered
Investment Adviser. Verify all figures independently before acting. Last rebuilt {datetime.date.today().isoformat()}.
</div>
</div></body></html>"""

    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, "index.html"), "w").write(page)
    print(f"Index rebuilt with {len(entries)} report(s)")


if __name__ == "__main__":
    main()
