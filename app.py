import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

st.set_page_config(page_title="ICT Baba", page_icon="🥇", layout="wide")
API_URL = "https://api.twelvedata.com"

st.title("🥇 ICT BABA — GOLD ICT TRADING")
st.caption("XAU/USD | Real OHLC | Liquidity Sweep • MSS • FVG")

try:
    API_KEY = st.secrets["TWELVE_DATA_API_KEY"]
except Exception:
    API_KEY = ""

if not API_KEY:
    st.error("API key missing. Streamlit Secrets mein TWELVE_DATA_API_KEY set karein.")
    st.stop()


@st.cache_data(ttl=20)
def get_price():
    response = requests.get(
        f"{API_URL}/price",
        params={"symbol": "XAU/USD", "apikey": API_KEY},
        timeout=20
    )
    response.raise_for_status()
    data = response.json()
    if "price" not in data:
        raise ValueError(data.get("message", str(data)))
    return float(data["price"])


@st.cache_data(ttl=30)
def get_candles(interval):
    response = requests.get(
        f"{API_URL}/time_series",
        params={
            "symbol": "XAU/USD",
            "interval": interval,
            "outputsize": 300,
            "order": "asc",
            "timezone": "UTC",
            "apikey": API_KEY
        },
        timeout=30
    )
    response.raise_for_status()
    data = response.json()
    if "values" not in data:
        raise ValueError(data.get("message", str(data)))
    df = pd.DataFrame(data["values"])
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce", utc=True)
    df = df.dropna(subset=["datetime", "open", "high", "low", "close"])
    df = df.drop_duplicates(subset=["datetime"], keep="last")
    # Reject malformed OHLC rows instead of drawing misleading candles.
    body_top = df[["open", "close"]].max(axis=1)
    body_bottom = df[["open", "close"]].min(axis=1)
    df = df[
        (df["high"] >= body_top) &
        (df["low"] <= body_bottom) &
        (df["high"] >= df["low"])
    ]
    return df.sort_values("datetime").reset_index(drop=True)


def add_ict_signals(data, swing_length=3):
    """Confirmed swing pivots, sweep -> MSS -> same-direction FVG entry."""
    df = data.copy().reset_index(drop=True)
    n = len(df)
    df["swing_high"] = False
    df["swing_low"] = False
    df["sweep_bull"] = False
    df["sweep_bear"] = False
    df["mss_bull"] = False
    df["mss_bear"] = False
    df["fvg_bull"] = False
    df["fvg_bear"] = False
    df["entry_bull"] = False
    df["entry_bear"] = False
    df["fvg_low"] = float("nan")
    df["fvg_high"] = float("nan")
    df["entry_price"] = float("nan")
    df["stop_price"] = float("nan")
    df["target_price"] = float("nan")

    last_swing_high = None
    last_swing_low = None
    pending_direction = None
    sweep_extreme = None
    mss_seen = False
    rr = 2.0

    for i in range(n):
        # A pivot is used only after swing_length candles have formed to its right.
        pivot_i = i - swing_length
        if pivot_i >= swing_length:
            left = pivot_i - swing_length
            right = i + 1
            window = df.iloc[left:right]
            candidate = df.iloc[pivot_i]
            if candidate["high"] >= window["high"].max():
                last_swing_high = float(candidate["high"])
                df.at[pivot_i, "swing_high"] = True
            if candidate["low"] <= window["low"].min():
                last_swing_low = float(candidate["low"])
                df.at[pivot_i, "swing_low"] = True

        row = df.iloc[i]
        # Sell-side sweep: wick below the last swing low, then close back above it.
        if last_swing_low is not None and row["low"] < last_swing_low and row["close"] > last_swing_low:
            df.at[i, "sweep_bull"] = True
            pending_direction = "bull"
            sweep_extreme = float(row["low"])
            mss_seen = False
        # Buy-side sweep: wick above the last swing high, then close back below it.
        elif last_swing_high is not None and row["high"] > last_swing_high and row["close"] < last_swing_high:
            df.at[i, "sweep_bear"] = True
            pending_direction = "bear"
            sweep_extreme = float(row["high"])
            mss_seen = False

        if pending_direction == "bull" and not mss_seen and last_swing_high is not None:
            if row["close"] > last_swing_high:
                df.at[i, "mss_bull"] = True
                mss_seen = True
        elif pending_direction == "bear" and not mss_seen and last_swing_low is not None:
            if row["close"] < last_swing_low:
                df.at[i, "mss_bear"] = True
                mss_seen = True

        # Three-candle FVG, only after the matching MSS.
        if i >= 2 and mss_seen and pending_direction == "bull":
            if row["low"] > df.iloc[i - 2]["high"]:
                zone_low = float(df.iloc[i - 2]["high"])
                zone_high = float(row["low"])
                entry = (zone_low + zone_high) / 2
                stop = float(sweep_extreme)
                risk = entry - stop
                if risk > 0:
                    df.at[i, "fvg_bull"] = True
                    df.at[i, "entry_bull"] = True
                    df.at[i, "fvg_low"] = zone_low
                    df.at[i, "fvg_high"] = zone_high
                    df.at[i, "entry_price"] = entry
                    df.at[i, "stop_price"] = stop
                    df.at[i, "target_price"] = entry + rr * risk
                    pending_direction = None
                    mss_seen = False
        elif i >= 2 and mss_seen and pending_direction == "bear":
            if row["high"] < df.iloc[i - 2]["low"]:
                zone_low = float(row["high"])
                zone_high = float(df.iloc[i - 2]["low"])
                entry = (zone_low + zone_high) / 2
                stop = float(sweep_extreme)
                risk = stop - entry
                if risk > 0:
                    df.at[i, "fvg_bear"] = True
                    df.at[i, "entry_bear"] = True
                    df.at[i, "fvg_low"] = zone_low
                    df.at[i, "fvg_high"] = zone_high
                    df.at[i, "entry_price"] = entry
                    df.at[i, "stop_price"] = stop
                    df.at[i, "target_price"] = entry - rr * risk
                    pending_direction = None
                    mss_seen = False

    return df


