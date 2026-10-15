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

# ---------- Styling ----------
st.markdown("""
<style>
    .stApp { background-color: #0d0d0f; color: #f5f5f7; }
    .main-header { font-size: 2.1rem; font-weight: 700; color: #f5f5f7; letter-spacing: -0.5px; margin-bottom: 0.15rem; }
    .sub-header { font-size: 1.05rem; color: #a1a1a6; margin-bottom: 1.8rem; }
    .bubble-card {
        background: #1c1c1e; border-radius: 18px; padding: 1.4rem 1.5rem;
        margin-bottom: 1.1rem; border: 1px solid #2c2c2e;
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    }
    .bubble-card-title { font-size: 1.15rem; font-weight: 600; color: #f5f5f7; margin-bottom: 0.6rem; }
    .metric-label { font-size: 0.85rem; color: #8e8e93; margin-bottom: 0.15rem; }
    .metric-value { font-size: 1.7rem; font-weight: 600; color: #f5f5f7; letter-spacing: -0.5px; }
    .score-highlight { color: #30d158; font-weight: 700; }
    .section-header { font-size: 1.35rem; font-weight: 600; color: #f5f5f7; margin: 1.8rem 0 1rem 0; letter-spacing: -0.3px; }
    .why-text { color: #d1d1d6; font-size: 0.95rem; line-height: 1.5; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    section[data-testid="stSidebar"] { background-color: #161618; }
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
        ["S&P 500 (main)", "Higher-risk smaller stocks", "Custom tickers"]
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
    st.session_state.ipo_df = None

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

# ==================== TAB 1 ====================
with tab1:
    if st.session_state.results is not None and not st.session_state.results.empty:
        df = st.session_state.results

        st.success(f"Scan completed at {st.session_state.last_run.strftime('%Y-%m-%d %H:%M')} · Universe: {st.session_state.universe_used} · Showing top {len(df)} opportunities")

        # Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Top Score", f"{df['score'].iloc[0]:.1f}", df['ticker'].iloc[0])
        m2.metric("Avg 1-Week Return", f"{df['ret_1w'].mean():+.1f}%")
        m3.metric("Elevated Volume", f"{(df['rel_volume'] >= 1.3).sum()} stocks")
        m4.metric("Above 50-day MA", f"{df['above_sma50'].sum()}/{len(df)}")

        # Scoring explanation
        with st.expander("How the ranking & Top Score work", expanded=False):
            st.markdown("""
            **What the Opportunity Score measures**  
            It tries to answer: *“Which stocks are currently showing the strongest combination of recent price strength + rising interest (volume), while still looking reasonably healthy on the chart?”*

            **How points are awarded**
            - **1-week return** → heavily weighted (biggest driver)
            - **1-month return** → secondary boost
            - **Relative volume** ≥ 1.2–1.5× → big bonus
            - **Above 50-day & 200-day MAs** → trend quality
            - **RSI 55–70** → healthy momentum zone
            - **Near 52-week high** → breakout potential

            **Penalties**
            - Very low volume
            - Extremely overbought RSI (>75)
            - Price far below key moving averages

            **How to read the score**
            - **30+** → Very strong this week
            - **20–30** → Solid setup
            - **Below 15** → Weaker / mixed signals
            """)

        # ---------- Top 5 (safe version) ----------
        if st.session_state.top5_enriched is not None and not st.session_state.top5_enriched.empty:
            st.markdown("### Top 5 Ranked Stocks")

            for _, row in st.session_state.top5_enriched.iterrows():
                with st.container():
                    st.markdown(f"#### #{int(row['rank'])}  {row['ticker']}  ·  {row['company_name']}")

                    cols = st.columns(4)
                    cols[0].markdown(f"**Sector**  \n{row['sector']}")
                    cols[1].markdown(f"**Industry**  \n{row['industry']}")
                    cols[2].markdown(f"**Market Cap**  \n{row['market_cap']}")
                    cols[3].markdown(f"**Score**  \n{row['score']:.1f}")

                    st.markdown(
                        f"**Price** ${row['price']:.2f}  ·  "
                        f"**1W** {row['ret_1w']:+.1f}%  ·  "
                        f"**1M** {row['ret_1m']:+.1f}%  ·  "
                        f"**Rel Vol** {row['rel_volume']:.2f}x  ·  "
                        f"**RSI** {row['rsi']:.0f}  ·  "
                        f"**Illustrative 4W** {row.get('illustrative_4w', 'N/A')}"
                    )

                    if row.get("summary"):
                        st.markdown(f"**About** — {row['summary']}")

                    st.markdown(f"**Why it ranked high this week** — {row['why']}")
                    st.markdown("---")

        # Full table
        st.markdown("### All Ranked Opportunities")

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
            "dist_52w_high": "vs 52w High %",
            "illustrative_4w": "Illustrative 4W Potential"
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

        st.caption("⚠️ **Illustrative 4W Potential** is a rough heuristic only. It is **not** a forecast or financial advice.")

        # Charts
        st.markdown("### Visual Overview")
        c1, c2 = st.columns(2)

        with c1:
            fig1 = px.bar(
                df.head(12), x="ticker", y="score", color="score",
                color_continuous_scale=["#1c1c1e", "#30d158"],
                title="Opportunity Score Ranking"
            )
            fig1.update_layout(showlegend=False, height=400,
                               paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               font_color="#f5f5f7", title_font_color="#f5f5f7")
            st.plotly_chart(fig1, use_container_width=True)

        with c2:
            chart_df = df.dropna(subset=["ret_1w", "rel_volume", "score", "rsi"]).copy()
            if not chart_df.empty:
                fig2 = px.scatter(
                    chart_df, x="ret_1w", y="rel_volume", size="score", color="rsi",
                    hover_name="ticker", color_continuous_scale="RdYlGn",
                    title="Momentum vs Volume (size = Score)"
                )
                fig2.update_layout(height=400,
                                   paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                   font_color="#f5f5f7", title_font_color="#f5f5f7")
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Not enough data for the scatter chart.")

        st.markdown("### Score vs 1-Week Momentum")
        fig3 = px.scatter(
            df, x="ret_1w", y="score", size="rel_volume", color="rsi",
            hover_name="ticker", color_continuous_scale="RdYlGn",
            title="Higher score stocks tend to have stronger recent momentum + volume"
        )
        fig3.update_layout(height=420,
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="#f5f5f7", title_font_color="#f5f5f7")
        st.plotly_chart(fig3, use_container_width=True)

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
        st.info("Choose a universe in the sidebar and click **Run Screener**.")

# ==================== TAB 2: IPOs ====================
with tab2:
    st.markdown("### Upcoming & Recent IPOs")
    st.info("Upcoming IPOs cannot be scored the same way as listed stocks (no price/volume history yet). Once they start trading you can run the normal screener on them.")

    if st.button("Refresh IPO Calendar"):
        with st.spinner("Fetching IPO calendar..."):
            st.session_state.ipo_df = get_ipo_calendar(limit=40)

    if st.session_state.ipo_df is not None and not st.session_state.ipo_df.empty:
        st.dataframe(st.session_state.ipo_df, use_container_width=True, height=500)
        st.caption("Data from Yahoo Finance IPO calendar. Dates and details can change.")
    else:
        st.write("Click **Refresh IPO Calendar** to load the latest available data.")

# ==================== TAB 3 ====================
with tab3:
    st.markdown("### Higher-Risk Smaller Stocks")
    st.markdown("""
    Select **“Higher-risk smaller stocks”** in the sidebar and run the screener.  
    This uses a curated list of more volatile small/mid-cap and recent growth names.

    **What this category is for**
    - Smaller companies and higher-beta names
    - Recent high-growth or thematic stocks
    - Higher potential moves — and higher chance of large losses

    True early-stage start-ups rarely have enough free daily data for reliable technical scoring.  
    This list focuses on names that are already publicly traded and liquid enough to analyse.
    """)
    st.caption("Not financial advice. Higher-risk names can lose a large percentage of their value quickly.")

st.markdown("---")
st.caption("Not financial advice. Always do your own research. Illustrative potential numbers are rough heuristics only.")
