#!/usr/bin/env python3
"""
Write the narrative sections of the report.

The numbers come from fetch_data.py (deterministic). This step adds the
judgement: what changed, what the price implies, what to watch.

If ANTHROPIC_API_KEY (an API key) or CLAUDE_CODE_OAUTH_TOKEN (a Claude Code
subscription token) is set, Claude writes it using live web search.
If not, the page still builds - narrative sections say "not generated"
rather than inventing a story.

Usage:
    python scripts/write_analysis.py --facts build/facts.json --out build/
"""
import argparse
import json
import os
import re
import sys

MODEL = "claude-sonnet-4-6"

SYSTEM = """You write fundamental stock analysis for Ticker Tales, an Indian \
markets publication. Plain English, no jargon, no hype.

HARD RULES - these exist because each one has caused a real error before:

1. NEVER invent a number. If you cannot verify something, write
   "Not verified - check on Screener" and move on. A missing figure is
   fine; a wrong one is not.

2. CHECK FOR ACCOUNTING ARTIFACTS. A revenue line can jump purely because
   a tax moved from outside gross revenue to inside it. If a company says
   figures are "not strictly comparable", say so loudly. Compare EBITDA and
   PAT, which sit below the distortion.

3. PERCENTAGES OFF A TINY BASE LIE. "Profit up 483%" usually means last
   year was near zero. Always convert to the underlying measure - a margin
   moving 2% to 11.5% is honest, the 483% is theatre.

4. CORPORATE ACTIONS ARE NOT CRASHES. Before calling a price fall a crash,
   check the splits/demerger data supplied to you. A spin-off means holders
   received other shares; raw price series do not add those back, so long-run
   returns are understated. Say so and quantify it.

5. SOURCES CONTRADICT EACH OTHER CONSTANTLY. Prefer the company's own
   filing, then the cluster of independent sources. Name the outlier you set
   aside. Never average conflicting figures.

6. LEAD WITH THE UNCOMFORTABLE FACT. If long-term shareholder returns are
   poor, or there is a governance problem, that goes near the top. A report
   full of good ratios that omits a 70% drawdown is misleading by omission.

7. DISTINGUISH MARGIN-LED FROM VOLUME-LED. Flat revenue with rising margin
   is less durable in commodity businesses than growth in both.

8. NEVER give buy/sell/hold advice, target prices, or tell anyone what to
   do with a position. You are not a SEBI-registered Investment Adviser.
   Describe what the price implies and what would resolve the question.

Return ONLY valid JSON, no markdown fences, with exactly these keys:
{
 "one_liner": "one sentence on what the company actually does",
 "tags": ["4-5 very short pills, e.g. 'P/E ~8x', 'Profit fell 3 yrs running'"],
 "whats_happening": "2-4 sentences on the most recent material news. If a
    results date, record date or AGM falls within ~2 weeks, lead with it.",
 "plain_terms": "3-4 sentences a beginner follows. Name the tension; do not
    smooth it over.",
 "quarters": "the quarterly trend and what management said. Flag derived or
    non-comparable figures explicitly.",
 "performance_read": "honest read on long-term returns, including any
    corporate-action adjustment.",
 "valuation_read": "is it cheap or expensive, and WHY. Separate 'why it is
    cheap' from 'whether it is cheap'.",
 "growth_read": "is the business growing, and is it margin-led or volume-led",
 "health_read": "do profits turn into cash; name whether financial risk or
    business risk is the real concern",
 "ownership_read": "promoter behaviour, pledging, notable investors. If a
    famous investor is NOT on the register, say so plainly.",
 "strengths": ["3-4 items, each tied to a specific number"],
 "watchpoints": ["3-4 items, specific"],
 "one_thing": "the single metric or event that resolves the central question",
 "quality": "Strong | Moderate | Weak",
 "quality_why": "2-3 sentences. If quality and shareholder outcome diverge,
    hold both facts together.",
 "data_confidence": "High | Moderate | Low",
 "data_notes": "what was cross-checked, what could not be verified"
}"""


