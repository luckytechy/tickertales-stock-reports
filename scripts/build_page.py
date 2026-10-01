#!/usr/bin/env python3
"""
Render the final Ticker Tales HTML report.

Usage:
    python scripts/build_page.py --ticker ITC --build build/ --out docs/stocks/
"""
import argparse
import datetime
import html
import json
import os

CSS = """
:root{--ink:#1b1a17;--ink2:#3a3832;--bg:#F5F1EB;--white:#FFFFFF;--yellow:#F9D55A;
--orange:#FFAA78;--pink:#F9A8B4;--blue:#93C5FD;--mint:#6AE9B8;
--sans:'Hanken Grotesk',system-ui,sans-serif;--head:'Bricolage Grotesque',system-ui,sans-serif;
--mono:'JetBrains Mono','Courier New',monospace;}
*{margin:0;padding:0;box-sizing:border-box;}
body{background-color:var(--bg);background-image:linear-gradient(rgba(27,26,23,.055) 1px,transparent 1px),
linear-gradient(90deg,rgba(27,26,23,.055) 1px,transparent 1px);background-size:34px 34px;
font-family:var(--sans);color:var(--ink);-webkit-font-smoothing:antialiased;position:relative;}
.wrap{max-width:700px;margin:0 auto;padding:26px 16px 60px;position:relative;z-index:1;}
.deco{position:absolute;pointer-events:none;z-index:0;}
.mast{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-bottom:18px;}
.logo{font-family:var(--head);font-weight:800;font-size:22px;letter-spacing:-.03em;display:flex;align-items:center;gap:9px;
text-decoration:none;color:var(--ink);}
.logo-mark{height:34px;width:auto;border-radius:8px;display:block;}
.logo span{background:var(--yellow);border:2px solid var(--ink);border-radius:6px;padding:0 6px;box-shadow:3px 3px 0 0 var(--ink);}
.issue-tag{font-family:var(--mono);font-size:11px;font-weight:700;border:2px solid var(--ink);border-radius:12px;padding:4px 10px;background:var(--white);}
.hcard{background:var(--white);border:2px solid var(--ink);border-radius:16px;padding:22px 20px;box-shadow:5px 5px 0 0 var(--ink);margin-bottom:16px;}
.eyebrow{font-family:var(--mono);font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--ink2);margin-bottom:6px;}
h1.title{font-family:var(--head);font-weight:800;font-size:30px;line-height:1.1;letter-spacing:-.03em;margin-bottom:8px;}
.subline{font-size:14px;color:var(--ink2);margin-bottom:14px;}
.taglist{display:flex;flex-wrap:wrap;gap:6px;}
.tag{font-family:var(--mono);font-size:10.5px;font-weight:700;border:2px solid var(--ink);border-radius:12px;padding:3px 9px;}
.tag.y{background:var(--yellow);}.tag.o{background:var(--orange);}.tag.p{background:var(--pink);}
.tag.b{background:var(--blue);}.tag.m{background:var(--mint);}.tag.w{background:var(--white);}
.tabs{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px;}
.tab{font-family:var(--mono);font-size:11px;font-weight:700;border:2px solid var(--ink);border-radius:10px;padding:7px 12px;background:var(--white);cursor:pointer;transition:.1s;}
.tab:hover{transform:translate(-1px,-1px);box-shadow:2px 2px 0 0 var(--ink);}
.tab.active{background:var(--ink);color:var(--white);}
.panel{display:none;}.panel.active{display:block;animation:f .2s ease;}
@keyframes f{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}
.card{border:2px solid var(--ink);border-radius:16px;padding:20px 18px;margin-bottom:14px;box-shadow:5px 5px 0 0 var(--ink);}
.card.white{background:var(--white);}.card.yellow{background:var(--yellow);}
.card.orange{background:var(--orange);}.card.pink{background:var(--pink);}
.card.blue{background:var(--blue);}.card.mint{background:var(--mint);}
.card h2{font-family:var(--head);font-weight:800;font-size:16px;letter-spacing:-.02em;margin-bottom:10px;}
.card h4{font-family:var(--head);font-weight:800;font-size:13.5px;margin-bottom:10px;}
.card p{font-size:14px;line-height:1.6;margin-bottom:8px;}.card p:last-child{margin-bottom:0;}
.inset{background:var(--white);border:2px solid var(--ink);border-radius:12px;padding:12px 14px;margin:8px 0;font-size:13.5px;line-height:1.55;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:6px;}
.metric{background:var(--white);border:2px solid var(--ink);border-radius:12px;padding:11px 13px;}
.metric .k{font-family:var(--mono);font-size:9.5px;font-weight:700;text-transform:uppercase;color:var(--ink2);margin-bottom:5px;}
.metric .v{font-family:var(--head);font-weight:800;font-size:20px;letter-spacing:-.02em;}
.metric .v.sm{font-size:14px;}
.metric .n{font-size:11px;color:var(--ink2);margin-top:3px;}
table{width:100%;border-collapse:collapse;margin:6px 0 10px;font-size:13px;background:var(--white);border:2px solid var(--ink);border-radius:10px;overflow:hidden;}
th,td{text-align:left;padding:8px 10px;border-bottom:1.5px solid var(--ink);}
th{font-family:var(--mono);font-size:9.5px;text-transform:uppercase;letter-spacing:.05em;background:var(--ink);color:var(--white);}
tr:last-child td{border-bottom:none;}
.rt{text-align:right;}td.pos{color:#0a7c52;font-weight:700;}td.neg{color:#c0392b;font-weight:700;}
.tickpill{display:inline-block;font-family:var(--mono);font-size:10px;font-weight:700;border:2px solid var(--ink);border-radius:6px;padding:2px 7px;background:var(--white);margin-right:6px;}
.sectorpill{display:inline-block;font-family:var(--mono);font-size:9px;border:2px solid var(--ink);border-radius:20px;padding:2px 8px;background:rgba(255,255,255,.65);}
svg{display:block;width:100%;height:auto;}
.legend{display:flex;flex-wrap:wrap;gap:12px;margin-top:8px;font-size:11px;font-family:var(--mono);}
.legend span{display:flex;align-items:center;gap:5px;}
.sw{width:10px;height:10px;border:1.5px solid var(--ink);border-radius:3px;display:inline-block;}
.tfbtns{display:flex;gap:5px;margin-bottom:10px;flex-wrap:wrap;}
.tfbtn{font-family:var(--mono);font-size:10.5px;font-weight:700;border:2px solid var(--ink);border-radius:8px;padding:4px 12px;background:var(--white);cursor:pointer;}
.tfbtn.active{background:var(--ink);color:var(--white);}
.tfpanel{display:none;}.tfpanel.active{display:block;}
.tfhead{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:6px;margin-bottom:7px;}
.tfret{font-family:var(--head);font-weight:800;font-size:22px;}
.tfret.pos{color:#0a7c52;}.tfret.neg{color:#c0392b;}
.tflab{font-family:var(--mono);font-size:10.5px;color:var(--ink2);}
.tfrange{font-family:var(--mono);font-size:10px;color:var(--ink2);}
.spark{height:130px;}.cmp{height:170px;}
.tffoot{display:flex;justify-content:space-between;font-family:var(--mono);font-size:9.5px;color:var(--ink2);margin-top:4px;}
.disc{background:var(--white);border:2px dashed var(--ink);border-radius:12px;padding:14px 16px;font-size:11.5px;color:var(--ink2);line-height:1.6;margin-top:10px;}
ul.plain{list-style:none;padding:0;margin:0;}
ul.plain li{font-size:14px;line-height:1.6;margin-bottom:7px;}
@media(max-width:640px){.wrap{padding:18px 10px 48px;}h1.title{font-size:24px;}}
"""

