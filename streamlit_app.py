"""
Weekly Stock Opportunity Screener - Modern Dashboard
Clean portfolio-style UI + Watchlist with search + NZD + change tracking
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from stock_screener_core import (
    run_screener, get_sp500_tickers, get_higher_risk_tickers, get_asx_tickers,
    generate_report, enrich_top_stocks, get_ipo_calendar,
    get_watchlist_history, get_usd_nzd_rate, search_companies, get_company_info
)

st.set_page_config(page_title="Stock Opportunities", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

# ---------- Modern CSS ----------
st.markdown("""
<style>
    .stApp { background-color: #0f0f12; color: #f5f5f7; }
    .main-title { font-size: 1.9rem; font-weight: 700; color: #ffffff; letter-spacing: -0.5px; margin-bottom: 0.2rem; }
    .sub-title { font-size: 0.95rem; color: #8e8e93; margin-bottom: 1.4rem; }
    .card {
        background: #1c1c1e;
        border-radius: 16px;
        padding: 1.25rem 1.4rem;
        margin-bottom: 0.9rem;
        border: 1px solid #2c2c2e;
    }
    .card-title { font-size: 1.15rem; font-weight: 600; color: #ffffff; margin-bottom: 0.35rem; }
    .ticker-badge {
        display: inline-block;
        background: #2c2c2e;
        color: #30d158;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 0.15rem 0.55rem;
        border-radius: 6px;
        margin-right: 0.5rem;
    }
    .metric-label { font-size: 0.78rem; color: #8e8e93; margin-bottom: 0.1rem; }
    .metric-value { font-size: 1.55rem; font-weight: 650; color: #ffffff; }
    .green { color: #30d158; }
    .red { color: #ff453a; }
    .section { font-size: 1.25rem; font-weight: 600; color: #ffffff; margin: 1.5rem 0 0.8rem 0; }
    .info { background: #1c1c1e; border-left: 4px solid #30d158; padding: 0.9rem 1.1rem; border-radius: 10px; color: #d1d1d6; margin-bottom: 1rem; }
    .change-up { background: #13251a; color: #30d158; padding: 0.2rem 0.55rem; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
    .change-down { background: #2a1215; color: #ff453a; padding: 0.2rem 0.55rem; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
    #MainMenu, footer {visibility: hidden;}
    section[data-testid="stSidebar"] { background-color: #161618; }
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.markdown('<p class="main-title">Weekly Stock Opportunities</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Momentum + Volume Screener · Prices in USD & NZD</p>', unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### Settings")
    top_n = st.slider("Top stocks to show", 5, 20, 10)
    min_price = st.number_input("Min price (USD)", 1.0, 500.0, 5.0, 1.0)

    universe = st.radio("Market", [
        "S&P 500 (US)",
        "Higher-risk US",
        "ASX (Australia)",
        "Custom"
    ])

    custom_tickers = None
    if universe == "Custom":
        raw = st.text_area("Tickers (comma separated)", "AAPL,MSFT,NVDA,BHP.AX,CBA.AX")
        custom_tickers = [t.strip().upper() for t in raw.split(",") if t.strip()]

    run_btn = st.button("Run Screener", type="primary", use_container_width=True)

    st.markdown("---")
    st.caption("Higher score = stronger recent momentum + rising volume while still looking healthy on the chart.")

# ---------- Session state ----------
if "results" not in st.session_state:
    st.session_state.results = None
    st.session_state.last_run = None
    st.session_state.top5 = None
    st.session_state.universe = None
    st.session_state.ipo_df = None
    st.session_state.watchlist = ["AAPL", "NVDA", "MSFT", "BHP.AX", "CBA.AX"]
    st.session_state.watchlist_data = None
    st.session_state.prev_prices = {}          # for change tracking
    st.session_state.usd_nzd = 1.70
    st.session_state.page = "Opportunities"

# ---------- Run screener ----------
if run_btn:
    with st.spinner("Scanning market... 30–90 seconds"):
        if universe == "S&P 500 (US)":
            tickers = get_sp500_tickers()
        elif universe == "Higher-risk US":
            tickers = get_higher_risk_tickers()
        elif universe == "ASX (Australia)":
            tickers = get_asx_tickers()
        else:
            tickers = custom_tickers or []

        results = run_screener(tickers=tickers, top_n=top_n, min_price=min_price)
        st.session_state.results = results
        st.session_state.last_run = datetime.now()
        st.session_state.universe = universe
        st.session_state.usd_nzd = get_usd_nzd_rate()

        if not results.empty:
            st.session_state.top5 = enrich_top_stocks(results, n=5)
        else:
            st.session_state.top5 = None

# ---------- Bottom-style navigation ----------
st.markdown("---")
nav = st.radio(
    "Navigation",
    ["Opportunities", "Watchlist", "IPOs", "Guide"],
    horizontal=True,
    label_visibility="collapsed",
    key="nav"
)
st.session_state.page = nav
st.markdown("---")

rate = st.session_state.usd_nzd

# ==================== PAGE: Opportunities ====================
if st.session_state.page == "Opportunities":
    if st.session_state.results is not None and not st.session_state.results.empty:
        df = st.session_state.results

        st.markdown(f"""
        <div class="info">
            Scan finished · {st.session_state.last_run.strftime('%Y-%m-%d %H:%M')} · 
            Market: <b>{st.session_state.universe}</b> · USD→NZD ≈ {rate:.3f}
        </div>
        """, unsafe_allow_html=True)

        # Top metrics
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class="card">
                <div class="metric-label">Top Score</div>
                <div class="metric-value green">{df['score'].iloc[0]:.1f}</div>
                <div style="color:#8e8e93;font-size:0.85rem;">{df['ticker'].iloc[0]}</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="card">
                <div class="metric-label">Avg 1-Week</div>
                <div class="metric-value">{df['ret_1w'].mean():+.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            high_vol = (df['rel_volume'] >= 1.3).sum()
            st.markdown(f"""
            <div class="card">
                <div class="metric-label">Rising Volume</div>
                <div class="metric-value">{high_vol}</div>
            </div>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="card">
                <div class="metric-label">Above 50-day MA</div>
                <div class="metric-value">{df['above_sma50'].sum()}/{len(df)}</div>
            </div>
            """, unsafe_allow_html=True)

        # Top 5 cards
        if st.session_state.top5 is not None and not st.session_state.top5.empty:
            st.markdown('<p class="section">Top Opportunities</p>', unsafe_allow_html=True)

            for _, row in st.session_state.top5.iterrows():
                price_usd = row["price"]
                price_nzd = price_usd * rate
                name = row.get("company_name", row["ticker"])

                st.markdown(f"""
                <div class="card">
                    <div class="card-title">
                        <span class="ticker-badge">{row['ticker']}</span>
                        {name}
                    </div>
                    <div style="color:#a1a1a6;font-size:0.88rem;margin-bottom:0.6rem;">
                        {row.get('sector','')} · {row.get('industry','')} · Market Cap {row.get('market_cap','N/A')}
                    </div>
                    <div style="display:flex;gap:1.5rem;flex-wrap:wrap;margin-bottom:0.6rem;">
                        <div><span style="color:#8e8e93;">Price</span><br>
                            <b>${price_usd:.2f}</b> USD &nbsp;≈&nbsp; <b>${price_nzd:.2f}</b> NZD
                        </div>
                        <div><span style="color:#8e8e93;">1 Week</span><br>
                            <b class="{'green' if row['ret_1w']>=0 else 'red'}">{row['ret_1w']:+.1f}%</b>
                        </div>
                        <div><span style="color:#8e8e93;">1 Month</span><br>
                            <b class="{'green' if row['ret_1m']>=0 else 'red'}">{row['ret_1m']:+.1f}%</b>
                        </div>
                        <div><span style="color:#8e8e93;">Volume</span><br>
                            <b>{row['rel_volume']:.2f}x</b>
                        </div>
                        <div><span style="color:#8e8e93;">Score</span><br>
                            <b class="green">{row['score']:.1f}</b>
                        </div>
                    </div>
                    <div style="color:#d1d1d6;font-size:0.9rem;margin-bottom:0.4rem;">
                        <b>Illustrative 4-week range:</b> {row.get('illustrative_4w','N/A')}
                    </div>
                    {f"<div style='color:#d1d1d6;font-size:0.9rem;margin-bottom:0.4rem;'><b>About:</b> {row['summary']}</div>" if row.get('summary') else ""}
                    <div style="color:#d1d1d6;font-size:0.9rem;">
                        <b>Why it ranked high:</b> {row.get('why','')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Full ranked table
        st.markdown('<p class="section">All Ranked Opportunities</p>', unsafe_allow_html=True)

        display = df.copy()
        display["Price NZD"] = (display["price"] * rate).round(2)
        display["Company"] = display["ticker"].map(lambda t: get_company_info(t)["name"])

        show = display[["rank", "ticker", "Company", "score", "price", "Price NZD", "ret_1w", "ret_1m", "rel_volume", "rsi", "illustrative_4w"]].rename(columns={
            "rank": "Rank", "ticker": "Ticker", "score": "Score",
            "price": "USD", "ret_1w": "1W %", "ret_1m": "1M %",
            "rel_volume": "Vol", "rsi": "RSI", "illustrative_4w": "4W Range"
        })

        st.dataframe(show, use_container_width=True, height=400,
            column_config={
                "Score": st.column_config.NumberColumn(format="%.1f"),
                "USD": st.column_config.NumberColumn(format="$%.2f"),
                "Price NZD": st.column_config.NumberColumn(format="$%.2f"),
                "1W %": st.column_config.NumberColumn(format="%+.1f%%"),
                "1M %": st.column_config.NumberColumn(format="%+.1f%%"),
                "Vol": st.column_config.NumberColumn(format="%.2fx"),
                "RSI": st.column_config.NumberColumn(format="%.0f"),
            })

        # Charts
        st.markdown('<p class="section">Charts</p>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.bar(df.head(10), x="ticker", y="score", color="score",
                          color_continuous_scale=["#1c1c1e", "#30d158"], title="Opportunity Score")
            fig1.update_layout(height=420, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               font_color="#f5f5f7", title_font_color="#ffffff", showlegend=False)
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.scatter(df.dropna(subset=["ret_1w","rel_volume"]), x="ret_1w", y="rel_volume",
                              size="score", color="rsi", hover_name="ticker",
                              color_continuous_scale="RdYlGn", title="Momentum vs Volume")
            fig2.update_layout(height=420, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               font_color="#f5f5f7", title_font_color="#ffffff")
            st.plotly_chart(fig2, use_container_width=True)

        st.download_button("Download CSV", df.to_csv(index=False),
                           file_name=f"opportunities_{datetime.now().strftime('%Y%m%d')}.csv")

    else:
        st.markdown("""
        <div class="card">
            <div class="card-title">Ready to scan</div>
            <div style="color:#d1d1d6;">Choose a market in the sidebar and click <b>Run Screener</b>.</div>
        </div>
        """, unsafe_allow_html=True)

# ==================== PAGE: Watchlist ====================
elif st.session_state.page == "Watchlist":
    st.markdown('<p class="section">Your Watchlist</p>', unsafe_allow_html=True)

    # Search box
    search_q = st.text_input("Search companies (e.g. Tesla, Apple, BHP)", placeholder="Type company name or ticker...")
    if search_q:
        suggestions = search_companies(search_q)
        if suggestions:
            st.markdown("**Suggestions**")
            for s in suggestions:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{s['ticker']}** — {s['name']}")
                with col2:
                    if st.button("Add", key=f"add_{s['ticker']}"):
                        if s['ticker'] not in st.session_state.watchlist:
                            st.session_state.watchlist.append(s['ticker'])
                            st.success(f"Added {s['ticker']}")
                            st.rerun()

    # Current list + remove
    if st.session_state.watchlist:
        st.markdown("**Current list**")
        cols = st.columns(min(5, len(st.session_state.watchlist)))
        for i, t in enumerate(st.session_state.watchlist):
            with cols[i % 5]:
                if st.button(f"✕ {t}", key=f"rm_{t}"):
                    st.session_state.watchlist.remove(t)
                    st.rerun()

    if st.button("Refresh Watchlist", type="primary"):
        with st.spinner("Updating watchlist..."):
            # Save previous prices for change tracking
            if st.session_state.watchlist_data is not None:
                for _, row in st.session_state.watchlist_data.iterrows():
                    st.session_state.prev_prices[row["ticker"]] = row["price"]

            st.session_state.watchlist_data = get_watchlist_history(st.session_state.watchlist)
            st.session_state.usd_nzd = get_usd_nzd_rate()

    if st.session_state.watchlist_data is not None and not st.session_state.watchlist_data.empty:
        wdf = st.session_state.watchlist_data.copy()
        rate = st.session_state.usd_nzd

        st.markdown("### Performance since last check")

        for _, row in wdf.iterrows():
            ticker = row["ticker"]
            name = row.get("company_name", ticker)
            price = row["price"]
            price_nzd = price * rate
            prev = st.session_state.prev_prices.get(ticker)

            change_html = ""
            if prev is not None and prev > 0:
                chg = price - prev
                chg_pct = (chg / prev) * 100
                cls = "change-up" if chg >= 0 else "change-down"
                change_html = f'<span class="{cls}">{chg:+.2f} ({chg_pct:+.1f}%)</span>'

            st.markdown(f"""
            <div class="card">
                <div class="card-title">
                    <span class="ticker-badge">{ticker}</span> {name}
                </div>
                <div style="display:flex;gap:1.8rem;flex-wrap:wrap;align-items:center;">
                    <div>
                        <span style="color:#8e8e93;font-size:0.8rem;">Price</span><br>
                        <b>${price:.2f}</b> USD · <b>${price_nzd:.2f}</b> NZD
                    </div>
                    <div>
                        <span style="color:#8e8e93;font-size:0.8rem;">1 Week</span><br>
                        <b class="{'green' if row['ret_1w']>=0 else 'red'}">{row['ret_1w']:+.1f}%</b>
                    </div>
                    <div>
                        <span style="color:#8e8e93;font-size:0.8rem;">1 Month</span><br>
                        <b class="{'green' if row['ret_1m']>=0 else 'red'}">{row['ret_1m']:+.1f}%</b>
                    </div>
                    <div>
                        <span style="color:#8e8e93;font-size:0.8rem;">Score</span><br>
                        <b>{row['score']:.1f}</b>
                    </div>
                    <div>
                        <span style="color:#8e8e93;font-size:0.8rem;">Since last check</span><br>
                        {change_html if change_html else "<span style='color:#8e8e93;'>First check</span>"}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Chart
        fig = px.bar(wdf, x="ticker", y="ret_1w", color="ret_1w",
                     color_continuous_scale=["#ff453a", "#30d158"], title="1-Week Return")
        fig.update_layout(height=380, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#f5f5f7", title_font_color="#ffffff", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Add stocks using the search box above, then click **Refresh Watchlist**.")

# ==================== PAGE: IPOs ====================
elif st.session_state.page == "IPOs":
    st.markdown('<p class="section">Upcoming & Recent IPOs</p>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info">
        New companies coming to market. These cannot be fully scored until they start trading.
    </div>
    """, unsafe_allow_html=True)

    if st.button("Refresh IPO Calendar"):
        with st.spinner("Loading..."):
            st.session_state.ipo_df = get_ipo_calendar(limit=40)

    if st.session_state.ipo_df is not None and not st.session_state.ipo_df.empty:
        st.dataframe(st.session_state.ipo_df, use_container_width=True, height=450)
    else:
        st.info("Click **Refresh IPO Calendar** to load data.")

# ==================== PAGE: Guide ====================
else:
    st.markdown('<p class="section">How to use this app</p>', unsafe_allow_html=True)
    st.markdown("""
    <div class="card">
        <div class="card-title">Weekly routine</div>
        <div style="color:#d1d1d6;line-height:1.6;">
            1. Choose a market in the sidebar<br>
            2. Click <b>Run Screener</b><br>
            3. Look at the <b>Top Opportunities</b> first<br>
            4. Add interesting names to your <b>Watchlist</b><br>
            5. Come back later and refresh the Watchlist to see what moved
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    **What the score looks for**  
    Stocks that are already moving with conviction (strong recent price rise + rising volume) while still looking reasonably healthy on the chart.

    **Important**  
    This is a research tool only. It is **not** financial advice.  
    Past performance does not guarantee future results.  
    Always do your own research.
    """)

st.markdown("---")
st.caption("Not financial advice · NZD prices are approximate · Data from Yahoo Finance")
