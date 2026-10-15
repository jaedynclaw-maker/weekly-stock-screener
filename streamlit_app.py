"""
Weekly Stock Opportunity Screener - Streamlit Dashboard
Clean Apple-style cards + Higher-risk + IPO calendar
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

# ---------- Polished Apple-style CSS ----------
st.markdown("""
<style>
    .stApp { background-color: #0d0d0f; color: #f5f5f7; }
    .main-header { font-size: 2.15rem; font-weight: 700; color: #f5f5f7; letter-spacing: -0.6px; margin-bottom: 0.1rem; }
    .sub-header { font-size: 1.05rem; color: #8e8e93; margin-bottom: 1.6rem; }
    .bubble-card {
        background: #1c1c1e; border-radius: 18px; padding: 1.35rem 1.45rem;
        margin-bottom: 1rem; border: 1px solid #2c2c2e;
        box-shadow: 0 6px 24px rgba(0,0,0,0.28);
    }
    .bubble-card-title { font-size: 1.12rem; font-weight: 600; color: #f5f5f7; margin-bottom: 0.55rem; }
    .metric-label { font-size: 0.82rem; color: #8e8e93; margin-bottom: 0.2rem; }
    .metric-value { font-size: 1.75rem; font-weight: 650; color: #f5f5f7; letter-spacing: -0.6px; }
    .score-highlight { color: #30d158; font-weight: 700; }
    .section-header { font-size: 1.32rem; font-weight: 600; color: #f5f5f7; margin: 1.7rem 0 0.9rem 0; letter-spacing: -0.3px; }
    .why-text { color: #d1d1d6; font-size: 0.94rem; line-height: 1.55; }
    .success-pill {
        background: #13251a; border: 1px solid #1e3a29; border-radius: 14px;
        padding: 0.85rem 1.2rem; color: #30d158; font-weight: 500; margin-bottom: 1.2rem;
    }
    #MainMenu, footer {visibility: hidden;}
    section[data-testid="stSidebar"] { background-color: #161618; border-right: 1px solid #2c2c2e; }
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
    - Strong 1-week & 1-month moves  
    - Rising / elevated volume  
    - Healthy RSI (≈55–70)  
    - Above 50-day & 200-day MAs  
    - Near 52-week highs  
    """)
    st.caption("Higher score = stronger momentum + volume with basic risk filters.")

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
    "Higher-Risk Info"
])

# ==================== TAB 1 ====================
with tab1:
    if st.session_state.results is not None and not st.session_state.results.empty:
        df = st.session_state.results

        st.markdown(f"""
        <div class="success-pill">
            Scan completed at {st.session_state.last_run.strftime('%Y-%m-%d %H:%M')} · 
            Universe: <b>{st.session_state.universe_used}</b> · Showing top {len(df)} opportunities
        </div>
        """, unsafe_allow_html=True)

        # Metrics
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"""
            <div class="bubble-card">
                <div class="metric-label">Top Score</div>
                <div class="metric-value score-highlight">{df['score'].iloc[0]:.1f}</div>
                <div style="color:#8e8e93; font-size:0.9rem; margin-top:0.25rem;">{df['ticker'].iloc[0]}</div>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="bubble-card">
                <div class="metric-label">Avg 1-Week Return</div>
                <div class="metric-value">{df['ret_1w'].mean():+.1f}%</div>
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

        # Scoring explanation
        with st.expander("How the ranking & Top Score work"):
            st.markdown("""
            **What the Opportunity Score measures**  
            It answers: *“Which stocks currently show the strongest combination of recent price strength + rising interest (volume), while still looking reasonably healthy on the chart?”*

            **Points awarded**
            - 1-week return (heavily weighted)
            - 1-month return
            - Relative volume ≥ 1.2–1.5×
            - Price above 50-day & 200-day MAs
            - RSI in the healthy 55–70 zone
            - Trading near 52-week highs

            **Penalties**
            - Very low volume
            - Extremely overbought RSI (>75)
            - Price far below key moving averages

            **Reading the score**
            - **30+** → Very strong this week
            - **20–30** → Solid setup
            - **Below 15** → Weaker / mixed signals
            """)

        # Top 5
        if st.session_state.top5_enriched is not None and not st.session_state.top5_enriched.empty:
            st.markdown('<p class="section-header">Top 5 Ranked Stocks</p>', unsafe_allow_html=True)

            for _, row in st.session_state.top5_enriched.iterrows():
                summary_html = f"<div class='why-text'><b>About</b> — {row['summary']}</div>" if row.get('summary') else ""
                why_html = f"<div class='why-text' style='margin-top:0.55rem;'><b>Why it ranked high</b> — {row['why']}</div>"

                st.markdown(f"""
                <div class="bubble-card">
                    <div class="bubble-card-title">#{int(row['rank'])} &nbsp; {row['ticker']} &nbsp;·&nbsp; {row['company_name']}</div>
                    <div style="display:flex; gap:1.4rem; flex-wrap:wrap; margin-bottom:0.7rem; color:#a1a1a6; font-size:0.9rem;">
                        <span><b style="color:#f5f5f7;">Sector</b> {row['sector']}</span>
                        <span><b style="color:#f5f5f7;">Industry</b> {row['industry']}</span>
                        <span><b style="color:#f5f5f7;">Market Cap</b> {row['market_cap']}</span>
                        <span><b style="color:#30d158;">Score</b> {row['score']:.1f}</span>
                    </div>
                    <div style="color:#d1d1d6; font-size:0.92rem; margin-bottom:0.65rem;">
                        <b>Price</b> ${row['price']:.2f} &nbsp;·&nbsp;
                        <b>1W</b> {row['ret_1w']:+.1f}% &nbsp;·&nbsp;
                        <b>1M</b> {row['ret_1m']:+.1f}% &nbsp;·&nbsp;
                        <b>Rel Vol</b> {row['rel_volume']:.2f}x &nbsp;·&nbsp;
                        <b>RSI</b> {row['rsi']:.0f} &nbsp;·&nbsp;
                        <b>Illustrative 4W</b> {row.get('illustrative_4w', 'N/A')}
                    </div>
                    {summary_html}
                    {why_html}
                </div>
                """, unsafe_allow_html=True)

        # Full table
        st.markdown('<p class="section-header">All Ranked Opportunities</p>', unsafe_allow_html=True)

        display_df = df.rename(columns={
            "rank": "Rank", "ticker": "Ticker", "score": "Score", "price": "Price ($)",
            "ret_1w": "1W %", "ret_1m": "1M %", "ret_3m": "3M %",
            "rel_volume": "Rel Volume", "rsi": "RSI",
            "dist_sma50": "vs 50SMA %", "dist_sma200": "vs 200SMA %",
            "dist_52w_high": "vs 52w High %", "illustrative_4w": "Illustrative 4W"
        })

        st.dataframe(display_df, use_container_width=True, height=460,
            column_config={
                "Score": st.column_config.NumberColumn(format="%.1f"),
                "Price ($)": st.column_config.NumberColumn(format="$%.2f"),
                "1W %": st.column_config.NumberColumn(format="%+.1f"),
                "1M %": st.column_config.NumberColumn(format="%+.1f"),
                "3M %": st.column_config.NumberColumn(format="%+.1f"),
                "Rel Volume": st.column_config.NumberColumn(format="%.2fx"),
                "RSI": st.column_config.NumberColumn(format="%.0f"),
            })

        st.caption("⚠️ Illustrative 4W is a rough heuristic only — not a forecast.")

        # Charts
        st.markdown('<p class="section-header">Visual Overview</p>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.bar(df.head(12), x="ticker", y="score", color="score",
                          color_continuous_scale=["#1c1c1e", "#30d158"], title="Opportunity Score")
            fig1.update_layout(showlegend=False, height=380, paper_bgcolor="rgba(0,0,0,0)",
                               plot_bgcolor="rgba(0,0,0,0)", font_color="#f5f5f7", title_font_color="#f5f5f7")
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            chart_df = df.dropna(subset=["ret_1w", "rel_volume", "score", "rsi"])
            if not chart_df.empty:
                fig2 = px.scatter(chart_df, x="ret_1w", y="rel_volume", size="score", color="rsi",
                                  hover_name="ticker", color_continuous_scale="RdYlGn",
                                  title="Momentum vs Volume")
                fig2.update_layout(height=380, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                   font_color="#f5f5f7", title_font_color="#f5f5f7")
                st.plotly_chart(fig2, use_container_width=True)

        with st.expander("Full Text Report"):
            st.code(generate_report(df, top_n=top_n), language=None)

        st.download_button("Download Results CSV", df.to_csv(index=False),
                           file_name=f"weekly_opportunities_{datetime.now().strftime('%Y%m%d')}.csv",
                           mime="text/csv")

    else:
        st.markdown("""
        <div class="bubble-card">
            <div class="bubble-card-title">Ready when you are</div>
            <div class="why-text">Choose a universe in the sidebar and click <b>Run Screener</b>.</div>
        </div>
        """, unsafe_allow_html=True)

# ==================== TAB 2: IPOs ====================
with tab2:
    st.markdown('<p class="section-header">Upcoming & Recent IPOs</p>', unsafe_allow_html=True)
    st.markdown("""
    <div class="bubble-card">
        <div class="why-text">
            Upcoming IPOs cannot be scored the same way (no price/volume history yet).  
            Once they start trading you can run the main screener on them.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Refresh IPO Calendar"):
        with st.spinner("Fetching IPO calendar..."):
            st.session_state.ipo_df = get_ipo_calendar(limit=40)

    if st.session_state.ipo_df is not None and not st.session_state.ipo_df.empty:
        st.dataframe(st.session_state.ipo_df, use_container_width=True, height=480)
    else:
        st.info("Click **Refresh IPO Calendar** to load the latest available data.")

# ==================== TAB 3: Higher-Risk Info ====================
with tab3:
    st.markdown('<p class="section-header">Higher-Risk Smaller Stocks</p>', unsafe_allow_html=True)
    st.markdown("""
    <div class="bubble-card">
        <div class="why-text">
            To see actual results for this category:<br><br>
            1. Go to the sidebar<br>
            2. Select <b>“Higher-risk smaller stocks”</b><br>
            3. Click <b>Run Screener</b><br><br>
            The results will appear in the <b>Main Opportunities</b> tab.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    **What this universe contains**
    - More volatile small/mid-cap names
    - Recent high-growth and thematic stocks
    - Higher potential moves and higher chance of large losses

    It still uses the same momentum + volume + risk-filter scoring logic as the main S&P 500 scan.
    """)

st.markdown("---")
st.caption("Not financial advice. Always do your own research. Illustrative numbers are rough heuristics only.")