TAG_COLORS = ["y", "m", "p", "b", "o"]


def esc(x):
    return html.escape(str(x)) if x is not None else ""


def para(text):
    """Split a block of text into paragraphs."""
    if not text:
        return ""
    return "".join(f"<p>{esc(p.strip())}</p>" for p in str(text).split("\n\n") if p.strip())


def bullets(items, mark):
    if not items:
        return "<p>Not generated.</p>"
    return "<ul class='plain'>" + "".join(f"<li>{mark} {esc(i)}</li>" for i in items) + "</ul>"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--build", default="build")
    ap.add_argument("--out", default="docs/stocks")
    ap.add_argument("--logo", default="templates/logo.txt")
    a = ap.parse_args()

    facts = json.load(open(os.path.join(a.build, "facts.json")))
    an = json.load(open(os.path.join(a.build, "analysis.json")))
    tf = open(os.path.join(a.build, "timeframes.html")).read()
    cmp_svg = open(os.path.join(a.build, "compare.html")).read()
    rows = open(os.path.join(a.build, "returns_rows.html")).read()
    div_rows = open(os.path.join(a.build, "dividend_rows.html")).read()
    logo = open(a.logo).read().strip() if os.path.exists(a.logo) else ""

    tk = facts["ticker"]
    today = datetime.date.today().strftime("%d %b %Y").upper()
    peer = facts.get("peer") or "Peer"

    tags = "".join(
        f'<span class="tag {TAG_COLORS[i % len(TAG_COLORS)]}">{esc(t)}</span>'
        for i, t in enumerate(an.get("tags", [])[:5]))

    # Alerts that earn a place at the top
    alerts = ""
    if facts.get("at_52w_low"):
        alerts += '<p><b>At its 52-week low.</b> The price is within 2% of the lowest level in a year.</p>'
    if facts.get("at_52w_high"):
        alerts += '<p><b>At its 52-week high.</b> The price is within 2% of the highest level in a year.</p>'
    if facts.get("short_history_mode"):
        alerts += (f'<p><b>Short trading history.</b> Listed {facts["listed_from"]} - only '
                   f'{facts["years_listed"]} years of data exist, so 3-year and 5-year views are '
                   f'not shown. Treat conclusions as provisional.</p>')
    if facts.get("has_corporate_action"):
        sp = ", ".join(f'{s["date"]} ({s["ratio"]}x)' for s in facts["splits"])
        alerts += (f'<p><b>Corporate actions on record:</b> {esc(sp)}. Price falls around these dates '
                   f'may be adjustments rather than declines.</p>')
    if facts.get("peer_dropped_from_chart"):
        alerts += (f'<p><b>Note:</b> {esc(peer)} was left off the comparison chart because its return '
                   f'would compress every other line. It remains in the returns table.</p>')

    alert_card = f'<div class="card pink"><h2>Worth knowing first</h2>{alerts}</div>' if alerts else ""

    dy = facts.get("dividend_yield_pct")
    m = facts["returns_pct"]
    first_tf = list(m.keys())[0]

    def ret(k):
        v = m.get(k, {}).get("stock")
        return f"{v:+.1f}%" if v is not None else "&mdash;"

    tf_buttons = "".join(
        f'<button class="tfbtn{" active" if i == 0 else ""}" data-tf="{k}">{k}</button>'
        for i, k in enumerate(m.keys()))

    page = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{esc(tk)} - Ticker Tales Deep Dive</title>
