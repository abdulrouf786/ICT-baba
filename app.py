import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timezone

st.set_page_config(page_title="ICT Baba Gold", page_icon="🥇", layout="wide")

st.title("🥇 ICT BABA — XAUUSD GOLD")
st.caption("Gold spot (Yahoo Finance: XAUUSD=X) • OHLC candles • ICT-style market structure")

# Yahoo Finance intraday history is limited; 4h candles are built from 1h candles.
TIMEFRAMES = {
    "1m": ("1m", "1m", "1d"),
    "5m": ("5m", "5m", "5d"),
    "15m": ("15m", "15m", "1mo"),
    "1h": ("1h", "60m", "3mo"),
    "4h": ("4h", "60m", "3mo"),
}
PERIODS = {"1m": "1d", "5m": "5d", "15m": "1mo", "1h": "3mo", "4h": "3mo"}

@st.cache_data(ttl=10, show_spinner=False)
def get_gold_data(timeframe: str, refresh_key: int):
    interval = TIMEFRAMES[timeframe][1]
    period = PERIODS[timeframe]
    data = yf.download(
        "XAUUSD=X",
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
        prepost=True,
        threads=False,
    )
    if data is None or data.empty:
        return pd.DataFrame()
    # yfinance may return a MultiIndex column index, depending on its version.
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    data = data.rename(columns=str.title)
    needed = ["Open", "High", "Low", "Close"]
    if not all(c in data.columns for c in needed):
        return pd.DataFrame()
    data = data[needed].copy()
    data = data.apply(pd.to_numeric, errors="coerce").dropna()
    data.index = pd.to_datetime(data.index)
    if timeframe == "4h":
        data = data.resample("4h").agg({
            "Open": "first", "High": "max", "Low": "min", "Close": "last"
        }).dropna()
    return data.tail(300)

def add_ict_levels(df):
    """Simple, educational swing/liquidity and FVG approximations."""
    out = df.copy()
    out["SwingHigh"] = out["High"].rolling(5, center=True).max()
    out["SwingLow"] = out["Low"].rolling(5, center=True).min()
    highs = out["High"].rolling(20, min_periods=5).max().shift(1)
    lows = out["Low"].rolling(20, min_periods=5).min().shift(1)
    out["BuySideSweep"] = (out["High"] > highs) & (out["Close"] < highs)
    out["SellSideSweep"] = (out["Low"] < lows) & (out["Close"] > lows)
    out["BullFVG"] = out["Low"] > out["High"].shift(2)
    out["BearFVG"] = out["High"] < out["Low"].shift(2)
    # Basic structure-break markers; not a full discretionary ICT model.
    out["BullBOS"] = out["Close"] > out["High"].rolling(10).max().shift(1)
    out["BearBOS"] = out["Close"] < out["Low"].rolling(10).min().shift(1)
    return out

with st.sidebar:
    st.header("Chart settings")
    timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h"], index=1)
    candle_count = st.slider("Candles on chart", 50, 300, 180, 10)
    st.divider()
    show_liquidity = st.checkbox("Show liquidity sweeps", True)
    show_fvg = st.checkbox("Show FVG markers", True)
    show_structure = st.checkbox("Show BOS markers", True)
    st.caption("Data source: Yahoo Finance. Quotes may be delayed and intraday history is limited.")

if st.button("🔄 Refresh Gold data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

with st.spinner("Loading XAUUSD Gold candles..."):
    raw = get_gold_data(timeframe, int(datetime.now().timestamp() // 10))

if raw.empty:
    st.error(
        "Gold data load nahi hua. Thori dair baad Refresh dabayein. "
        "Yahoo Finance kabhi kabhi intraday data limit ya block karta hai."
    )
    st.info("Agar baar-baar error aaye, reliable live feed ke liye broker/market-data API key connect karni hogi.")
    st.stop()

df = add_ict_levels(raw).tail(candle_count)
last = df.iloc[-1]
prev_close = float(df["Close"].iloc[-2]) if len(df) > 1 else float(last["Close"])
change = float(last["Close"]) - prev_close
change_pct = (change / prev_close * 100) if prev_close else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("XAUUSD latest", f"${float(last['Close']):,.2f}", f"{change:+.2f} ({change_pct:+.2f}%)")
c2.metric("High", f"${float(last['High']):,.2f}")
c3.metric("Low", f"${float(last['Low']):,.2f}")
c4.metric("Last candle", str(df.index[-1])[:19])

fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
    name="XAUUSD OHLC",
    increasing_line_color="#16a34a", decreasing_line_color="#dc2626",
    increasing_fillcolor="#16a34a", decreasing_fillcolor="#dc2626",
))
if show_liquidity:
    for col, label, color, symbol in [
        ("BuySideSweep", "Buy-side liquidity sweep", "#f59e0b", "triangle-down"),
        ("SellSideSweep", "Sell-side liquidity sweep", "#06b6d4", "triangle-up"),
    ]:
        points = df[df[col]]
        if not points.empty:
            y = points["High"] if col == "BuySideSweep" else points["Low"]
            fig.add_trace(go.Scatter(
                x=points.index, y=y, mode="markers", name=label,
                marker=dict(color=color, size=11, symbol=symbol)
            ))
if show_fvg:
    bull = df[df["BullFVG"]]
    bear = df[df["BearFVG"]]
    if not bull.empty:
        fig.add_trace(go.Scatter(x=bull.index, y=bull["Low"], mode="markers",
            name="Bullish FVG", marker=dict(color="#22c55e", size=8, symbol="circle")))
    if not bear.empty:
        fig.add_trace(go.Scatter(x=bear.index, y=bear["High"], mode="markers",
            name="Bearish FVG", marker=dict(color="#ef4444", size=8, symbol="circle")))
if show_structure:
    bull = df[df["BullBOS"]]
    bear = df[df["BearBOS"]]
    if not bull.empty:
        fig.add_trace(go.Scatter(x=bull.index, y=bull["Low"], mode="markers",
            name="Bullish BOS", marker=dict(color="#15803d", size=12, symbol="star")))
    if not bear.empty:
        fig.add_trace(go.Scatter(x=bear.index, y=bear["High"], mode="markers",
            name="Bearish BOS", marker=dict(color="#b91c1c", size=12, symbol="star")))

fig.update_layout(
    title=f"XAUUSD — {timeframe} • Real OHLC feed",
    height=650, xaxis_rangeslider_visible=False,
    margin=dict(l=10, r=10, t=50, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
)
fig.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)")
fig.update_yaxes(title="Price (USD/oz)", showgrid=True, gridcolor="rgba(128,128,128,0.15)")
st.plotly_chart(fig, use_container_width=True)

sweeps = df[(df["BuySideSweep"]) | (df["SellSideSweep"])]
if not sweeps.empty:
    st.subheader("Recent liquidity sweeps")
    view = sweeps[["Open", "High", "Low", "Close", "BuySideSweep", "SellSideSweep"]].tail(10).copy()
    view["Type"] = view.apply(lambda r: "Buy-side" if r["BuySideSweep"] else "Sell-side", axis=1)
    st.dataframe(view[["Open", "High", "Low", "Close", "Type"]], use_container_width=True)
else:
    st.caption("Selected candles mein koi basic liquidity-sweep condition detect nahi hui.")

st.warning(
    "Important: XAUUSD=X Yahoo Finance ka spot-gold quote hai; feed delayed/limited ho sakti hai. "
    "1m/5m/15m/1h/4h data availability provider par depend karti hai. "
    "ICT markers simplified technical approximations hain, financial advice ya guaranteed entry signals nahi."
)
st.caption(f"Last app update (UTC): {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
