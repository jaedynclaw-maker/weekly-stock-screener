"""
Weekly Stock Opportunity Screener - Core Logic
Momentum + volume focus, with NZD conversion, Watchlist, ASX support, and blurbs.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")


# -----------------------------
# 1. Universes
# -----------------------------
def get_sp500_tickers():
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        df = tables[0]
        tickers = df["Symbol"].str.replace(".", "-", regex=False).tolist()
        return tickers
    except Exception:
        return [
            "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "BRK-B",
            "JPM", "V", "UNH", "XOM", "LLY", "JNJ", "AVGO", "PG", "MA", "HD",
            "COST", "ABBV", "MRK", "PEP", "KO", "WMT", "BAC", "CRM", "CSCO",
            "ACN", "TMO", "MCD", "ABT", "LIN", "DHR", "NEE", "TXN", "PM",
            "UPS", "RTX", "QCOM", "HON", "LOW", "AMGN", "IBM", "CAT", "GE",
            "SBUX", "INTU", "AXP", "BA", "GS", "BLK", "AMD", "ISRG", "SPGI"
        ]


def get_higher_risk_tickers():
    return [
        "SMCI", "MSTR", "COIN", "HOOD", "SOFI", "UPST", "AFRM", "PATH",
        "SNOW", "NET", "DDOG", "CRWD", "ZS", "MDB", "ESTC", "BILL",
        "TOST", "CAVA", "DUOL", "CELH", "HIMS", "OSCR", "RXRX", "IONQ",
        "RIVN", "LCID", "NIO", "XPEV", "LI", "PLTR", "AI", "BBAI",
        "RKLB", "ASTS", "LUNR", "JOBY", "ACHR", "RDW", "BKSY",
        "SOUN", "OPEN", "RDFN", "COMP", "Z", "CVNA", "W", "CHWY",
        "FSLR", "ENPH", "RUN", "BE", "PLUG", "FCEL", "CHPT", "QS"
    ]


def get_asx_tickers():
    """Popular liquid ASX stocks (Australian market)."""
    return [
        "BHP.AX", "CBA.AX", "CSL.AX", "NAB.AX", "WBC.AX", "ANZ.AX", "WES.AX",
        "MQG.AX", "FMG.AX", "TLS.AX", "WOW.AX", "RIO.AX", "TCL.AX", "GMG.AX",
        "ALL.AX", "QBE.AX", "COL.AX", "STO.AX", "ORG.AX", "NCM.AX", "JHX.AX",
        "REA.AX", "XRO.AX", "WTC.AX", "CPU.AX", "APA.AX", "SHL.AX", "IAG.AX",
        "SUN.AX", "MIN.AX", "PLS.AX", "LYC.AX", "CXO.AX", "LTR.AX"
    ]


# -----------------------------
# 2. FX Helper (USD → NZD)
# -----------------------------
def get_usd_nzd_rate():
    """Get approximate USD to NZD rate."""
    try:
        t = yf.Ticker("NZD=X")
        hist = t.history(period="5d")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
        # fallback
        return 1.70
    except Exception:
        return 1.70  # safe fallback


# -----------------------------
# 3. Download & Indicators
# -----------------------------
def download_data(tickers, period="6mo"):
    print(f"Downloading data for {len(tickers)} tickers...")
    data = yf.download(
        tickers, period=period, interval="1d",
        group_by="ticker", auto_adjust=True, threads=True, progress=False
    )
    return data


def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def analyze_ticker(df, ticker):
    if df is None or len(df) < 50:
        return None

    close = df["Close"].dropna()
    volume = df["Volume"].dropna()
    if len(close) < 50:
        return None

    ret_1w = (close.iloc[-1] / close.iloc[-6] - 1) * 100 if len(close) >= 6 else np.nan
    ret_1m = (close.iloc[-1] / close.iloc[-22] - 1) * 100 if len(close) >= 22 else np.nan
    ret_3m = (close.iloc[-1] / close.iloc[-66] - 1) * 100 if len(close) >= 66 else np.nan

    sma50 = close.rolling(50).mean().iloc[-1]
    sma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else np.nan
    price = close.iloc[-1]
    dist_sma50 = (price / sma50 - 1) * 100 if pd.notna(sma50) else np.nan
    dist_sma200 = (price / sma200 - 1) * 100 if pd.notna(sma200) else np.nan

    rsi = compute_rsi(close).iloc[-1]

    avg_vol_20 = volume.rolling(20).mean().iloc[-1]
    avg_vol_5 = volume.rolling(5).mean().iloc[-1]
    rel_volume = avg_vol_5 / avg_vol_20 if avg_vol_20 > 0 else np.nan

    high_52w = close.max()
    dist_52w_high = (price / high_52w - 1) * 100

    daily_rets = close.pct_change().dropna()
    vol_20 = daily_rets.tail(20).std() * 100 if len(daily_rets) >= 20 else np.nan

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
        "above_sma50": price > sma50 if pd.notna(sma50) else False,
        "above_sma200": price > sma200 if pd.notna(sma200) else False,
        "vol_20d": round(vol_20, 2) if pd.notna(vol_20) else None,
    }


def score_stock(row):
    score = 0.0
    if pd.notna(row["ret_1w"]):
        score += row["ret_1w"] * 1.5
    if pd.notna(row["ret_1m"]):
        score += row["ret_1m"] * 0.8

    if pd.notna(row["rel_volume"]):
        if row["rel_volume"] >= 1.5: score += 8
        elif row["rel_volume"] >= 1.2: score += 5
        elif row["rel_volume"] >= 1.0: score += 2
        else: score -= 3

    if row.get("above_sma50"): score += 4
    if row.get("above_sma200"): score += 3

    if pd.notna(row["rsi"]):
        if 55 <= row["rsi"] <= 70: score += 5
        elif 45 <= row["rsi"] < 55: score += 2
        elif row["rsi"] > 75: score -= 6
        elif row["rsi"] < 35: score -= 2

    if pd.notna(row["dist_52w_high"]):
        if -5 <= row["dist_52w_high"] <= 0: score += 4
        elif -12 <= row["dist_52w_high"] < -5: score += 2

    return round(score, 2)


def illustrative_potential(row):
    if pd.isna(row.get("ret_1w")) or pd.isna(row.get("vol_20d")):
        return "N/A"
    base = row["ret_1w"] * 0.4 * 4
    band = row["vol_20d"] * 2.0
    low = max(base - band, -40)
    high = min(base + band, 60)
    return f"{low:+.0f}% to {high:+.0f}%"


# -----------------------------
# 4. Company info + blurbs
# -----------------------------
def get_company_info(ticker):
    try:
        info = yf.Ticker(ticker).info
        name = info.get("longName") or info.get("shortName") or ticker
        sector = info.get("sector") or "N/A"
        industry = info.get("industry") or "N/A"
        market_cap = info.get("marketCap")
        summary = info.get("longBusinessSummary") or ""
        if summary and len(summary) > 260:
            summary = summary[:257] + "..."
        return {"name": name, "sector": sector, "industry": industry,
                "market_cap": market_cap, "summary": summary}
    except Exception:
        return {"name": ticker, "sector": "N/A", "industry": "N/A",
                "market_cap": None, "summary": ""}


def format_market_cap(mc):
    if not mc or pd.isna(mc): return "N/A"
    if mc >= 1e12: return f"${mc/1e12:.1f}T"
    if mc >= 1e9: return f"${mc/1e9:.1f}B"
    if mc >= 1e6: return f"${mc/1e6:.0f}M"
    return f"${mc:,.0f}"


def build_why_blurb(row):
    reasons = []
    if pd.notna(row.get("ret_1w")) and row["ret_1w"] > 3:
        reasons.append(f"strong 1-week momentum (+{row['ret_1w']:.1f}%)")
    elif pd.notna(row.get("ret_1w")) and row["ret_1w"] > 1:
        reasons.append(f"positive 1-week momentum (+{row['ret_1w']:.1f}%)")
    if pd.notna(row.get("ret_1m")) and row["ret_1m"] > 5:
        reasons.append(f"solid 1-month gain (+{row['ret_1m']:.1f}%)")
    if pd.notna(row.get("rel_volume")):
        if row["rel_volume"] >= 1.5:
            reasons.append(f"elevated volume ({row['rel_volume']:.1f}x)")
        elif row["rel_volume"] >= 1.2:
            reasons.append(f"rising volume ({row['rel_volume']:.1f}x)")
    if row.get("above_sma50") and row.get("above_sma200"):
        reasons.append("above both key moving averages")
    elif row.get("above_sma50"):
        reasons.append("holding above the 50-day MA")
    if pd.notna(row.get("rsi")) and 55 <= row["rsi"] <= 70:
        reasons.append(f"healthy RSI ({row['rsi']:.0f})")
    if pd.notna(row.get("dist_52w_high")) and -8 <= row["dist_52w_high"] <= 0:
        reasons.append("near 52-week high")

    if not reasons:
        return "Scored well on momentum + volume + trend filters."
    if len(reasons) == 1:
        return f"Ranked high because of {reasons[0]}."
    return "Ranked high because of " + ", ".join(reasons[:-1]) + f" and {reasons[-1]}."


def enrich_top_stocks(df, n=5):
    if df.empty: return df
    top = df.head(n).copy()
    names, sectors, industries, mcaps, summaries, whys = [], [], [], [], [], []
    for _, row in top.iterrows():
        info = get_company_info(row["ticker"])
        names.append(info["name"])
        sectors.append(info["sector"])
        industries.append(info["industry"])
        mcaps.append(format_market_cap(info["market_cap"]))
        summaries.append(info["summary"])
        whys.append(build_why_blurb(row))
    top["company_name"] = names
    top["sector"] = sectors
    top["industry"] = industries
    top["market_cap"] = mcaps
    top["summary"] = summaries
    top["why"] = whys
    return top


# -----------------------------
# 5. IPO + Watchlist
# -----------------------------
def get_ipo_calendar(limit=30):
    try:
        cal = yf.Calendars()
        df = cal.get_ipo_info_calendar(limit=limit)
        return df if df is not None else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def get_watchlist_history(tickers, period="3mo"):
    if not tickers: return pd.DataFrame()
    data = download_data(tickers, period=period)
    results = []
    if isinstance(data.columns, pd.MultiIndex):
        for ticker in data.columns.get_level_values(0).unique():
            try:
                metrics = analyze_ticker(data[ticker].copy(), ticker)
                if metrics: results.append(metrics)
            except Exception: continue
    else:
        metrics = analyze_ticker(data, tickers[0])
        if metrics: results.append(metrics)

    if not results: return pd.DataFrame()
    df = pd.DataFrame(results)
    df["score"] = df.apply(score_stock, axis=1)
    df["illustrative_4w"] = df.apply(illustrative_potential, axis=1)
    return df


# -----------------------------
# 6. Main screener
# -----------------------------
def run_screener(tickers=None, top_n=15, min_price=5.0):
    if tickers is None:
        tickers = get_sp500_tickers()

    data = download_data(tickers)
    results = []

    if isinstance(data.columns, pd.MultiIndex):
        for ticker in data.columns.get_level_values(0).unique():
            try:
                metrics = analyze_ticker(data[ticker].copy(), ticker)
                if metrics and metrics["price"] and metrics["price"] >= min_price:
                    results.append(metrics)
            except Exception: continue
    else:
        metrics = analyze_ticker(data, tickers[0] if isinstance(tickers, list) else tickers)
        if metrics: results.append(metrics)

    if not results: return pd.DataFrame()

    df = pd.DataFrame(results)
    df["score"] = df.apply(score_stock, axis=1)
    df["illustrative_4w"] = df.apply(illustrative_potential, axis=1)
    df = df.sort_values("score", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1

    cols = ["rank", "ticker", "score", "price", "ret_1w", "ret_1m", "ret_3m",
            "rel_volume", "rsi", "dist_sma50", "dist_sma200", "dist_52w_high",
            "above_sma50", "above_sma200", "illustrative_4w", "vol_20d"]
    df = df[[c for c in cols if c in df.columns]]
    return df.head(top_n)


def generate_report(df, top_n=10):
    if df.empty: return "No results found."
    lines = ["="*70, f"  WEEKLY STOCK OPPORTUNITY REPORT  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}", "="*70, ""]
    lines.append("Focus: Strong recent momentum + rising volume | Risk filters applied\n")
    for _, row in df.head(top_n).iterrows():
        lines.append(f"#{int(row['rank']):2d}  {row['ticker']:<8}  Score: {row['score']:>5.1f}")
        lines.append(f"     Price: ${row['price']:<8}  1W: {row['ret_1w']:+.1f}%  1M: {row['ret_1m']:+.1f}%")
        lines.append(f"     Rel Vol: {row['rel_volume']:.2f}x   RSI: {row['rsi']:.0f}")
        lines.append("")
    lines.append("-"*70)
    lines.append("Not financial advice. Illustrative ranges are heuristics only.")
    return "\n".join(lines)