def fallback(facts, reason="no Claude key was set"):
    """No key, or the writing step failed - build an honest data-only page."""
    t = facts["ticker"]
    na = (f"Not generated - {reason}, so no narrative analysis was written for this section. "
          "The price data, returns and charts on this page are still fully verified.")
    r = facts.get("returns_pct", {})

    tags = []
    for k in ("1Y", "3Y", "5Y"):
        if k in r and r[k].get("stock") is not None:
            tags.append(f"{k}: {r[k]['stock']:+.0f}%")
    if facts.get("dividend_yield_pct"):
        tags.append(f"Yield {facts['dividend_yield_pct']:.1f}%")
    if facts.get("at_52w_low"):
        tags.append("At 52-week low")
    if facts.get("at_52w_high"):
        tags.append("At 52-week high")
    tags.append("Data-only build")

    return {
        "one_liner": f"{t} - listed on the NSE. Company description not generated.",
        "tags": tags[:5],
        "whats_happening": na,
        "plain_terms": na,
        "quarters": na,
        "performance_read": (
            f"Over the periods shown, {t} returned "
            + ", ".join(f"{k} {v['stock']:+.1f}%" for k, v in r.items() if v.get("stock") is not None)
            + ". Benchmark comparisons are in the returns table. "
            + ("Note this company has corporate actions on record - price falls may partly be "
               "adjustments rather than declines. " if facts.get("has_corporate_action") else "")
            + "No narrative analysis was generated."
        ),
        "valuation_read": na, "growth_read": na, "health_read": na, "ownership_read": na,
        "strengths": ["Not generated"],
        "watchpoints": ["Not generated"],
        "one_thing": na,
        "quality": "Not assessed",
        "quality_why": na,
        "data_confidence": "Moderate",
        "data_notes": ("Price history, returns, dividends and corporate actions were fetched live "
                       "and are verified. No fundamental or news analysis was performed."),
    }


def parse_json(text):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON object in model response")
    return json.loads(m.group(0))


def via_api(key, prompt):
    import anthropic
    client = anthropic.Anthropic(api_key=key)
    resp = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        system=SYSTEM,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 12}],
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in resp.content if b.type == "text")


def via_claude_code(token, prompt):
    """Use the Claude Code CLI, signed in with a Claude Code OAuth token
    (made by `claude setup-token`). This is the supported way to use a
    Claude subscription inside GitHub Actions."""
    import subprocess
    env = dict(os.environ)
    env.pop("ANTHROPIC_API_KEY", None)          # else the CLI treats it as an API key
    env["CLAUDE_CODE_OAUTH_TOKEN"] = token
    cmd = ["claude", "-p", "--output-format", "json",
           "--append-system-prompt", SYSTEM,
           "--allowedTools", "WebSearch", "WebFetch",
           "--max-turns", "40"]
    r = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                       env=env, timeout=1200)
    if r.returncode != 0:
        raise RuntimeError(f"claude CLI exit {r.returncode}: {(r.stderr or r.stdout)[-600:]}")
    out = json.loads(r.stdout)
    if out.get("is_error"):
        raise RuntimeError(f"claude CLI error: {str(out.get('result'))[:600]}")
    return out.get("result", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--facts", required=True)
    ap.add_argument("--out", default="build")
    a = ap.parse_args()

    facts = json.load(open(a.facts))
    outpath = os.path.join(a.out, "analysis.json")

    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", "").strip()
    # A Claude Code OAuth token pasted into the ANTHROPIC_API_KEY secret is fine too.
    if key.startswith("sk-ant-oat"):
        token, key = token or key, ""

    if not key and not token:
        print("No Claude key or token - building data-only page.")
        json.dump(fallback(facts), open(outpath, "w"), indent=2)
        return

    prompt = f"""Analyse the Indian listed company with NSE ticker {facts['ticker']}.

Verified market data (use these numbers, do not recompute or contradict them):
{json.dumps(facts, indent=2)}

Search the web for: the latest quarterly results and what management said on
the earnings call; any news in the last 3 months; valuation metrics (P/E, P/B,
ROE, ROCE, debt); shareholding pattern and promoter pledging; upcoming results
or record dates.

Pay attention to the corporate-action data above before describing any price
fall. If short_history_mode is true, say clearly that long-horizon evidence
does not exist yet.

Return only the JSON object, with no other text."""

    try:
        if token:
            print("Writing analysis with Claude Code (OAuth token).")
            text = via_claude_code(token, prompt)
        else:
            print("Writing analysis with the Anthropic API key.")
            text = via_api(key, prompt)
        analysis = parse_json(text)
        json.dump(analysis, open(outpath, "w"), indent=2)
        print(f"Analysis written for {facts['ticker']} "
              f"(quality: {analysis.get('quality')}, confidence: {analysis.get('data_confidence')})")
    except Exception as e:
        print(f"Analysis step failed ({e}) - falling back to data-only page.", file=sys.stderr)
        json.dump(fallback(facts, "the analysis step failed on this run"), open(outpath, "w"), indent=2)


if __name__ == "__main__":
    main()
