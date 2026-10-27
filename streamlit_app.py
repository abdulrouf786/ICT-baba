
import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

st.set_page_config(
    page_title="Gold ICT Learning Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 XAUUSD ICT Learning Dashboard")
st.caption("Educational chart — not financial advice")

st.sidebar.header("Chart Settings")
timeframe = st.sidebar.selectbox(
    "Timeframe",
    ["1m", "5m", "15m", "1h"],
    index=0
)
bars_count = st.sidebar.slider(
    "Candles",
    min_value=50,
    max_value=300,
    value=150,
    step=50
)

show_swings = st.sidebar.checkbox("Swing High / Low", True)
show_fvg = st.sidebar.checkbox("FVG zones", True)
show_liquidity = st.sidebar.checkbox("BSL / SSL levels", True)

if st.button("🔄 Refresh chart"):
    st.cache_data.clear()

@st.cache_data(ttl=30)
def load_data(interval, count):
    url = "https://biquote.io/api/XAUUSD/ohlc"
    response = requests.get(
        url,
        params={"interval": interval, "limit": count},
        timeout=20
    )
    response.raise_for_status()
    payload = response.json()

    if "bars" not in payload or not payload["bars"]:
        raise ValueError("API ne candle data return nahi kiya.")

    df = pd.DataFrame(payload["bars"])
    required = ["openTime", "open", "high", "low", "close"]

    if not all(col in df.columns for col in required):
        raise ValueError("API data ka format mukhtalif hai.")

    df["openTime"] = pd.to_datetime(
        df["openTime"], utc=True, errors="coerce"
    )

    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=required)
    df = df.sort_values("openTime").drop_duplicates("openTime")
    return df.tail(count).reset_index(drop=True)

try:
    df = load_data(timeframe, bars_count)

    st.success(
        f"Data received: XAUUSD | {timeframe} | "
        f"{len(df)} candles"
    )

    st.caption(
        "Data provider: biquote API. "
        "Broker prices aur timestamps mukhtalif ho sakte hain."
    )

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df["openTime"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="XAUUSD"
    ))

    swing_highs = []
    swing_lows = []

    for i in range(1, len(df) - 1):
        if (
            df.loc[i, "high"] > df.loc[i - 1, "high"]
            and df.loc[i, "high"] > df.loc[i + 1, "high"]
        ):
            swing_highs.append(i)

        if (
            df.loc[i, "low"] < df.loc[i - 1, "low"]
            and df.loc[i, "low"] < df.loc[i + 1, "low"]
        ):
            swing_lows.append(i)

    if show_swings:
        fig.add_trace(go.Scatter(
            x=df.loc[swing_highs, "openTime"],
            y=df.loc[swing_highs, "high"],
            mode="markers+text",
            text=["SH"] * len(swing_highs),
            textposition="top center",
            name="Swing High",
            marker=dict(symbol="triangle-down", size=9)
        ))

        fig.add_trace(go.Scatter(
            x=df.loc[swing_lows, "openTime"],
            y=df.loc[swing_lows, "low"],
            mode="markers+text",
            text=["SL"] * len(swing_lows),
            textposition="bottom center",
            name="Swing Low",
            marker=dict(symbol="triangle-up", size=9)
        ))

    if show_liquidity:
        if swing_highs:
            idx = swing_highs[-1]
            level = float(df.loc[idx, "high"])
            fig.add_hline(
                y=level,
                line_dash="dot",
                annotation_text="BSL reference"
            )

        if swing_lows:
            idx = swing_lows[-1]
            level = float(df.loc[idx, "low"])
            fig.add_hline(
                y=level,
                line_dash="dot",
                annotation_text="SSL reference"
            )

    if show_fvg:
        for i in range(2, len(df)):
            # Basic three-candle FVG candidates
            if df.loc[i, "low"] > df.loc[i - 2, "high"]:
                fig.add_hrect(
                    y0=float(df.loc[i - 2, "high"]),
                    y1=float(df.loc[i, "low"]),
                    fillcolor="green",
                    opacity=0.12,
                    line_width=0
                )

            if df.loc[i, "high"] < df.loc[i - 2, "low"]:
                fig.add_hrect(
                    y0=float(df.loc[i, "high"]),
                    y1=float(df.loc[i - 2, "low"]),
                    fillcolor="red",
                    opacity=0.12,
                    line_width=0
                )

    fig.update_layout(
        title=f"XAUUSD — {timeframe} Candlestick Chart",
        xaxis_title="Time (UTC)",
        yaxis_title="Price (USD)",
        template="plotly_dark",
        height=650,
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h")
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("ICT Learning Notes")
    st.markdown("""
    - **SH / SL:** Possible swing high and swing low.
    - **BSL / SSL:** Reference levels near detected swings;
      these do not confirm actual resting orders.
    - **FVG:** Basic three-candle imbalance candidate.
    - **BOS / MSS:** Need additional structure and confirmation;
      this version does not automatically label them.
    """)

    st.warning(
        "Chart labels are educational approximations, not "
        "verified trading signals. Open candles can change."
    )

except Exception as e:
    st.error("Chart load nahi hua.")
    st.write("Error details:", str(e))
    st.caption(f"Technical detail: {e}")

st.divider()
st.caption("Free-data availability and freshness are not guaranteed.")