# Top controls
left, right = st.columns([3, 1])
with left:
    timeframes = {
        "1 Minute": "1min",
        "5 Minutes": "5min",
        "15 Minutes": "15min",
        "1 Hour": "1h",
        "4 Hours": "4h"
    }
    selected = st.selectbox("Gold timeframe", list(timeframes.keys()), index=2)
with right:
    st.write("")
    st.write("")
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

try:
    price = get_price()
    st.metric("LIVE GOLD PRICE — XAU/USD", f"${price:,.2f}")
except Exception as exc:
    st.warning(f"Live price error: {exc}")

try:
    raw_df = get_candles(timeframes[selected])
    if raw_df.empty:
        st.error("Gold OHLC candles available nahi hain.")
        st.stop()

    df = add_ict_signals(raw_df, swing_length=3)

    # Keep the chart readable on mobile: calculations use all fetched bars,
    # while the display focuses on the most recent 150 real OHLC candles.
    chart_df = df.tail(150).copy()
    show_overlays = st.checkbox("Chart par ICT markers / FVG zones dikhayein", value=False)

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=chart_df["datetime"], open=chart_df["open"], high=chart_df["high"],
        low=chart_df["low"], close=chart_df["close"],
        increasing_line_color="#00C853", decreasing_line_color="#FF1744",
        increasing_fillcolor="#00C853", decreasing_fillcolor="#FF1744",
        whiskerwidth=0.5, name="XAU/USD Real OHLC"
    ))

    # Optional overlays are off by default so the real candles stay clear.
    if show_overlays:
        # Confirmed swing levels
        swing_highs = chart_df[chart_df["swing_high"]]
        swing_lows = chart_df[chart_df["swing_low"]]
        if not swing_highs.empty:
        fig.add_trace(go.Scatter(
            x=swing_highs["datetime"], y=swing_highs["high"], mode="markers",
            marker=dict(symbol="triangle-down", color="#FFB300", size=8),
            name="Swing High"
        ))
        if not swing_lows.empty:
            fig.add_trace(go.Scatter(
                x=swing_lows["datetime"], y=swing_lows["low"], mode="markers",
                marker=dict(symbol="triangle-up", color="#29B6F6", size=8),
                name="Swing Low"
            ))

        for col, label, color, symbol, y_col in [
        ("sweep_bull", "Sell-side Sweep", "#00BCD4", "circle", "low"),
        ("sweep_bear", "Buy-side Sweep", "#FF9800", "circle", "high"),
        ("mss_bull", "Bullish MSS", "#00E676", "star", "close"),
        ("mss_bear", "Bearish MSS", "#FF5252", "star", "close"),
        ("entry_bull", "BUY Entry", "#00E676", "triangle-up", "low"),
        ("entry_bear", "SELL Entry", "#FF1744", "triangle-down", "high")
        ]:
            points = chart_df[chart_df[col]]
            if not points.empty:
                fig.add_trace(go.Scatter(
                    x=points["datetime"], y=points[y_col], mode="markers",
                    marker=dict(symbol=symbol, color=color, size=10),
                    name=label
                ))

        # Draw only the latest three FVG zones to avoid clutter.
        setups = chart_df[chart_df["entry_bull"] | chart_df["entry_bear"]]
        for _, setup in setups.tail(3).iterrows():
            color = "rgba(0,230,118,0.16)" if setup["entry_bull"] else "rgba(255,82,82,0.16)"
            fig.add_shape(
                type="rect", x0=setup["datetime"], x1=chart_df["datetime"].iloc[-1],
                y0=setup["fvg_low"], y1=setup["fvg_high"],
                fillcolor=color, line=dict(width=1), layer="below"
            )

    setups = df[df["entry_bull"] | df["entry_bear"]]

    fig.update_layout(
        title=f"XAU/USD ICT Setup — {selected}",
        xaxis_title="Time (UTC)", yaxis_title="Gold Price (USD)",
        template="plotly_dark", height=680,
        xaxis_rangeslider_visible=False,
        xaxis=dict(type="date", fixedrange=False),
        yaxis=dict(fixedrange=False, autorange=True),
        margin=dict(l=10, r=10, t=55, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("ICT Signal Status")
    latest_setup = setups.iloc[-1] if not setups.empty else None
    if latest_setup is not None:
        direction = "BUY" if latest_setup["entry_bull"] else "SELL"
        a, b, c, d = st.columns(4)
        a.metric("Signal", direction)
        b.metric("FVG Entry (50%)", f"{latest_setup['entry_price']:.2f}")
        c.metric("Stop Loss", f"{latest_setup['stop_price']:.2f}")
        d.metric("Target (2R)", f"{latest_setup['target_price']:.2f}")
        st.caption(f"Setup candle time (UTC): {latest_setup['datetime']}")
    else:
        st.info("Abhi confirmed Sweep → MSS → FVG entry setup nahi mila. Naya candle aane par refresh karein.")

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Liquidity Sweeps", int(df["sweep_bull"].sum() + df["sweep_bear"].sum()))
    s2.metric("MSS", int(df["mss_bull"].sum() + df["mss_bear"].sum()))
    s3.metric("Bullish FVG", int(df["fvg_bull"].sum()))
    s4.metric("Bearish FVG", int(df["fvg_bear"].sum()))

    latest = df.iloc[-1]
    st.subheader("Latest Gold OHLC")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("OPEN", f"{latest['open']:.2f}")
    c2.metric("HIGH", f"{latest['high']:.2f}")
    c3.metric("LOW", f"{latest['low']:.2f}")
    c4.metric("CLOSE", f"{latest['close']:.2f}")

    with st.expander("View OHLC and ICT data"):
        st.dataframe(df.tail(60).iloc[::-1], use_container_width=True)

    st.success(f"Loaded {len(df)} real XAU/USD OHLC candles for {selected}.")

except Exception as exc:
    st.error(f"Gold / ICT data error: {exc}")
    st.info("Twelve Data API plan, API credits aur XAU/USD access check karein.")

st.divider()
st.caption(
    "ICT BABA | Educational rule-based indicators only. "
    "Signals are not guaranteed trade recommendations; verify setups before trading."
)
