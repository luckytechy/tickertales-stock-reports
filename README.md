# Ticker Tales - Stock Deep Dives

Type a stock ticker into GitHub. Get a published, branded analysis page a couple of minutes later.

---

## Setup (once, about 10 minutes)

### 1. Turn on GitHub Pages

Repo -> **Settings** -> **Pages** -> under *Build and deployment*:

- **Source**: Deploy from a branch
- **Branch**: `main`, folder **`/docs`**
- Click **Save**

Your site will be at `https://luckytechy.github.io/tickertales-stock-reports/`

### 2. Allow Actions to publish

Repo -> **Settings** -> **Actions** -> **General** -> scroll to *Workflow permissions* ->
select **Read and write permissions** -> **Save**.

Without this the workflow builds the page but cannot commit it.

### 3. Add your Anthropic API key (recommended)

Repo -> **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**

- Name: `ANTHROPIC_API_KEY`
- Value: your key from [console.anthropic.com](https://console.anthropic.com)

**This is optional.** Without it, pages still build with full price data, charts, returns,
dividends and automatic warnings - but the written analysis sections stay empty and say so.
With it, Claude researches the company live and writes the narrative.

---

## Using it

1. Repo -> **Actions** tab
2. Select **Generate Stock Report** in the left sidebar
3. Click **Run workflow**
4. Enter the NSE ticker - `ITC`, `TATACOMM`, `COALINDIA`, `STANLEY`
5. Optionally enter a peer to compare against - `HINDUNILVR`, `BHARTIARTL`
6. Click the green **Run workflow** button

Two to three minutes later the page is live. The run summary shows the exact link.

The homepage at `/index.html` lists every report you have generated, newest first.

---

## What is automated, and what is not

Being straight about this matters, because the two halves have very different reliability.

**Fully reliable - computed, not guessed:**

- Price history, returns over every timeframe, benchmark comparison vs the Nifty
- Interactive charts and the rebased Rs100 comparison
- Dividend history and trailing yield
- 52-week range, drawdown from peak
- Automatic warnings (below)

**Needs the API key, and is a model's judgement:**

- What is happening with the company right now
- Quarterly commentary and what management said
- Valuation, growth, balance-sheet and ownership reads
- Strengths, watch-points, overall quality rating

Always sanity-check the written sections against the company's own filings before publishing
anything. The data sections you can trust; the narrative is a well-researched draft.

---

## Guardrails built in

Each of these exists because it caused a real error at some point:

| Guardrail | What it does |
|---|---|
| **Short-history mode** | Under 3 years listed -> shows 3M/6M/1Y/Since-listing instead of fake 3Y/5Y views, and says so |
| **Corporate action check** | Detects splits and bonuses, warns that a price "fall" may be an adjustment |
| **Chart/table consistency** | Weekly resampling keeps the window's true first price, so the chart cannot disagree with the returns table |
| **52-week low/high flag** | Surfaces automatically when the price sits at either extreme |
| **Runaway peer** | A peer whose return would flatten the chart is dropped from it but kept in the table |
| **No invented numbers** | Anything unfetchable comes back empty and is labelled, never estimated |
| **No advice** | The prompt forbids buy/sell/hold calls and target prices |

---

## Running locally

```bash
pip install -r requirements.txt

python scripts/fetch_data.py ITC --peer HINDUNILVR --out build/
python scripts/write_analysis.py --facts build/facts.json --out build/
python scripts/build_page.py --ticker ITC --build build/ --out docs/stocks/
python scripts/build_index.py

open docs/stocks/ITC.html
```

Set `ANTHROPIC_API_KEY` in your shell first if you want the narrative.

---

## Files

```
.github/workflows/generate-report.yml   the button you press
scripts/fetch_data.py                   market data + charts   (deterministic)
scripts/write_analysis.py               narrative via Claude   (needs API key)
scripts/build_page.py                   renders the report page
scripts/build_index.py                  rebuilds the homepage
templates/logo.txt                      Ticker Tales logo, base64
docs/                                   published site - do not edit by hand
```

---

## Ideas for later

- Schedule a weekly refresh of your watchlist with a `cron` trigger
- Trigger from a GitHub Issue so you can request a report from your phone
- Push the generated page straight into tickertales.in instead of GitHub Pages
- Add an RSS feed of new reports

---

## Disclaimer

These pages are generated automatically and may contain errors. Nothing produced here is
investment advice, a buy/sell/hold recommendation, or personalised financial advice. The author
is not a SEBI-registered Investment Adviser. Verify all figures independently before acting.
