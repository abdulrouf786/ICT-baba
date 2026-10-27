import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

# -------------------- Page setup --------------------
st.set_page_config(page_title="ICT Baba | XAUUSD", page_icon="📈", layout="wide")
st.title("📈 ICT Baba — Gold XAUUSD ICT Dashboard")
st.caption("Market data is supplied by the configured provider. ICT signals are rule-based examples, not financial advice.")

API_URL = "https://biquote.io/api/XAUUSD"

# -------------------- Sidebar controls --------------------
with st.sidebar:
    st.header("Chart settings")
    timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h", "1d"], index=2)
    candle_limit = st.slider("Candles to load", min_value=50, max_value=300, value=150, step=25)
    swing_strength = st.slider("Swing strength", min_value=2, max_value=10, value=3)
    show_sweeps = st.checkbox("Show liquidity sweeps", value=True)
    show_mss = st.checkbox("Show MSS", value=True)
    show_fvg = st.checkbox("Show Fair Value Gaps (FVG)", value=True)
    show_entry = st.checkbox("Show possible entry markers", value=True)
    refresh = st.button("🔄 Refresh market data", use_container_width=True)

# -------------------- Data loading --------------------
@st.cache_data(ttl=30, show_spinner=False)
def load_data(interval: str, limit: int) -> pd.DataFrame:
    response = requests.get(
        API_URL,
        params={"interval": interval, "limit": limit},
        timeout=20,
        headers={"User-Agent": "ICT-Baba-Streamlit/1.0"},
    )
    response.raise_for_status()
    payload = response.json()

    # Providers may return a list directly or a dictionary containing bars/candles/data.
    if isinstance(payload, dict):
        bars = payload.get("bars") or payload.get("candles") or payload.get("data")
        if isinstance(bars, dict):
            bars = bars.get("bars") or bars.get("candles") or bars.get("data")
    elif isinstance(payload, list):
        bars = payload
    else:
        bars = None

    if not isinstance(bars, list) or not bars:
        detail = payload.get("message", payload.get("error", "No candle list found")) if isinstance(payload, dict) else "Unexpected API response"
        raise ValueError(f"Provider did not return candle data: {detail}")

    df = pd.DataFrame(bars)
    # Normalize common field-name variations.
    aliases = {
        "openTime": ["openTime", "opentime", "time", "timestamp", "date", "datetime", "t"],
        "open": ["open", "o"],
        "high": ["high", "h"],
        "low": ["low", "l"],
        "close": ["close", "c"],
        "volume": ["volume", "vol", "v"],
    }
    lower_map = {str(col).lower(): col for col in df.columns}
    rename = {}
    for target, names in aliases.items():
        for name in names:
            if name.lower() in lower_map:
                rename[lower_map[name.lower()]] = target
                break
    df = df.rename(columns=rename)

    required = ["openTime", "open", "high", "low", "close"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(
            "Unexpected candle format. Missing: " + ", ".join(missing)
            + ". API fields received: " + ", ".join(map(str, df.columns))
        )

    # Convert timestamps robustly (seconds, milliseconds, ISO text).
    raw_time = df["openTime"]
    if pd.api.types.is_numeric_dtype(raw_time):
        numeric_time = pd.to_numeric(raw_time, errors="coerce")
        unit = "ms" if numeric_time.dropna().median() > 10**11 else "s"
        df["openTime"] = pd.to_datetime(numeric_time, unit=unit, errors="coerce", utc=True)
    else:
        df["openTime"] = pd.to_datetime(raw_time, errors="coerce", utc=True)

    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if "volume" in df.columns:
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")

    df = df.dropna(subset=required).sort_values("openTime")
    df = df.drop_duplicates(subset=["openTime"], keep="last").tail(limit).reset_index(drop=True)
    if df.empty:
        raise ValueError("No valid candles remained after parsing the provider response.")
    if (df["high"] < df["low"]).any():
        raise ValueError("Invalid candle data: at least one High is below Low.")
    return df


if refresh:
    load_data.clear()

try:
    with st.spinner("Loading XAUUSD candles..."):
        df = load_data(timeframe, candle_limit)
except Exception as exc:
    st.error("Could not load market data.")
    st.write(f"**Details:** {exc}")
    st.info(
        "If the provider API changed or requires a key, update API_URL and the response parsing "
        "inside load_data(). The chart cannot show real candles until the provider returns valid OHLC data."
    )
    st.stop()

# -------------------- ICT calculations --------------------
def add_ict_signals(data: pd.DataFrame, strength: int) -> pd.DataFrame:
    out = data.copy()
    out["SwingHigh"] = False
    out["SwingLow"] = False
    out["SweepHigh"] = False
    out["SweepLow"] = False
    out["MSS_Bull"] = False
    out["MSS_Bear"] = False
    out["FVG_Bull"] = False
    out["FVG_Bear"] = False

    # Confirmed swing points; a swing is only marked after right-side candles exist.
    n = len(out)
    for i in range(strength, n - strength):
        high_window = out["high"].iloc[i-strength:i+strength+1]
        low_window = out["low"].iloc[i-strength:i+strength+1]
        if out["high"].iloc[i] == high_window.max() and (high_window == out["high"].iloc[i]).sum() == 1:
            out.loc[i, "SwingHigh"] = True
        if out["low"].iloc[i] == low_window.min() and (low_window == out["low"].iloc[i]).sum() == 1:
            out.loc[i, "SwingLow"] = True

    last_swing_high = None
    last_swing_low = None
    trend = 0
    for i in range(n):
        if out.loc[i, "SwingHigh"]:
            last_swing_high = float(out.loc[i, "high"])
        if out.loc[i, "SwingLow"]:
            last_swing_low = float(out.loc[i, "low"])

        # Sweep: price wicks beyond a known swing and closes back inside.
        if last_swing_high is not None and i > 0:
            if out.loc[i, "high"] > last_swing_high and out.loc[i, "close"] < last_swing_high:
                out.loc[i, "SweepHigh"] = True
        if last_swing_low is not None and i > 0:
            if out.loc[i, "low"] < last_swing_low and out.loc[i, "close"] > last_swing_low:
                out.loc[i, "SweepLow"] = True

        # Simple MSS proxy: close breaks the most recently confirmed swing.
        if last_swing_high is not None and out.loc[i, "close"] > last_swing_high and trend <= 0:
            out.loc[i, "MSS_Bull"] = True
            trend = 1
        if last_swing_low is not None and out.loc[i, "close"] < last_swing_low and trend >= 0:
            out.loc[i, "MSS_Bear"] = True
            trend = -1

        # Three-candle fair value gap.
        if i >= 2:
            if out.loc[i, "low"] > out.loc[i-2, "high"]:
                out.loc[i, "FVG_Bull"] = True
            if out.loc[i, "high"] < out.loc[i-2, "low"]:
                out.loc[i, "FVG_Bear"] = True

    # Illustrative setup markers, not a validated trading strategy:
    # a sweep and an MSS in the same direction are used as a simple confluence.
    out["EntryBull"] = out["SweepLow"] & (out["MSS_Bull"] | out["FVG_Bull"])
    out["EntryBear"] = out["SweepHigh"] & (out["MSS_Bear"] | out["FVG_Bear"])
    return out


df = add_ict_signals(df, swing_strength)

# -------------------- Summary metrics --------------------
latest = df.iloc[-1]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Latest close", f"{latest['close']:.2f}")
c2.metric("Candles loaded", f"{len(df)}")
c3.metric("Timeframe", timeframe)
c4.metric("Latest candle (UTC)", latest["openTime"].strftime("%Y-%m-%d %H:%M"))

# -------------------- Candlestick chart --------------------
fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=df["openTime"],
    open=df["open"],
    high=df["high"],
    low=df["low"],
    close=df["close"],
    name="XAUUSD",
    increasing_line_color="#22ab94",
    increasing_fillcolor="#22ab94",
    decreasing_line_color="#f23645",
    decreasing_fillcolor="#f23645",
    whiskerwidth=0.7,
))

