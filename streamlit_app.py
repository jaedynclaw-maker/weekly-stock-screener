"""
Weekly Stock Opportunity Screener - Polished Dashboard
Apple-style UI + Watchlist + NZD prices + ASX support
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from stock_screener_core import (
    run_screener,
    get_sp500_tickers,
    get_higher_risk_tickers,
    get_asx_tickers,
    generate_report,
    enrich_top_stocks,
    get_ipo_calendar,
    get_watchlist_history,
    get_usd_nzd_rate
)

st.set_page_config(
    page_title="Weekly Stock Opportunities",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Clean Apple-style CSS ----------
st.markdown("""
<style>
    .stApp { background-color: #0d0d0f; color: #f5f5f7; }
    .main-header { font-size: 2.1rem; font-weight: 700; color: #f5f5f7; letter-spacing: -0.5px; margin-bottom: 0.15rem; }
    .sub-header { font-size: 1.05rem; color: #8e8e93; margin-bottom: 1.5rem; }
    .bubble-card {
        background: #1c1c1e; border-radius: 18px; padding: 1.3rem 1.4rem;
        margin-bottom: 1rem; border: 1px solid #2c2c2e;
        box-shadow: 0 6px 22px rgba(0,0,0,0.28);
    }
    .bubble-card-title { font-size: 1.15rem; font-weight: 600; color: #f5f5f7; margin-bottom: 0.5rem; }
    .metric-label { font-size: 0.82rem; color: #8e8e93; margin-bottom: 0.15rem; }
    .metric-value { font-size: 1.7rem; font-weight: 650; color: #f5f5f7; letter-spacing: -0.5px; }
    .score-highlight { color: #30d158; font-weight: 700; }
    .section-header { font-size: 1.3rem; font-weight: 600; color: #f5f5f7; margin: 1.6rem 0 0.9rem 0; }
    .why-text { color: #d1d1d6; font-size: 0.94rem; line-height: 1.5; }
    .success-pill {
        background: #13251a; border: 1px solid #1e3a29; border-radius: 14px;
        padding: 0.8rem 1.2rem; color: #30d158; font-weight: 500; margin-bottom: 1.1rem;
    }
    .info-box {
        background: #1c1c1e; border-left: 4px solid #30d158; border-radius: 10px;
        padding: 1rem 1.2rem; margin-bottom: 1rem; color: #d1d1d6;
    }
    #MainMenu, footer {visibility: hidden;}
    section[data-testid="stSidebar"] { background-color: #161618; }
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.markdown('<p class="main-header">Weekly Stock Opportunity Screener</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Strong momentum + rising volume · Prices shown in USD & NZD</p>', unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### Settings")
    top_n = st.slider("Number of top stocks", 5, 25, 12)
    min_price = st.number_input("Minimum price (USD)", min_value=1.0, value=5.0, step=1.0)

    universe = st.radio(
        "Market / Universe",
        ["S&P 500 (US Large Cap)", "Higher-risk US stocks", "ASX (Australia)", "Custom tickers"]
    )

    custom_tickers = None
    if universe == "Custom tickers":
        custom_input = st.text_area(
            "Enter tickers (comma separated)",
            value="AAPL,MSFT,NVDA,BHP.AX,CBA.AX,TSLA"
        )
        custom_tickers = [t.strip().upper() for t in custom_input.split(",") if t.strip()]

    run_button = st.button("Run Screener", type="primary", use_container_width=True)

    st.markdown("---")
    st.markdown("**What a high score means**")
    st.markdown("""
    - Strong recent price momentum  
    - Rising trading volume  
    - Healthy technical position  
    - Lower chance of immediate large drop  
    """)
    st.caption("This is a research tool, not financial advice.")

# ---------- Session state ----------
if "results" not in st.session_state:
    st.session_state.results = None
    st.session_state.last_run = None
    st.session_state.top5_enriched = None
    st.session_state.universe_used = None
    st.session_state.ipo_df = None
    st.session_state.watchlist = ["AAPL", "NVDA", "MSFT", "BHP.AX", "CBA.AX"]
    st.session_state.watchlist_data = None
    st.session_state.usd_nzd = 1.70

# ---------- Run logic ----------
if run_button:
    with st.spinner("Downloading data and calculating scores... (this can take 30–90 seconds)"):
        if universe == "S&P 500 (US Large Cap)":
            tickers = get_sp500_tickers()
        elif universe == "Higher-risk US stocks":
            tickers = get_higher_risk_tickers()
        elif universe == "ASX (Australia)":
            tickers = get_asx_tickers()
        else:
            tickers = custom_tickers or []

        results = run_screener(tickers=tickers, top_n=top_n, min_price=min_price)
        st.session_state.results = results
        st.session_state.last_run = datetime.now()
        st.session_state.universe_used = universe
        st.session_state.usd_nzd = get_usd_nzd_rate()

        if not results.empty:
            with st.spinner("Getting company details for top stocks..."):
                st.session_state.top5_enriched = enrich_top_stocks(results, n=5)
        else:
            st.session_state.top5_enriched = None

# ---------- Tabs ----------
tab1, tab2, tab3, tab4 = st.tabs([
    "Main Opportunities",
    "Watchlist",
    "Upcoming IPOs",
    "How to use this"
])

# ==================== TAB 1: Main Opportunities ====================
with tab1:
    if st.session_state.results is not None and not st.session_state.results.empty:
        df = st.session_state.results
        rate = st.session_state.usd_nzd

        st.markdown(f"""
        <div class="success-pill">
            Scan finished at {st.session_state.last_run.strftime('%Y-%m-%d %H:%M')} · 
            Market: <b>{st.session_state.universe_used}</b> · 
            Showing top {len(df)} stocks · USD→NZD rate ≈ {rate:.3f}
        </div>
        """, unsafe_allow_html=True)

        # Key metrics
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"""
            <div class="bubble-card">
                <div class="metric-label">Highest Score</div>
                <div class="metric-value score-highlight">{df['score'].iloc[0]:.1f}</div>
                <div style="color:#8e8e93; font-size:0.9rem;">{df['ticker'].iloc[0]}</div>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="bubble-card">
                <div class="metric-label">Average 1-Week Move</div>
                <div class="metric-value">{df['ret_1w'].mean():+.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        with m3:
            high_vol = (df['rel_volume'] >= 1.3).sum()
            st.markdown(f"""
            <div class="bubble-card">
                <div class="metric-label">Stocks with Rising Volume</div>
                <div class="metric-value">{high_vol}</div>
            </div>
            """, unsafe_allow_html=True)
        with m4:
            above_50 = df['above_sma50'].sum()
            st.markdown(f"""
            <div class="bubble-card">
                <div class="metric-label">Above 50-day Average</div>
                <div class="metric-value">{above_50}/{len(df)}</div>
            </div>
            """, unsafe_allow_html=True)

        # Top 5 - Bold & Clear
        if st.session_state.top5_enriched is not None and not st.session_state.top5_enriched.empty:
            st.markdown('<p class="section-header">Top 5 Stocks Worth Looking At</p>', unsafe_allow_html=True)
            st.markdown("""
            <div class="info-box">
                These are the highest-scoring stocks from this scan.  
                They currently show the strongest combination of recent momentum + rising volume while still looking reasonably healthy on the chart.
            </div>
            """, unsafe_allow_html=True)

            for _, row in st.session_state.top5_enriched.iterrows():
                price_usd = row['price']
                price_nzd = price_usd * rate
                is_asx = ".AX" in str(row['ticker'])

                st.markdown(f"""
                <div class="bubble-card">
                    <div class="bubble-card-title">
                        #{int(row['rank'])} &nbsp; {row['ticker']} &nbsp;·&nbsp; {row['company_name']}
                    </div>
                    <div style="display:flex; gap:1.5rem; flex-wrap:wrap; margin-bottom:0.7rem; color:#a1a1a6; font-size:0.9rem;">
                        <span><b style="color:#f5f5f7;">Sector</b> {row['sector']}</span>
                        <span><b style="color:#f5f5f7;">Industry</b> {row['industry']}</span>
                        <span><b style="color:#f5f5f7;">Market Cap</b> {row['market_cap']}</span>
                        <span><b style="color:#30d158;">Score</b> {row['score']:.1f}</span>
                    </div>
                    <div style="color:#d1d1d6; font-size:0.95rem; margin-bottom:0.6rem;">
                        <b>Price</b> ${price_usd:.2f} USD &nbsp;≈&nbsp; <b>${price_nzd:.2f} NZD</b> &nbsp;·&nbsp;
                        <b>1 Week</b> {row['ret_1w']:+.1f}% &nbsp;·&nbsp;
                        <b>1 Month</b> {row['ret_1m']:+.1f}% &nbsp;·&nbsp;
                        <b>Volume</b> {row['rel_volume']:.2f}x &nbsp;·&nbsp;
                        <b>RSI</b> {row['rsi']:.0f}
                    </div>
                    <div style="color:#d1d1d6; font-size:0.93rem; margin-bottom:0.5rem;">
                        <b>Illustrative 4-week range</b> {row.get('illustrative_4w', 'N/A')} 
                        <span style="color:#8e8e93;">(rough estimate only)</span>
                    </div>
                    {f"<div class='why-text'><b>About the company</b> — {row['summary']}</div>" if row.get('summary') else ""}
                    <div class="why-text" style="margin-top:0.5rem;"><b>Why it ranked high this week</b> — {row['why']}</div>
                </div>
                """, unsafe_allow_html=True)

        # All Ranked Opportunities - Cleaner version
        st.markdown('<p class="section-header">All Ranked Opportunities</p>', unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box">
            Full list ranked by Opportunity Score.  
            Higher score = stronger recent momentum + rising volume + healthier technical picture.
        </div>
        """, unsafe_allow_html=True)

        # Create a cleaner display dataframe
        clean_df = df.copy()
        clean_df["Price NZD"] = (clean_df["price"] * rate).round(2)
        clean_df = clean_df.rename(columns={
            "rank": "Rank",
            "ticker": "Ticker",
            "score": "Score",
            "price": "Price USD",
            "ret_1w": "1 Week %",
            "ret_1m": "1 Month %",
            "ret_3m": "3 Month %",
            "rel_volume": "Rel Volume",
            "rsi": "RSI",
            "illustrative_4w": "Illustrative 4W"
        })

        show_cols = ["Rank", "Ticker", "Score", "Price USD", "Price NZD", "1 Week %", "1 Month %", 
                     "Rel Volume", "RSI", "Illustrative 4W"]
        show_cols = [c for c in show_cols if c in clean_df.columns]

        st.dataframe(
            clean_df[show_cols],
            use_container_width=True,
            height=420,
            column_config={
                "Score": st.column_config.NumberColumn(format="%.1f"),
                "Price USD": st.column_config.NumberColumn(format="$%.2f"),
                "Price NZD": st.column_config.NumberColumn(format="$%.2f"),
                "1 Week %": st.column_config.NumberColumn(format="%+.1f%%"),
                "1 Month %": st.column_config.NumberColumn(format="%+.1f%%"),
                "Rel Volume": st.column_config.NumberColumn(format="%.2fx"),
                "RSI": st.column_config.NumberColumn(format="%.0f"),
            }
        )

        st.caption("Illustrative 4W is a rough heuristic based on recent momentum and volatility — not a prediction.")

        # Charts
        st.markdown('<p class="section-header">Quick Visuals</p>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.bar(df.head(10), x="ticker", y="score", color="score",
                          color_continuous_scale=["#1c1c1e", "#30d158"], title="Top Scores")
            fig1.update_layout(showlegend=False, height=360, paper_bgcolor="rgba(0,0,0,0)",
                               plot_bgcolor="rgba(0,0,0,0)", font_color="#f5f5f7", title_font_color="#f5f5f7")
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            chart_df = df.dropna(subset=["ret_1w", "rel_volume", "score"])
            if not chart_df.empty:
                fig2 = px.scatter(chart_df, x="ret_1w", y="rel_volume", size="score", color="rsi",
                                  hover_name="ticker", color_continuous_scale="RdYlGn",
                                  title="Momentum vs Volume")
                fig2.update_layout(height=360, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                   font_color="#f5f5f7", title_font_color="#f5f5f7")
                st.plotly_chart(fig2, use_container_width=True)

        st.download_button("Download Full Results (CSV)", df.to_csv(index=False),
                           file_name=f"stock_opportunities_{datetime.now().strftime('%Y%m%d')}.csv")

    else:
        st.markdown("""
        <div class="bubble-card">
            <div class="bubble-card-title">Ready to scan</div>
            <div class="why-text">
                Choose a market in the sidebar and click <b>Run Screener</b>.  
                The app will find stocks currently showing strong momentum + rising volume.
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==================== TAB 2: Watchlist ====================
with tab2:
    st.markdown('<p class="section-header">Your Watchlist</p>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
        Add any stocks you want to follow.  
        Click Refresh to see their recent performance and current Opportunity Score.
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        new_ticker = st.text_input("Add a ticker (e.g. TSLA, BHP.AX, NVDA)", placeholder="Enter ticker")
    with col2:
        st.write("")
        st.write("")
        if st.button("Add to Watchlist", use_container_width=True) and new_ticker:
            t = new_ticker.strip().upper()
            if t and t not in st.session_state.watchlist:
                st.session_state.watchlist.append(t)
                st.success(f"Added {t}")

    if st.session_state.watchlist:
        st.markdown("**Current Watchlist**")
        cols = st.columns(min(6, len(st.session_state.watchlist)))
        for i, t in enumerate(st.session_state.watchlist):
            with cols[i % 6]:
                if st.button(f"✕ {t}", key=f"rm_{t}"):
                    st.session_state.watchlist.remove(t)
                    st.rerun()

    if st.button("Refresh Watchlist Data", type="primary"):
        with st.spinner("Loading recent data for your watchlist..."):
            st.session_state.watchlist_data = get_watchlist_history(st.session_state.watchlist)
            st.session_state.usd_nzd = get_usd_nzd_rate()

    if st.session_state.watchlist_data is not None and not st.session_state.watchlist_data.empty:
        wdf = st.session_state.watchlist_data.copy()
        rate = st.session_state.usd_nzd
        wdf["Price NZD"] = (wdf["price"] * rate).round(2)

        st.markdown("### Recent Performance")
        st.dataframe(
            wdf[["ticker", "price", "Price NZD", "ret_1w", "ret_1m", "ret_3m", "rel_volume", "rsi", "score", "illustrative_4w"]].rename(columns={
                "ticker": "Ticker", "price": "Price USD", "ret_1w": "1W %", "ret_1m": "1M %",
                "ret_3m": "3M %", "rel_volume": "Rel Vol", "rsi": "RSI", "score": "Score",
                "illustrative_4w": "Illustrative 4W"
            }),
            use_container_width=True,
            column_config={
                "1W %": st.column_config.NumberColumn(format="%+.1f"),
                "1M %": st.column_config.NumberColumn(format="%+.1f"),
                "3M %": st.column_config.NumberColumn(format="%+.1f"),
                "Rel Vol": st.column_config.NumberColumn(format="%.2fx"),
                "Score": st.column_config.NumberColumn(format="%.1f"),
                "Price USD": st.column_config.NumberColumn(format="$%.2f"),
                "Price NZD": st.column_config.NumberColumn(format="$%.2f"),
            }
        )

        fig = px.bar(wdf, x="ticker", y="ret_1w", color="ret_1w",
                     color_continuous_scale=["#ff453a", "#30d158"], title="1-Week Performance of Watchlist")
        fig.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#f5f5f7", title_font_color="#f5f5f7", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Add some tickers and click **Refresh Watchlist Data**.")

# ==================== TAB 3: IPOs ====================
with tab3:
    st.markdown('<p class="section-header">Upcoming & Recent IPOs</p>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
        New companies coming to the market.  
        These cannot be scored the same way until they start trading (no price history yet).
    </div>
    """, unsafe_allow_html=True)

    if st.button("Refresh IPO Calendar"):
        with st.spinner("Fetching IPO data..."):
            st.session_state.ipo_df = get_ipo_calendar(limit=40)

    if st.session_state.ipo_df is not None and not st.session_state.ipo_df.empty:
        st.dataframe(st.session_state.ipo_df, use_container_width=True, height=450)
    else:
        st.info("Click **Refresh IPO Calendar** to load the latest available data.")

# ==================== TAB 4: How to use ====================
with tab4:
    st.markdown('<p class="section-header">How to use this tool</p>', unsafe_allow_html=True)
    st.markdown("""
    <div class="bubble-card">
        <div class="bubble-card-title">Simple weekly routine</div>
        <div class="why-text">
            1. Choose a market (S&P 500, Higher-risk, or ASX)<br>
            2. Click <b>Run Screener</b><br>
            3. Look at the Top 5 first — these currently have the strongest combination of momentum + volume<br>
            4. Check the full ranked list for more ideas<br>
            5. Add interesting names to your Watchlist so you can track them easily<br><br>
            <b>Best time to run:</b> Friday evening or Saturday (NZ time) after US markets close.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    **What the score is trying to find**  
    Stocks that are already moving with conviction (strong recent price rise + rising volume) while still looking reasonably healthy on the chart (not extremely overbought, still above key moving averages).

    **Important**  
    This is a research and idea-generation tool only.  
    It is **not** financial advice.  
    Past performance does not guarantee future results.  
    Always do your own research and never invest money you cannot afford to lose.
    """)

st.markdown("---")
st.caption("Not financial advice. Prices in NZD are approximate using the latest available USD/NZD rate.")