<meta name="description" content="{esc(an.get('one_liner',''))[:160]}"/>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,700;12..96,800&family=Hanken+Grotesk:wght@400;500;600&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet"/>
<style>{CSS}</style></head><body>
<svg class="deco" style="top:26px;right:6%;width:34px;" viewBox="0 0 24 24" fill="#93C5FD" stroke="#1b1a17" stroke-width="1"><path d="M12 2l2.4 7.2H22l-6 4.6 2.3 7.2-6.3-4.5-6.3 4.5 2.3-7.2-6-4.6h7.6z"/></svg>
<svg class="deco" style="top:640px;left:2%;width:22px;" viewBox="0 0 24 24" fill="#F9D55A" stroke="#1b1a17" stroke-width="1"><path d="M12 2l2.4 7.2H22l-6 4.6 2.3 7.2-6.3-4.5-6.3 4.5 2.3-7.2-6-4.6h7.6z"/></svg>
<div class="wrap">

<div class="mast">
  <a class="logo" href="../index.html">{'<img src="' + logo + '" alt="Ticker Tales" class="logo-mark"/>' if logo else ''}<span>Ticker Tales</span></a>
  <div class="issue-tag">DEEP&nbsp;DIVE &middot; {today}</div>
</div>

<div class="hcard">
  <div class="eyebrow">Fundamentals Deep Dive</div>
  <span class="tickpill">NSE:{esc(tk)}</span><span class="sectorpill">Auto-generated</span>
  <h1 class="title">{esc(tk)}</h1>
  <div class="subline">{esc(an.get('one_liner',''))}</div>
  <div class="taglist">{tags}</div>
