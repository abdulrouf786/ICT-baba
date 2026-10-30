# ICT BABA GOLD — single-file Streamlit app
# Paste this entire file into GitHub as app.py. No separate requirements.txt needed.
import sys, subprocess, importlib.util

def ensure_package(import_name, package_name=None):
    if importlib.util.find_spec(import_name) is None:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name or import_name])

ensure_package("yfinance")
ensure_package("plotly")

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timezone

st.set_page_config(page_title="ICT Baba Gold", page_icon="🥇", layout="wide")
st.title("🥇 ICT BABA — XAUUSD GOLD")
st.caption("Gold spot OHLC chart • Yahoo Finance data • ICT-style reference markers")

TIMEFRAMES = {
    "1m": ("1m", "1d"), "5m": ("5m", "5d"), "15m": ("15m", "1mo"),
    "1h": ("60m", "3mo"), "4h": ("60m", "3mo")
}

@st.cache_data(ttl=15, show_spinner=False)
def fetch_gold(tf, refresh_token):
    interval, period = TIMEFRAMES[tf]
    data = yf.download("XAUUSD=X", interval=interval, period=period,
                       auto_adjust=False, progress=False, threads=False)
    if data is None or data.empty:
        return pd.DataFrame()
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    data.columns = [str(c).title() for c in data.columns]
    cols = ["Open", "High", "Low", "Close"]
    if not all(c in data.columns for c in cols):
        return pd.DataFrame()
    data = data[cols].apply(pd.to_numeric, errors="coerce").dropna()
    data.index = pd.to_datetime(data.index)
    if tf == "4h":
        data = data.resample("4h").agg(
            {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
        ).dropna()
    return data.tail(300)

with st.sidebar:
    st.header("Chart controls")
    tf = st.selectbox("Gold timeframe", ["1m", "5m", "15m", "1h", "4h"], index=1)
    count = st.slider("Candles", 50, 300, 180, 10)
    liquidity_on = st.checkbox("Liquidity sweep markers", True)
    fvg_on = st.checkbox("FVG markers", True)
    bos_on = st.checkbox("BOS markers", True)
    st.caption("Feed: Yahoo Finance XAUUSD=X. Availability and delay depend on provider.")

if st.button("🔄 Refresh Gold", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

with st.spinner("Gold OHLC candles load ho rahi hain..."):
    df = fetch_gold(tf, int(datetime.now().timestamp() // 15))

if df.empty:
    st.error("Gold data abhi provider se nahi mila. Refresh dabayein ya kuch dair baad dobara try karein.")
    st.info("Agar data baar-baar unavailable ho, broker ya paid market-data API ka feed connect karna hoga.")
    st.stop()

df = df.copy()
prior_high = df["High"].rolling(20, min_periods=5).max().shift(1)
prior_low = df["Low"].rolling(20, min_periods=5).min().shift(1)
df["BuySweep"] = (df["High"] > prior_high) & (df["Close"] < prior_high)
df["SellSweep"] = (df["Low"] < prior_low) & (df["Close"] > prior_low)
df["BullFVG"] = df["Low"] > df["High"].shift(2)
df["BearFVG"] = df["High"] < df["Low"].shift(2)
df["BullBOS"] = df["Close"] > df["High"].rolling(10).max().shift(1)
df["BearBOS"] = df["Close"] < df["Low"].rolling(10).min().shift(1)
df = df.tail(count)

last = df.iloc[-1]
previous = float(df["Close"].iloc[-2]) if len(df) > 1 else float(last["Close"])
price = float(last["Close"])
delta = price - previous
pct = delta / previous * 100 if previous else 0

a, b, c, d = st.columns(4)
a.metric("XAUUSD Gold", f"${price:,.2f}", f"{delta:+.2f} ({pct:+.2f}%)")
b.metric("Latest candle high", f"${float(last['High']):,.2f}")
c.metric("Latest candle low", f"${float(last['Low']):,.2f}")
d.metric("Timeframe", tf)

fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
    name="XAUUSD OHLC", increasing_line_color="#16a34a",
    decreasing_line_color="#dc2626", increasing_fillcolor="#16a34a",
    decreasing_fillcolor="#dc2626"
))

def add_markers(mask, y_col, name, color, symbol):
    pts = df[mask]
    if not pts.empty:
        fig.add_trace(go.Scatter(
            x=pts.index, y=pts[y_col], mode="markers", name=name,
            marker=dict(color=color, size=10, symbol=symbol)
        ))

if liquidity_on:
    add_markers(df["BuySweep"], "High", "Buy-side sweep", "#f59e0b", "triangle-down")
    add_markers(df["SellSweep"], "Low", "Sell-side sweep", "#06b6d4", "triangle-up")
if fvg_on:
    add_markers(df["BullFVG"], "Low", "Bullish FVG", "#22c55e", "circle")
    add_markers(df["BearFVG"], "High", "Bearish FVG", "#ef4444", "circle")
if bos_on:
    add_markers(df["BullBOS"], "Low", "Bullish BOS", "#15803d", "star")
    add_markers(df["BearBOS"], "High", "Bearish BOS", "#b91c1c", "star")

fig.update_layout(
    title=f"XAUUSD — {tf} Real OHLC Candles", height=650,
    xaxis_rangeslider_visible=False, margin=dict(l=8, r=8, t=55, b=8),
    legend=dict(orientation="h", y=1.02, x=0)
)
fig.update_yaxes(title="USD per troy ounce")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Recent candles")
st.dataframe(df[["Open", "High", "Low", "Close"]].tail(12).sort_index(ascending=False),
             use_container_width=True)
st.warning(
    "Data note: XAUUSD=X is Yahoo Finance's spot-gold symbol. Quotes may be delayed, "
    "and intraday history/availability can be limited. 4h candles are aggregated from 1h data. "
    "Sweep, FVG and BOS markers are simplified educational approximations, not guaranteed trade signals."
)
st.caption("Updated UTC: " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
