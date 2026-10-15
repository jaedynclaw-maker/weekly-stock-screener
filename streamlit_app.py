"""
Weekly Stock Opportunity Screener - Streamlit Dashboard
Clean Apple-style cards + clearer explanations
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from stock_screener_core import (
    run_screener, get_sp500_tickers, generate_report, enrich_top_stocks
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
    /* Overall background & text */
    .stApp {
        background-color: #0d0d0f;
        color: #f5f5f7;
    }
    
    /* Main header */
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

    /* Soft bubble / card style */
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
    
    /* Soft section headers */
    .section-header {
        font-size: 1.35rem;
        font-weight: 600;
        color: #f5f5f7;
        margin: 1.8rem 0 1rem 0;
        letter-spacing: -0.3px;
    }
    
    /* Why text */
    .why-text {
        color: #d1d1d6;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    
    /* Hide default Streamlit branding a bit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Sidebar cleaner */
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
        ["S&P 500 (full)", "Quick liquid list (faster)", "Custom tickers"]
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
    st.caption("Higher score = stronger combination of momentum + volume with lower downside risk filters.")

# ---------- Session state ----------
if "results" not in st.session_state:
    st.session_state.results = None
    st.session_state.last_run = None
    st.session_state.top5_enriched = None

# ---------- Run logic ----------
if run_button:
    with st.spinner("Downloading data and calculating scores... (30–90 seconds)"):
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

        results = run_screener(tickers=tickers, top_n=top_n, min_price=min_price)
        st.session_state.results = results
        st.session_state.last_run = datetime.now()

        if not results.empty:
            with st.spinner("Fetching company details for top 5..."):
                st.session_state.top5_enriched = enrich_top_stocks(results, n=5)
        else:
            st.session_state.top5_enriched = None

# ---------- Results ----------
if st.session_state.results is not None and not st.session_state.results.empty:
    df = st.session_state.results

    # Success message
    st.markdown(f"""
    <div class="bubble-card" style="background:#13251a; border-color:#1e3a29;">
        <span style="color:#30d158; font-weight:500;">
            Scan completed at {st.session_state.last_run.strftime('%Y-%m-%d %H:%M')} · Showing top {len(df)} opportunities
        </span>
    </div>
    """, unsafe_allow_html=True)

    # ---------- Key Metrics (bubble style) ----------
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
            <div class="metric-label">Elevated Volume</div>
            <div class="metric-value">{high_vol} stocks</div>
        </div>
        """, unsafe_allow_html=True)
    
    with m4:
        above_50 = df['above_sma50'].sum()
        st.markdown(f"""
        <div class="bubble-card">
            <div class="metric-label">Above 50-day MA</div>
            <div class="metric-value">{above_50}/{len(df)}</div>
        </div>
        """, unsafe_allow_html=True)

    # ---------- How scoring works (clear explanation) ----------
    with st.expander("How the ranking & Top Score work", expanded=False):
        st.markdown("""
        **What the Opportunity Score measures**  
        It is a single number that tries to answer:  
        *“Which stocks are currently showing the strongest combination of recent price strength + rising interest (volume), while still looking reasonably healthy on the chart?”*

        **How points are awarded (simplified)**
        - **1-week return** → heavily weighted (this is the biggest driver)
        - **1-month return** → solid secondary boost
        - **Relative volume** ≥ 1.2–1.5× average → big bonus (shows rising interest)
        - **Price above 50-day & 200-day moving averages** → trend quality points
        - **RSI between ~55–70** → healthy momentum zone (not extreme)
        - **Trading near 52-week high** → breakout potential bonus

        **What gets penalised**
        - Very low volume
        - Extremely overbought RSI (>75)
        - Price far below key moving averages

        **How to read the Top Score**
        - **30+** → Very strong combination this week
        - **20–30** → Solid momentum + volume setup
        - **Below 15** → Weaker or mixed signals

        The score is relative to the universe you scanned today. A high score means the stock stood out *this week* on the combination of momentum + volume with basic risk filters applied.
        """)

    # ---------- Top 5 Blurbs ----------
    if st.session_state.top5_enriched is not None and not st.session_state.top5_enriched.empty:
        st.markdown('<p class="section-header">Top 5 Ranked Stocks</p>', unsafe_allow_html=True)

        for _, row in st.session_state.top5_enriched.iterrows():
            st.markdown(f"""
            <div class="bubble-card">
                <div class="bubble-card-title">
                    #{int(row['rank'])} &nbsp; {row['ticker']} &nbsp;·&nbsp; {row['company_name']}
                </div>
                <div style="display:flex; gap:1.5rem; flex-wrap:wrap; margin-bottom:0.8rem; color:#a1a1a6; font-size:0.9rem;">
                    <span><b style="color:#f5f5f7;">Sector</b> {row['sector']}</span>
                    <span><b style="color:#f5f5f7;">Industry</b> {row['industry']}</span>
                    <span><b style="color:#f5f5f7;">Market Cap</b> {row['market_cap']}</span>
                    <span><b style="color:#30d158;">Score</b> {row['score']:.1f}</span>
                </div>
                <div style="color:#d1d1d6; font-size:0.92rem; margin-bottom:0.7rem;">
                    <b>Price</b> ${row['price']:.2f} &nbsp;·&nbsp;
                    <b>1W</b> {row['ret_1w']:+.1f}% &nbsp;·&nbsp;
                    <b>1M</b> {row['ret_1m']:+.1f}% &nbsp;·&nbsp;
                    <b>Rel Vol</b> {row['rel_volume']:.2f}x &nbsp;·&nbsp;
                    <b>RSI</b> {row['rsi']:.0f}
                </div>
            """, unsafe_allow_html=True)

            if row['summary']:
                st.markdown(f"<div class='why-text'><b>About</b> — {row['summary']}</div>", unsafe_allow_html=True)

            st.markdown(f"<div class='why-text' style='margin-top:0.6rem;'><b>Why it ranked high this week</b> — {row['why']}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # ---------- Full Ranked Table ----------
    st.markdown('<p class="section-header">All Ranked Opportunities</p>', unsafe_allow_html=True)

    display_df = df.copy()
    display_df = display_df.rename(columns={
        "rank": "Rank",
        "ticker": "Ticker",
        "score": "Score",
        "price": "Price ($)",
        "ret_1w": "1W %",
        "ret_1m": "1M %",
        "ret_3m": "3M %",
        "rel_volume": "Rel Volume",
        "rsi": "RSI",
        "dist_sma50": "vs 50SMA %",
        "dist_sma200": "vs 200SMA %",
        "dist_52w_high": "vs 52w High %"
    })

    st.dataframe(
        display_df,
        use_container_width=True,
        height=480,
        column_config={
            "Score": st.column_config.NumberColumn(format="%.1f"),
            "Price ($)": st.column_config.NumberColumn(format="$%.2f"),
            "1W %": st.column_config.NumberColumn(format="%+.1f"),
            "1M %": st.column_config.NumberColumn(format="%+.1f"),
            "3M %": st.column_config.NumberColumn(format="%+.1f"),
            "Rel Volume": st.column_config.NumberColumn(format="%.2fx"),
            "RSI": st.column_config.NumberColumn(format="%.0f"),
            "vs 50SMA %": st.column_config.NumberColumn(format="%+.1f"),
            "vs 200SMA %": st.column_config.NumberColumn(format="%+.1f"),
            "vs 52w High %": st.column_config.NumberColumn(format="%+.1f"),
        }
    )

    # ---------- Charts ----------
    st.markdown('<p class="section-header">Visual Overview</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        fig1 = px.bar(
            df.head(12),
            x="ticker",
            y="score",
            color="score",
            color_continuous_scale=["#1c1c1e", "#30d158"],
            title="Opportunity Score Ranking"
        )
        fig1.update_layout(
            showlegend=False,
            height=400,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#f5f5f7",
            title_font_color="#f5f5f7"
        )
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        chart_df = df.dropna(subset=["ret_1w", "rel_volume", "score", "rsi"]).copy()
        if not chart_df.empty:
            fig2 = px.scatter(
                chart_df,
                x="ret_1w",
                y="rel_volume",
                size="score",
                color="rsi",
                hover_name="ticker",
                color_continuous_scale="RdYlGn",
                title="Momentum vs Volume (size = Score)"
            )
            fig2.update_layout(
                height=400,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#f5f5f7",
                title_font_color="#f5f5f7"
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Not enough data for the scatter chart.")

    # ---------- Text report + download ----------
    with st.expander("Full Text Report"):
        st.code(generate_report(df, top_n=top_n), language=None)

    csv = df.to_csv(index=False)
    st.download_button(
        label="Download Results CSV",
        data=csv,
        file_name=f"weekly_opportunities_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

else:
    st.markdown("""
    <div class="bubble-card">
        <div class="bubble-card-title">Ready when you are</div>
        <div class="why-text">
            Adjust the settings in the sidebar and tap <b>Run Screener</b>.  
            The app will scan the market and surface the strongest momentum + volume setups with basic risk filters applied.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    ### How it works
    1. Pulls free daily data from Yahoo Finance  
    2. Calculates momentum, relative volume, RSI and trend  
    3. Scores stocks with focus on strong momentum + rising volume  
    4. Applies filters to reduce downside risk  
    5. Shows the most promising names + short company blurbs for the top 5  

    **Tip:** Run it once a week (Friday evening or Saturday NZ time).
    """)

st.markdown("---")
st.caption("Not financial advice. Always do your own research.")
