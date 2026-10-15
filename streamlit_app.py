"""
Weekly Stock Opportunity Screener - Streamlit Dashboard
Run with:  streamlit run streamlit_app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from stock_screener_core import run_screener, get_sp500_tickers, generate_report

st.set_page_config(
    page_title="Weekly Stock Opportunities",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #00C853;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #B0BEC5;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #1E1E1E;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #00C853;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">📈 Weekly Stock Opportunity Screener</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Strong momentum + rising volume · Free data (yfinance) · Focused on return potential with lower downside risk</p>', unsafe_allow_html=True)

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Settings")
    top_n = st.slider("Number of top stocks", 5, 30, 12)
    min_price = st.number_input("Minimum price ($)", min_value=1.0, value=5.0, step=1.0)
    
    universe = st.radio(
        "Universe",
        ["S&P 500 (full)", "Quick liquid list (faster)", "Custom tickers"]
    )
    
    custom_tickers = None
    if universe == "Custom tickers":
        custom_input = st.text_area(
            "Enter tickers (comma separated)",
            value="AAPL,MSFT,NVDA,AMZN,GOOGL,META,TSLA,AMD,AVGO,JPM"
        )
        custom_tickers = [t.strip().upper() for t in custom_input.split(",") if t.strip()]
    
    run_button = st.button("🚀 Run Screener", type="primary", use_container_width=True)
    
    st.markdown("---")
    st.markdown("**Scoring focuses on:**")
    st.markdown("- Strong 1-week & 1-month momentum")
    st.markdown("- Rising / elevated volume")
    st.markdown("- Healthy RSI (not extreme)")
    st.markdown("- Above key moving averages")
    st.markdown("- Near 52-week highs (breakout potential)")

# Session state for results
if "results" not in st.session_state:
    st.session_state.results = None
    st.session_state.last_run = None

if run_button:
    with st.spinner("Downloading data and calculating scores... (30-90 seconds)"):
        if universe == "S&P 500 (full)":
            tickers = get_sp500_tickers()
        elif universe == "Quick liquid list (faster)":
            tickers = [
                "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "BRK-B",
                "JPM", "V", "UNH", "XOM", "LLY", "AVGO", "MA", "HD", "COST",
                "ABBV", "PEP", "KO", "WMT", "BAC", "CRM", "AMD", "QCOM", "INTU",
                "ISRG", "NOW", "ADBE", "NFLX", "ORCL", "CSCO", "IBM", "GE", "CAT"
            ]
        else:
            tickers = custom_tickers or []

        results = run_screener(tickers=tickers, top_n=