if show_sweeps:
    sweep_highs = df[df["SweepHigh"]]
    sweep_lows = df[df["SweepLow"]]
    if not sweep_highs.empty:
        fig.add_trace(go.Scatter(
            x=sweep_highs["openTime"], y=sweep_highs["high"],
            mode="markers+text", text=["BSL sweep"] * len(sweep_highs),
            textposition="top center", name="Liquidity sweep high",
            marker=dict(symbol="triangle-down", size=11, color="#ff9800"),
        ))
    if not sweep_lows.empty:
        fig.add_trace(go.Scatter(
            x=sweep_lows["openTime"], y=sweep_lows["low"],
            mode="markers+text", text=["SSL sweep"] * len(sweep_lows),
            textposition="bottom center", name="Liquidity sweep low",
            marker=dict(symbol="triangle-up", size=11, color="#00bcd4"),
        ))

if show_mss:
    bull = df[df["MSS_Bull"]]
    bear = df[df["MSS_Bear"]]
    if not bull.empty:
        fig.add_trace(go.Scatter(
            x=bull["openTime"], y=bull["low"],
            mode="markers+text", text=["MSS ↑"] * len(bull),
            textposition="bottom center", name="Bullish MSS",
            marker=dict(symbol="arrow-up", size=12, color="#00e676"),
        ))
    if not bear.empty:
        fig.add_trace(go.Scatter(
            x=bear["openTime"], y=bear["high"],
            mode="markers+text", text=["MSS ↓"] * len(bear),
            textposition="top center", name="Bearish MSS",
            marker=dict(symbol="arrow-down", size=12, color="#ff5252"),
        ))