</div>

<div class="tabs">
  <button class="tab active" data-t="snapshot">Snapshot</button>
  <button class="tab" data-t="quarters">Quarters</button>
  <button class="tab" data-t="performance">Performance</button>
  <button class="tab" data-t="dividend">Dividend</button>
  <button class="tab" data-t="valuation">Valuation</button>
  <button class="tab" data-t="growth">Growth</button>
  <button class="tab" data-t="health">Health</button>
  <button class="tab" data-t="ownership">Ownership</button>
  <button class="tab" data-t="view">The View</button>
</div>

<div class="panel active" id="snapshot">
  {alert_card}
  <div class="card orange">
    <h2>The 30-second picture</h2>
    <div class="grid">
      <div class="metric"><div class="k">Price</div><div class="v">&#8377;{facts['last_close']:,.2f}</div><div class="n">{facts['last_date']}</div></div>
      <div class="metric"><div class="k">52-wk range</div><div class="v sm">&#8377;{facts['low_52w']:,.0f}-{facts['high_52w']:,.0f}</div><div class="n">{'At the low' if facts.get('at_52w_low') else 'At the high' if facts.get('at_52w_high') else 'Mid-range'}</div></div>
      <div class="metric"><div class="k">From peak</div><div class="v">{facts['drawdown_from_peak_pct']:+.1f}%</div><div class="n">Peak {facts['peak_date']}</div></div>
      <div class="metric"><div class="k">{first_tf} return</div><div class="v">{ret(first_tf)}</div><div class="n">Price only</div></div>
      <div class="metric"><div class="k">1-yr return</div><div class="v">{ret('1Y')}</div><div class="n">Price only</div></div>
      <div class="metric"><div class="k">Div yield</div><div class="v">{f'{dy:.2f}%' if dy else '&mdash;'}</div><div class="n">{f"&#8377;{facts['dividend_ttm']} last 12m" if facts.get('dividend_ttm') else 'None found'}</div></div>
      <div class="metric"><div class="k">Listed since</div><div class="v sm">{facts['listed_from']}</div><div class="n">{facts['years_listed']} years</div></div>
      <div class="metric"><div class="k">Quality</div><div class="v sm">{esc(an.get('quality','&mdash;'))}</div><div class="n">Confidence: {esc(an.get('data_confidence','&mdash;'))}</div></div>
    </div>
  </div>
  <div class="card white"><h2>What's happening</h2>{para(an.get('whats_happening'))}</div>
  <div class="inset"><b>In plain terms.</b> {esc(an.get('plain_terms',''))}</div>
</div>

<div class="panel" id="quarters">
  <div class="card yellow"><h2>The quarterly story</h2>{para(an.get('quarters'))}</div>
</div>

<div class="panel" id="performance">
  <div class="card white">
    <h2>Price history</h2>
    <div class="tfbtns">{tf_buttons}</div>
    {tf}
  </div>
  <div class="card white">
    <h4>&#8377;100 rebased</h4>
    {cmp_svg}
    <div class="legend"><span><i class="sw" style="background:#1b1a17"></i>{esc(tk)}</span><span><i class="sw" style="background:#93C5FD"></i>Nifty 50</span>{f'<span><i class="sw" style="background:#c0392b"></i>{esc(peer)}</span>' if facts.get('peer') and not facts.get('peer_dropped_from_chart') else ''}</div>
  </div>
  <table><tr><th>Period</th><th class="rt">{esc(tk)}</th><th class="rt">Nifty 50</th><th class="rt">{esc(peer)}</th></tr>{rows}</table>
  <div class="card orange">{para(an.get('performance_read'))}</div>
  <div class="inset">Past performance describes what has already happened. It is not an indicator of what comes next.</div>
