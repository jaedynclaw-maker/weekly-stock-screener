"""
Weekly Stock Opportunity Screener - Core Logic
Uses free yfinance data.
Focus: strong recent momentum + rising volume + basic risk filters.
Also supports Higher-risk smaller stocks, IPO calendar, company blurbs, and illustrative potential.
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
    """Scrape current S&P 500 tickers from Wikipedia."""
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        df = tables[0]
        tickers = df["Symbol"].str.replace(".", "-", regex=False).tolist()
        return tickers
    except Exception as e:
        print(f"Could not fetch S&P 500 list: {e}")
        return [
            "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "BRK-B",
            "JPM", "V", "UNH", "XOM", "LLY", "JNJ", "AVGO", "PG", "MA", "HD",
            "COST", "ABBV", "MRK", "PEP", "KO", "WMT", "BAC", "CRM", "CSCO",
            "ACN", "TMO", "MCD", "ABT", "LIN", "DHR", "NEE", "TXN", "PM",
            "UPS", "RTX