if show_fvg:
    for i in range(2, len(df)):
        if df.loc[i, "FVG_Bull"]:
            lower = float(df.loc[i-2, "high"])
            upper = float(df.loc[i, "low"])
            fig.add_shape(
                type="rect", xref="x", yref="y",
                x0=df.loc[i-2, "openTime"], x1=df.loc[i, "openTime"],
                y0=lower, y1=upper,
                fillcolor="rgba(0,230,118,0.16)", line_width=0,
                layer="below",
            )
        elif df.loc[i, "FVG_Bear"]:
            lower = float(df.loc[i, "high"])
            upper = float(df.loc[i-2, "low"])
            fig.add_shape(
                type="rect", xref="x", yref="y",
                x0=df.loc[i-2, "openTime"], x1=df.loc[i, "openTime"],
                y0=lower, y1=upper,
                fillcolor="rgba(255,82,82,0.16)", line_width=0,
                layer="below",
            )

if show_entry:
    entries_bull = df[df["EntryBull"]]
    entries_bear = df[df["EntryBear"]]
    if not entries_bull.empty:
        fig.add_trace(go.Scatter(
            x=entries_bull["openTime"], y=entries_bull["low"],
            mode="markers+text", text=["BUY?"] * len(entries_bull),
            textposition="bottom center", name="Possible bullish setup",
            marker=dict(symbol="star", size=14, color="#00e676"),
        ))
    if not entries_bear.empty:
        fig.add_trace(go.Scatter(
            x=entries_bear["openTime"], y=entries_bear["high"],
            mode="markers+text", text=["SELL?"] * len(entries_bear),
            textposition="top center", name="Possible bearish setup",
            marker=dict(symbol="star", size=14, color="#ff5252"),
        ))

fig.update_layout(
    template="plotly_dark",
    height=720,
    title=f"XAUUSD — {timeframe} | ICT concepts",
    xaxis_title="Time (UTC)",
    yaxis_title="Price",
    xaxis_rangeslider_visible=False,
    hovermode="x unified",
    margin=dict(l=10, r=10, t=60, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
)
fig.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.18)", rangeslider_visible=False)
fig.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.18)", side="right")

st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True, "displaylogo": False})

# -------------------- Signal table and raw data --------------------
left, right = st.columns(2)
with left:
    st.subheader("Recent ICT events")
    event_rows = []
    for _, row in df.tail(80).iterrows():
        labels = []
        if row["SweepHigh"]: labels.append("Liquidity sweep high / BSL")
        if row["SweepLow"]: labels.append("Liquidity sweep low / SSL")
        if row["MSS_Bull"]: labels.append("Bullish MSS")
        if row["MSS_Bear"]: labels.append("Bearish MSS")
        if row["FVG_Bull"]: labels.append("Bullish FVG")
        if row["FVG_Bear"]: labels.append("Bearish FVG")
        if row["EntryBull"]: labels.append("Possible BUY setup")
        if row["EntryBear"]: labels.append("Possible SELL setup")
        if labels:
            event_rows.append({
                "Time (UTC)": row["openTime"].strftime("%Y-%m-%d %H:%M"),
                "Event": ", ".join(labels),
                "Close": round(float(row["close"]), 3),
            })
    if event_rows:
        st.dataframe(pd.DataFrame(event_rows[::-1]), use_container_width=True, hide_index=True)
    else:
        st.info("No events detected in the currently loaded candles.")

with right:
    st.subheader("Latest candle data")
    display_cols = ["openTime", "open", "high", "low", "close"]
    if "volume" in df.columns:
        display_cols.append("volume")
    view = df[display_cols].tail(15).copy()
    view["openTime"] = view["openTime"].dt.strftime("%Y-%m-%d %H:%M")
    st.dataframe(view.iloc[::-1], use_container_width=True, hide_index=True)

st.caption(
    "Important: these are simplified, mechanical ICT-style labels. They may repaint as new candles arrive, "
    "do not account for spread/news/session context, and are not financial advice. Verify signals manually."
)
