"""
Weekly Stock Opportunity Screener - Streamlit Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from stock_screener_core import run_screener, get_sp500_tickers, generate_report

st.set_page_config(
    page_title="Weekly Stock Opportunities",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">📈 Weekly Stock Opportunity Screener</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Strong momentum + rising volume · Free data (yfinance)</p>', unsafe_allow_html=True)

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

        results = run_screener(tickers=tickers, top_n=top_n, min_price=min_price)
        st.session_state.results = results
        st.session_state.last_run = datetime.now()

if st.session_state.results is not None and not st.session_state.results.empty:
    df = st.session_state.results

    st.success(f"Scan completed at {st.session_state.last_run.strftime('%Y-%m-%d %H:%M')} · Showing top {len(df)} opportunities")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Top Score", f"{df['score'].iloc[0]:.1f}", df['ticker'].iloc[0])
    with col2:
        avg_1w = df['ret_1w'].mean()
        st.metric("Avg 1-Week Return", f"{avg_1w:+.1f}%")
    with col3:
        high_vol = (df['rel_volume'] >= 1.3).sum()
        st.metric("Elevated Volume", f"{high_vol} stocks")
    with col4:
        above_50 = df['above_sma50'].sum()
        st.metric("Above 50-day MA", f"{above_50}/{len(df)}")

    st.markdown("---")
    st.subheader("🏆 Ranked Opportunities")

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
        height=500,
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

    st.subheader("📊 Visual Overview")
    c1, c2 = st.columns(2)

    with c1:
        fig1 = px.bar(
            df.head(12),
            x="ticker",
            y="score",
            color="score",
            color_continuous_scale="Greens",
            title="Opportunity Score Ranking"
        )
        fig1.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        fig2 = px.scatter(
            df,
            x="ret_1w",
            y="rel_volume",
            size="score",
            color="rsi",
            hover_name="ticker",
            color_continuous_scale="RdYlGn",
            title="Momentum vs Volume (size = Score)"
        )
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)

    with st.expander("📄 Full Text Report", expanded=False):
        st.code(generate_report(df, top_n=top_n), language=None)

    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Results CSV",
        data=csv,
        file_name=f"weekly_opportunities_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

else:
    st.info("👈 Adjust settings in the sidebar and click **Run Screener** to generate this week's opportunities.")
    st.markdown("""
    ### How it works
    1. Pulls free daily data from Yahoo Finance
    2. Calculates momentum, relative volume, RSI and trend
    3. Scores stocks with focus on strong momentum + rising volume
    4. Applies filters to reduce downside risk
    5. Shows the most promising names

    **Tip:** Run it once a week (Friday evening or Saturday NZ time).
    """)

st.markdown("---")
st.caption("Not financial advice. Always do your own research.")
