# Weekly Stock Opportunity Screener

A free, personal tool that scans the market every week and highlights the stocks showing the strongest combination of:

- Strong recent momentum (1-week + 1-month)
- Rising / elevated volume
- Healthy technical position (to reduce the chance of large losses)

Uses only free data from Yahoo Finance via `yfinance`.

---

## Files

| File | Purpose |
|------|---------|
| `stock_screener_core.py` | Core logic (scoring, data download, report generation) |
| `run_weekly_screener.py` | Simple command-line runner |
| `streamlit_app.py` | Nice interactive web dashboard |

---

## Quick Start

### 1. Install dependencies (one time)

```bash
pip install yfinance streamlit pandas numpy plotly ta
```

### 2. Run the command-line version

```bash
python run_weekly_screener.py
```

Options:
```bash
python run_weekly_screener.py --top 15 --min-price 10
python run_weekly_screener.py --tickers AAPL,MSFT,NVDA,AMD,AVGO
```

### 3. Run the Streamlit web app

```bash
streamlit run streamlit_app.py
```

Then open the local URL it shows (usually http://localhost:8501).

---

## How the scoring works

The Opportunity Score rewards:

- Strong 1-week returns (highest weight)
- Solid 1-month returns
- Relative volume ≥ 1.2–1.5x (rising interest)
- Price above 50-day and 200-day moving averages
- RSI in the healthy momentum zone (roughly 55–70)
- Trading near 52-week highs (breakout potential)

It penalizes:

- Very low volume
- Extreme overbought RSI (>75)
- Stocks far below key moving averages

This gives a bias toward stocks that are already moving with conviction while still applying basic risk filters.

---

## Recommended weekly routine (NZ time)

- Run it **Friday evening or Saturday morning** (after US markets close)
- Look at the top 5–10 names
- Do a quick sanity check (news, earnings date, overall market mood)
- Decide if any fit your risk tolerance and position size rules

---

## Important disclaimer

This is **not financial advice**.  
The tool is for research and idea generation only.  
Past performance does not guarantee future results.  
Always do your own due diligence and never invest money you cannot afford to lose.

---

## Customisation ideas

- Change the universe (S&P 500 → Nasdaq-100, your own watchlist, or ASX stocks)
- Tweak the scoring weights in `score_stock()` inside `stock_screener_core.py`
- Add more filters (e.g. minimum market cap, sector preference)
- Schedule it with cron / Task Scheduler and email the CSV to yourself

Enjoy the edge of systematic weekly scanning!
