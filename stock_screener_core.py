"""
Weekly Stock Opportunity Screener - Core Logic
Uses free yfinance data. Focus: strong recent momentum + rising volume,
while filtering for lower risk of large losses.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

# -----------------------------
# 1. Get universe (S&P 500)
# -----------------------------
def get_sp500_tickers():
    """Scrape current S&P 500 tickers from Wikipedia."""
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        df = tables[0]
        tickers = df["Symbol"].str.replace(".", "-", regex=False).tolist()
        return tickers
    except Exception as e:
        print(f"Could not fetch S&P 500 list: {e}")
        # Fallback to a solid liquid list
        return [
            "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "BRK-B",
            "JPM", "V", "UNH", "XOM", "LLY", "JNJ", "AVGO", "PG", "MA", "HD",
            "COST", "ABBV", "MRK", "PEP", "KO", "WMT", "BAC", "CRM", "CSCO",
            "ACN", "TMO", "MCD", "ABT", "LIN", "DHR", "NEE", "TXN", "PM",
            "UPS", "RTX", "QCOM", "HON", "LOW", "AMGN", "IBM", "CAT", "GE",
            "SBUX", "INTU", "AXP", "BA", "GS", "BLK", "AMD", "ISRG", "SPGI"
        ]


# -----------------------------
# 2. Download data
# -----------------------------
def download_data(tickers, period="6mo"):
    """Download daily OHLCV for a list of tickers."""
    print(f"Downloading data for {len(tickers)} tickers...")
    data = yf.download(
        tickers,
        period=period,
        interval="1d",
        group_by="ticker",
        auto_adjust=True,
        threads=True,
        progress=False
    )
    return data


# -----------------------------
# 3. Calculate indicators & metrics
# -----------------------------
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def analyze_ticker(df, ticker):
    """
    Analyze a single ticker's dataframe.
    Returns a dict of metrics or None if insufficient data.
    """
    if df is None or len(df) < 50:
        return None

    close = df["Close"].dropna()
    volume = df["Volume"].dropna()
    if len(close) < 50:
        return None

    # Returns
    ret_1w = (close.iloc[-1] / close.iloc[-6] - 1) * 100 if len(close) >= 6 else np.nan
    ret_1m = (close.iloc[-1] / close.iloc[-22] - 1) * 100 if len(close) >= 22 else np.nan
    ret_3m = (close.iloc[-1] / close.iloc[-66] - 1) * 100 if len(close) >= 66 else np.nan

    # Moving averages
    sma50 = close.rolling(50).mean().iloc[-1]
    sma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else np.nan
    price = close.iloc[-1]
    dist_sma50 = (price / sma50 - 1) * 100 if pd.notna(sma50) else np.nan
    dist_sma200 = (price / sma200 - 1) * 100 if pd.notna(sma200) else np.nan

    # RSI
    rsi = compute_rsi(close).iloc[-1]

    # Volume metrics
    avg_vol_20 = volume.rolling(20).mean().iloc[-1]
    avg_vol_5 = volume.rolling(5).mean().iloc[-1]
    rel_volume = avg_vol_5 / avg_vol_20 if avg_vol_20 > 0 else np.nan

    # 52-week high proximity (using available data)
    high_52w = close.max()
    dist_52w_high = (price / high_52w - 1) * 100

    return {
        "ticker": ticker,
        "price": round(price, 2),
        "ret_1w": round(ret_1w, 2) if pd.notna(ret_1w) else None,
        "ret_1m": round(ret_1m, 2) if pd.notna(ret_1m) else None,
        "ret_3m": round(ret_3m, 2) if pd.notna(ret_3m) else None,
        "rsi": round(rsi, 1) if pd.notna(rsi) else None,
        "rel_volume": round(rel_volume, 2) if pd.notna(rel_volume) else None,
        "dist_sma50": round(dist_sma50, 2) if pd.notna(dist_sma50) else None,
        "dist_sma200": round(dist_sma200, 2) if pd.notna(dist_sma200) else None,
        "dist_52w_high": round(dist_52w_high, 2) if pd.notna(dist_52w_high) else None,
        "sma50": round(sma50, 2) if pd.notna(sma50) else None,
        "above_sma50": price > sma50 if pd.notna(sma50) else False,
        "above_sma200": price > sma200 if pd.notna(sma200) else False,
    }


def score_stock(row):
    """
    Composite Opportunity Score.
    Higher = more promising for momentum + volume with downside protection.
    """
    score = 0.0

    # Strong recent momentum (core)
    if pd.notna(row["ret_1w"]):
        score += row["ret_1w"] * 1.5          # 1-week heavily weighted
    if pd.notna(row["ret_1m"]):
        score += row["ret_1m"] * 0.8

    # Rising volume bonus
    if pd.notna(row["rel_volume"]):
        if row["rel_volume"] >= 1.5:
            score += 8
        elif row["rel_volume"] >= 1.2:
            score += 5
        elif row["rel_volume"] >= 1.0:
            score += 2
        else:
            score -= 3                        # low volume penalty

    # Trend quality (reduce chance of big losses)
    if row.get("above_sma50"):
        score += 4
    if row.get("above_sma200"):
        score += 3

    # RSI sweet spot (momentum without extreme overbought)
    if pd.notna(row["rsi"]):
        if 55 <= row["rsi"] <= 70:
            score += 5                        # healthy momentum
        elif 45 <= row["rsi"] < 55:
            score += 2
        elif row["rsi"] > 75:
            score -= 6                        # overbought risk
        elif row["rsi"] < 35:
            score -= 2                        # weak

    # Near 52-week high (breakout potential) but not too extended
    if pd.notna(row["dist_52w_high"]):
        if -5 <= row["dist_52w_high"] <= 0:
            score += 4
        elif -12 <= row["dist_52w_high"] < -5:
            score += 2

    return round(score, 2)


# -----------------------------
# 4. Main screening function
# -----------------------------
def run_screener(tickers=None, top_n=15, min_price=5.0):
    """
    Run the full weekly opportunity screener.
    Returns a ranked DataFrame of the best opportunities.
    """
    if tickers is None:
        tickers = get_sp500_tickers()

    data = download_data(tickers)

    results = []
    # Handle both multi-ticker and single-ticker return shapes
    if isinstance(data.columns, pd.MultiIndex):
        available = data.columns.get_level_values(0).unique()
        for ticker in available:
            try:
                df = data[ticker].copy()
                metrics = analyze_ticker(df, ticker)
                if metrics and metrics["price"] and metrics["price"] >= min_price:
                    results.append(metrics)
            except Exception:
                continue
    else:
        # Single ticker case
        metrics = analyze_ticker(data, tickers[0] if isinstance(tickers, list) else tickers)
        if metrics:
            results.append(metrics)

    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results)
    df["score"] = df.apply(score_stock, axis=1)

    # Sort by score descending
    df = df.sort_values("score", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1

    # Reorder columns
    cols = [
        "rank", "ticker", "score", "price",
        "ret_1w", "ret_1m", "ret_3m",
        "rel_volume", "rsi",
        "dist_sma50", "dist_sma200", "dist_52w_high",
        "above_sma50", "above_sma200"
    ]
    df = df[[c for c in cols if c in df.columns]]

    return df.head(top_n)


def generate_report(df, top_n=10):
    """Pretty text report for the top opportunities."""
    if df.empty:
        return "No results found."

    lines = []
    lines.append("=" * 70)
    lines.append(f"  WEEKLY STOCK OPPORTUNITY REPORT  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 70)
    lines.append("")
    lines.append("Focus: Strong recent momentum + rising volume  |  Lower downside risk filters applied")
    lines.append("")
    lines.append(f"Top {min(top_n, len(df))} most promising names this week:\n")

    for _, row in df.head(top_n).iterrows():
        lines.append(f"#{int(row['rank']):2d}  {row['ticker']:<6}  Score: {row['score']:>6.1f}")
        lines.append(f"     Price: ${row['price']:<8}  1W: {row['ret_1w']:+.1f}%   1M: {row['ret_1m']:+.1f}%")
        vol_str = f"{row['rel_volume']:.2f}x" if pd.notna(row['rel_volume']) else "N/A"
        rsi_str = f"{row['rsi']:.0f}" if pd.notna(row['rsi']) else "N/A"
        lines.append(f"     Rel Vol: {vol_str:<6}  RSI: {rsi_str:<4}  vs 50SMA: {row['dist_sma50']:+.1f}%")
        reason = []
        if row['ret_1w'] > 3:
            reason.append("strong 1-week momentum")
        if pd.notna(row['rel_volume']) and row['rel_volume'] >= 1.3:
            reason.append("elevated volume")
        if row.get('above_sma50'):
            reason.append("above 50-day MA")
        if pd.notna(row['rsi']) and 55 <= row['rsi'] <= 70:
            reason.append("healthy RSI")
        if reason:
            lines.append(f"     Why: {', '.join(reason)}")
        lines.append("")

    lines.append("-" * 70)
    lines.append("Disclaimer: This is not financial advice. Past performance ≠ future results.")
    lines.append("Always do your own research and consider risk management.")
    lines.append("=" * 70)

    return "\n".join(lines)


if __name__ == "__main__":
    # Quick test when run directly
    print("Running weekly opportunity screener...")
    results = run_screener(top_n=12)
    print(generate_report(results))
    results.to_csv("weekly_opportunities.csv", index=False)
    print("\nSaved results to weekly_opportunities.csv")