</div>

<div class="panel" id="dividend">
  <div class="card mint">
    <h2>What it pays</h2>
    <div class="grid">
      <div class="metric"><div class="k">Yield</div><div class="v">{f'{dy:.2f}%' if dy else '&mdash;'}</div><div class="n">Trailing 12 months</div></div>
      <div class="metric"><div class="k">Last 12m total</div><div class="v sm">{f"&#8377;{facts['dividend_ttm']}" if facts.get('dividend_ttm') else '&mdash;'}</div><div class="n">Per share</div></div>
    </div>
  </div>
  <table><tr><th>Ex-date</th><th class="rt">Per share</th></tr>{div_rows}</table>
  <div class="inset">Dividend history is from exchange data. A yield can rise because the dividend grew, or because the price fell - check which applies here.</div>
</div>

<div class="panel" id="valuation"><div class="card white"><h2>Is it cheap or pricey?</h2>{para(an.get('valuation_read'))}</div></div>
<div class="panel" id="growth"><div class="card mint"><h2>Is the business growing?</h2>{para(an.get('growth_read'))}</div></div>
<div class="panel" id="health"><div class="card blue"><h2>Do profits turn into cash?</h2>{para(an.get('health_read'))}</div></div>
<div class="panel" id="ownership"><div class="card orange"><h2>Who owns it</h2>{para(an.get('ownership_read'))}</div></div>

<div class="panel" id="view">
  <div class="card mint"><h2>Strengths</h2>{bullets(an.get('strengths'), '&#10003;')}</div>
  <div class="card pink"><h2>Watch-points</h2>{bullets(an.get('watchpoints'), '!')}</div>
  <div class="card blue"><h2>One thing to track</h2>{para(an.get('one_thing'))}</div>
  <div class="card white">
    <h2>Fundamental quality: {esc(an.get('quality','Not assessed'))}</h2>
    {para(an.get('quality_why'))}
  </div>
  <div class="card white"><h4>Data confidence: {esc(an.get('data_confidence','&mdash;'))}</h4>{para(an.get('data_notes'))}</div>
  <div class="disc">
    This is a view of the fundamentals for educational purposes - not investment advice, not a
    buy/sell/hold recommendation, and not personalised financial advice. This page is generated
    automatically; figures may contain errors and should be verified independently before acting.
    The author is not a SEBI-registered Investment Adviser. Market data as at {facts['last_date']}.
    The decision is yours.
  </div>
</div>

</div>
<script>
document.querySelectorAll('.tab').forEach(t=>t.addEventListener('click',()=>{{
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(x=>x.classList.remove('active'));
  t.classList.add('active'); document.getElementById(t.dataset.t).classList.add('active');
  window.scrollTo({{top:0,behavior:'smooth'}});
}}));
document.querySelectorAll('.tfbtn').forEach(b=>b.addEventListener('click',()=>{{
  document.querySelectorAll('.tfbtn').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.tfpanel').forEach(x=>x.classList.remove('active'));
  b.classList.add('active'); document.getElementById('tf'+b.dataset.tf).classList.add('active');
}}));
</script></body></html>"""

    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, f"{tk}.html")
    open(path, "w").write(page)

    # index entry metadata
    meta_dir = os.path.join(a.out, "_meta")
    os.makedirs(meta_dir, exist_ok=True)
    json.dump({
        "ticker": tk,
        "one_liner": an.get("one_liner", ""),
        "quality": an.get("quality", ""),
        "last_close": facts["last_close"],
        "last_date": facts["last_date"],
        "return_1y": m.get("1Y", {}).get("stock"),
        "generated": datetime.date.today().isoformat(),
    }, open(os.path.join(meta_dir, f"{tk}.json"), "w"), indent=2)

    print(f"Wrote {path} ({len(page):,} bytes)")


if __name__ == "__main__":
    main()
