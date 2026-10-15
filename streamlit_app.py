"""
Weekly Stock Opportunity Screener - Streamlit Dashboard
Clean Apple-style cards + IPO section + Higher-risk smaller stocks + Illustrative potential
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from stock_screener_core import (
    run_screener,
    get_sp500_tickers,
    get_higher_risk_tickers,
    generate_report,
    enrich_top_stocks,
    get_ipo_calendar
)

st.set_page_config(
    page_title="Weekly Stock Opportunities",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Apple-inspired clean styling ----------
st.markdown("""
<style>
    .stApp {
        background-color: #0d0d0f;
        color: #f5f5f7;
    }
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #f5f5f7;
        letter-spacing: -0.5px;
        margin-bottom: 0.15rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #a1a1a6;
        margin-bottom: 1.8rem;
    }
    .bubble-card {
        background: #1c1c1e;
        border-radius: 18px;
        padding: 1.4rem 1.5rem;
        margin-bottom: 1.1rem;
        border: 1px solid #2c2c2e;
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    }
    .bubble-card-title {
        font-size: 1.15rem;
        font-weight: 600;
        color: #f5f5f7;
        margin-bottom: 0.6rem;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #8e8e93;
        margin-bottom: 0.15rem;
    }
    .metric-value {
        font-size: 1.7rem;
        font-weight: 600;
        color: #f5f5f7;
        letter-spacing: -0.5px;
    }
    .score-highlight {
        color: #30d158;
        font-weight: 700;
    }
    .section-header {
        font-size: 1.35rem;
        font-weight: 600;
        color: #f5f5f7;
        margin: 1.8rem 0 1rem 0;
        letter-spacing: -0.3px;
    }
    .why-text {
        color: #d1d1d6;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    section[data-testid="stSidebar"] {
        background-color: #161618;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.markdown('<p class="main-header">Weekly Stock Opportunity Screener</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Strong momentum + rising volume · Free Yahoo Finance data</p>', unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### Settings")
    top_n = st.slider("Number of top stocks", 5, 30, 12)
    min_price = st.number_input("Minimum price ($)", min_value=1.0, value=5.0, step=1.0)

    universe = st.radio(
        "Universe",
        [
            "S&P 500 (main)",
            "Higher-risk smaller stocks",
            "Custom tickers"
        ]
    )

    custom_tickers = None
    if universe == "Custom tickers":
        custom_input = st.text_area(
            "Enter tickers (comma separated)",
            value="AAPL,MSFT,NVDA,AMZN,GOOGL,META,TSLA,AMD,AVGO,JPM"
        )
        custom_tickers = [t.strip().upper() for t in custom_input.split(",") if t.strip()]

    run_button = st.button("Run Screener", type="primary", use_container_width=True)

    st.markdown("---")
    st.markdown("**What the score rewards**")
    st.markdown("""
    - Strong 1-week & 1-month price moves  
    - Rising / elevated volume  
    - Healthy RSI (roughly 55–70)  
    - Price above 50-day & 200-day MAs  
    - Trading near 52-week highs  
    """)
    st.caption("Higher score = stronger combination of momentum + volume with basic risk filters.")

# ---------- Session state ----------
if "results" not in st.session_state:
    st.session_state.results = None
    st.session_state.last_run = None
    st.session_state.top5_enriched = None
    st.session_state.universe_used = None

# ---------- Run logic ----------
if run_button:
    with st.spinner("Downloading data and calculating scores... (30–90 seconds)"):
        if universe == "S&P 500 (main)":
            tickers = get_sp500_tickers()
        elif universe == "Higher-risk smaller stocks":
            tickers = get_higher_risk_tickers()
        else:
            tickers = custom_tickers or []

        results = run_screener(tickers=tickers, top_n=top_n, min_price=min_price)
        st.session_state.results = results
        st.session_state.last_run = datetime.now()
        st.session_state.universe_used = universe

        if not results.empty:
            with st.spinner("Fetching company details for top 5..."):
                st.session_state.top5_enriched = enrich_top_stocks(results, n=5)
        else:
            st.session_state.top5_enriched = None

# ---------- Tabs ----------
tab1, tab2, tab3 = st.tabs([
    "Main Opportunities",
    "Upcoming & Recent IPOs",
    "Higher-Risk Smaller Stocks Info"
])

# ==================== TAB 1: Main Opportunities ====================
with tab1:
    if st.session_state.results is not None and not st.session_state.results.empty:
        df = st.session_state.results

        st.markdown(f"""
        <div class="bubble-card" style="background:#13251a; border-color:#1e3a29;">
            <span style="color:#30d158; font-weight:500;">
                Scan completed at {st.session_state.last_run.strftime('%Y-%m-%d %H:%M')} · 
                Universe: {st.session_state.universe_used} · Showing top {len(df)} opportunities
            </span>
        </div>
        """, unsafe_allow_html=True)

        # Key metrics
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"""
            <div class="bubble-card">
                <div class="metric-label">Top Score</div>
                <div class="metric-value score-highlight">{df['score'].iloc[0]:.1f}</div>
                <div style="color:#8e8e93; font-size:0.9rem; margin-top:0.3rem;">{df['ticker'].iloc[0]}</div>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            avg_1w = df['ret_1w'].mean()
            st.markdown(f"""
            <div class="bubble-card">
                <div class="metric-label">Avg 1-Week Return</div>
                <div class="metric-value">{avg_1w:+.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        with m3:
            high_vol = (df['rel_volume'] >= 1.3).sum()
            st.markdown(f"""
            <div class="bubble-card">
                <div
