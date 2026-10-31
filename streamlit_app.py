import requests
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Abdul Rauf King - ICT Gold",
    page_icon="🥇",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.block-container {
    max-width: 100% !important;
    zoom: 0.75;
    padding-top: 0.15rem !important;
    padding-left: 0.15rem !important;
    padding-right: 0.15rem !important;
    padding-bottom: 1rem !important;
}
h1 { font-size: 1.3rem !important; line-height: 1.15 !important; white-space: nowrap !important; margin: 0 0 0.25rem 0 !important; }
</style>
""", unsafe_allow_html=True)

st.title("👑 ABDUL RAUF KING")
st.caption("XAU/USD GOLD • ICT CHART • XAUS DATA (not Vantage broker feed)")

TIMEFRAMES = {
    "1 Minute": "1m",
    "5 Minutes": "5m",
    "15 Minutes": "15m",
    "1 Hour": "1h",
    "4 Hours": "4h",
}
selected = st.selectbox("Gold timeframe", list(TIMEFRAMES.keys()), index=2)
interval = TIMEFRAMES[selected]

# XAUS publishes XAU/USD OHLC through its chart endpoint without an API key.
# The endpoint documents Yahoo Finance-proxy OHLCV data; this is not Vantage's quote.
RANGES = {"1m": "1d", "5m": "5d", "15m": "1mo", "1h": "6mo", "4h": "6mo"}
request_interval = "1h" if interval == "4h" else interval

@st.cache_data(ttl=60, show_spinner=False)
def load_gold_data(api_interval, period):
    url = "https://xaus.com/api/v1/chart"
    response = requests.get(
        url,
        params={"symbol": "xau", "range": period, "interval": api_interval},
        timeout=20,
        headers={"User-Agent": "ICT-Baba-Streamlit/1.0"},
    )
    response.raise_for_status()
    payload = response.json()
    rows = payload.get("points", [])
    if not rows:
        raise ValueError(payload.get("message", "Gold OHLC data is currently unavailable."))
    frame = pd.DataFrame(rows)
    required = {"t", "o", "h", "l", "c"}
    if not required.issubset(frame.columns):
        raise ValueError("Gold data response did not contain valid OHLC fields.")
    frame["time"] = pd.to_datetime(frame["t"], unit="s", utc=True).dt.tz_convert("Asia/Karachi")
    for col in ["o", "h", "l", "c"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame.dropna(subset=["time", "o", "h", "l", "c"]).sort_values("time")
    frame = frame.drop_duplicates(subset=["time"]).set_index("time")
    frame = frame.reset_index()
    return frame, payload.get("data_state", {})

def add_ict_marks(frame, fig):
    df = frame.copy().reset_index(drop=True)
    n = len(df)
    if n < 8:
        return

    # Confirmed 2-left / 2-right swing points (non-repainting after confirmation).
    swing_high = [None] * n
    swing_low = [None] * n
    for i in range(2, n - 2):
        if df.loc[i, "h"] >= df.loc[i-2:i+2, "h"].max():
            swing_high[i + 2] = float(df.loc[i, "h"])
        if df.loc[i, "l"] <= df.loc[i-2:i+2, "l"].min():
            swing_low[i + 2] = float(df.loc[i, "l"])

    last_high = None
    last_low = None
    last_high_idx = None
    last_low_idx = None
    mss_bull = [False] * n
    mss_bear = [False] * n
    sweep_bull = [False] * n
    sweep_bear = [False] * n
    bull_fvg = [False] * n
    bear_fvg = [False] * n

    for i in range(n):
        if swing_high[i] is not None:
            last_high, last_high_idx = swing_high[i], i
        if swing_low[i] is not None:
            last_low, last_low_idx = swing_low[i], i

        if i >= 1 and last_high is not None and last_high_idx is not None and i > last_high_idx:
            mss_bull[i] = df.loc[i, "c"] > last_high and df.loc[i-1, "c"] <= last_high
        if i >= 1 and last_low is not None and last_low_idx is not None and i > last_low_idx:
            mss_bear[i] = df.loc[i, "c"] < last_low and df.loc[i-1, "c"] >= last_low

        if last_high is not None and last_high_idx is not None and i > last_high_idx:
            sweep_bear[i] = df.loc[i, "h"] > last_high and df.loc[i, "c"] < last_high
        if last_low is not None and last_low_idx is not None and i > last_low_idx:
            sweep_bull[i] = df.loc[i, "l"] < last_low and df.loc[i, "c"] > last_low

        if i >= 2:
            bull_fvg[i] = df.loc[i, "l"] > df.loc[i-2, "h"]
            bear_fvg[i] = df.loc[i, "h"] < df.loc[i-2, "l"]

    # Draw recent fair-value gaps as shaded price zones.
    drawn = 0
    for i in range(2, n):
        if bull_fvg[i] and drawn < 24:
            fig.add_shape(
                type="rect", x0=df.loc[i-2, "time"], x1=df.loc[i, "time"],
                y0=df.loc[i-2, "h"], y1=df.loc[i, "l"],
                fillcolor="rgba(0,180,90,0.16)", line=dict(color="rgba(0,180,90,0.65)", width=1),
                layer="below",
            )
            drawn += 1
        elif bear_fvg[i] and drawn < 24:
            fig.add_shape(
                type="rect", x0=df.loc[i-2, "time"], x1=df.loc[i, "time"],
                y0=df.loc[i, "h"], y1=df.loc[i-2, "l"],
                fillcolor="rgba(230,60,60,0.15)", line=dict(color="rgba(230,60,60,0.65)", width=1),
                layer="below",
            )
            drawn += 1

    def add_mark(mask, y_values, name, symbol, color, position):
        xs = [df.loc[i, "time"] for i in range(n) if mask[i]]
        ys = [y_values[i] for i in range(n) if mask[i]]
        if xs:
            fig.add_trace(go.Scatter(
                x=xs, y=ys, mode="markers+text", name=name,
                text=[name] * len(xs), textposition=position,
                marker=dict(symbol=symbol, size=10, color=color),
                textfont=dict(size=9, color=color),
                hovertemplate="%{text}<br>%{y:.2f}<extra></extra>",
            ))

    add_mark(mss_bull, [df.loc[i, "l"] for i in range(n)], "MSS ↑", "triangle-up", "#00c878", "bottom left")
    add_mark(mss_bear, [df.loc[i, "h"] for i in range(n)], "MSS ↓", "triangle-down", "#ff6262", "top left")
    add_mark(sweep_bull, [df.loc[i, "l"] for i in range(n)], "SSL sweep", "circle", "#00c878", "bottom right")
    add_mark(sweep_bear, [df.loc[i, "h"] for i in range(n)], "BSL sweep", "circle", "#ff6262", "top right")

    # Confluence entry: recent opposite-side liquidity sweep + MSS + same-side FVG.
    buy_x, buy_y, sell_x, sell_y = [], [], [], []
    for i in range(n):
        recent_ssl = any(sweep_bull[max(0, i-8):i+1])
        recent_bsl = any(sweep_bear[max(0, i-8):i+1])
        recent_bull_fvg = any(bull_fvg[max(0, i-3):i+1])
        recent_bear_fvg = any(bear_fvg[max(0, i-3):i+1])
        if mss_bull[i] and recent_ssl and recent_bull_fvg:
            buy_x.append(df.loc[i, "time"])
            buy_y.append(df.loc[i, "l"])
        if mss_bear[i] and recent_bsl and recent_bear_fvg:
            sell_x.append(df.loc[i, "time"])
            sell_y.append(df.loc[i, "h"])
    if buy_x:
        fig.add_trace(go.Scatter(
            x=buy_x, y=buy_y, mode="markers+text", name="BUY entry",
            text=["BUY"] * len(buy_x), textposition="bottom center",
            marker=dict(symbol="arrow-up", size=17, color="#00ff88"),
        ))
    if sell_x:
        fig.add_trace(go.Scatter(
            x=sell_x, y=sell_y, mode="markers+text", name="SELL entry",
            text=["SELL"] * len(sell_x), textposition="top center",
            marker=dict(symbol="arrow-down", size=17, color="#ff4545"),
        ))

try:
    with st.spinner("Gold OHLC candles load ho rahi hain..."):
        data, state = load_gold_data(request_interval, RANGES[interval])
    if interval == "4h":
        data = data.set_index("time").resample("4h").agg(
            {"o": "first", "h": "max", "l": "min", "c": "last"}
        ).dropna().reset_index()

    if data.empty:
        st.warning("Is timeframe ke liye abhi Gold candles available nahi hain.")
        st.stop()

    latest = float(data.iloc[-1]["c"])
    st.metric("XAU/USD latest close", f"${latest:,.2f}")
    state_status = state.get("status", "not supplied")
    state_asof = state.get("as_of", "timestamp not supplied")
    st.caption(f"Data status: {state_status} • Source time: {state_asof} • Timezone: Pakistan")

    fig = go.Figure(data=[go.Candlestick(
        x=data["time"], open=data["o"], high=data["h"], low=data["l"], close=data["c"],
        name="XAU/USD",
        increasing_line_color="#00c878", decreasing_line_color="#ff5252",
    )])
    add_ict_marks(data, fig)
    fig.update_layout(
        height=650,
        template="plotly_dark",
        margin=dict(l=8, r=8, t=30, b=25),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", y=1.02, x=0),
        xaxis_title=None,
        yaxis_title="USD / troy ounce",
        dragmode="pan",
        uirevision=f"xau-{interval}",
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(130,130,130,0.18)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(130,130,130,0.18)")
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": False, "displaylogo": False})
    st.caption("ICT marks are rule-based approximations (swing sweep + structure break + 3-candle FVG), not guaranteed trade signals. Spot XAU/USD feed is indicative and is not your Vantage broker quote.")
    st.caption("Data source: XAUS XAU/USD chart endpoint (Yahoo Finance proxy).")
except Exception as exc:
    st.error("Gold OHLC data abhi load nahi ho saka.")
    st.caption(f"Technical detail: {exc}")
    st.info("Data source unavailable ho to app fake candles ya fake ICT signals nahi dikhayegi. Thori dair baad refresh karein.")
