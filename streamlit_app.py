
import random

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st


st.set_page_config(
    page_title="Gold ICT Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("Gold XAUUSD ICT Dashboard")
st.caption("Candlestick chart and ICT learning tools")

timeframe = st.selectbox(
    "Timeframe",
    ["1m", "5m", "15m", "1h"],
)

number_of_candles = st.slider(
    "Number of candles",
    min_value=50,
    max_value=200,
    value=100,
    step=50,
)


@st.cache_data(ttl=30)
def load_market_data(interval, limit):
    url = "https://biquote.io/api/XAUUSD/ohlc"

    response = requests.get(
        url,
        params={"interval": interval, "limit": limit},
        timeout=15,
    )
    response.raise_for_status()

    result = response.json()
    if not isinstance(result, dict) or not result.get("bars"):
        raise ValueError("No candle data returned")

    data = pd.DataFrame(result["bars"])
    required = ["openTime", "open", "high", "low", "close"]

    if not all(column in data.columns for column in required):
        raise ValueError("Unexpected API data format")

    data["openTime"] = pd.to_datetime(
        data["openTime"], utc=True, errors="coerce"
    )

    for column in ["open", "high", "low", "close"]:
        data[column] = pd.to_numeric(
            data[column], errors="coerce"
        )

    data = data.dropna(subset=required)
    data = data.sort_values("openTime")
    data = data.drop_duplicates("openTime")

    if data.empty:
        raise ValueError("No valid candles")

    return data.tail(limit).reset_index(drop=True)


def make_demo_data(limit):
    random.seed(21)
    price = 4300.0
    rows = []
    now = pd.Timestamp.now(tz="UTC")

    for i in range(limit):
        opening = price
        closing = opening + random.uniform(-3, 3)
        high = max(opening, closing) + random.uniform(0.2, 1.5)
        low = min(opening, closing) - random.uniform(0.2, 1.5)

        rows.append(
            {
                "openTime": now - pd.Timedelta(minutes=limit - i),
                "open": opening,
                "high": high,
                "low": low,
                "close": closing,
            }
        )
        price = closing

    return pd.DataFrame(rows)


try:
    df = load_market_data(timeframe, number_of_candles)
    st.success("Market data received from provider.")
    demo_mode = False

except Exception as error:
    df = make_demo_data(number_of_candles)
    demo_mode = True
    st.warning(
        "DEMO MODE: Live data load nahi hua. "
        "Neeche ka chart simulated hai, real gold price nahi."
    )
    with st.expander("Data error details"):
        st.write(str(error))


df["SwingHigh"] = False
df["SwingLow"] = False

for i in range(1, len(df) - 1):
    df.loc[i, "SwingHigh"] = (
        df.loc[i, "high"] > df.loc[i - 1, "high"]
        and df.loc[i, "high"] > df.loc[i + 1, "high"]
    )

    df.loc[i, "SwingLow"] = (
        df.loc[i, "low"] < df.loc[i - 1, "low"]
        and df.loc[i, "low"] < df.loc[i + 1, "low"]
    )


fig = go.Figure()

fig.add_trace(
    go.Candlestick(
        x=df["openTime"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="Demo" if demo_mode else "XAUUSD",
        increasing_line_color="#00c853",
        decreasing_line_color="#ff1744",
        increasing_fillcolor="#00c853",
        decreasing_fillcolor="#ff1744",
    )
)

high_indices = df.index[df["SwingHigh"]].tolist()
low_indices = df.index[df["SwingLow"]].tolist()

fig.add_trace(
    go.Scatter(
        x=df.loc[high_indices, "openTime"],
        y=df.loc[high_indices, "high"],
        mode="markers+text",
        text=["SH"] * len(high_indices),
        textposition="top center",
        name="Swing High",
        marker={"symbol": "triangle-down", "size": 9},
    )
)

fig.add_trace(
    go.Scatter(
        x=df.loc[low_indices, "openTime"],
        y=df.loc[low_indices, "low"],
        mode="markers+text",
        text=["SL"] * len(low_indices),
        textposition="bottom center",
        name="Swing Low",
        marker={"symbol": "triangle-up", "size": 9},
    )
)

# Basic three-candle FVG candidates
for i in range(2, len(df)):
    if df.loc[i, "low"] > df.loc[i - 2, "high"]:
        fig.add_hrect(
            y0=float(df.loc[i - 2, "high"]),
            y1=float(df.loc[i, "low"]),
            fillcolor="green",
            opacity=0.15,
            line_width=0,
        )

    if df.loc[i, "high"] < df.loc[i - 2, "low"]:
        fig.add_hrect(
            y0=float(df.loc[i, "high"]),
            y1=float(df.loc[i - 2, "low"]),
            fillcolor="red",
            opacity=0.15,
            line_width=0,
        )

if high_indices:
    last_high = float(df.loc[high_indices[-1], "high"])
    fig.add_hline(
        y=last_high,
        line_dash="dot",
        annotation_text="BSL reference",
    )

if low_indices:
    last_low = float(df.loc[low_indices[-1], "low"])
    fig.add_hline(
        y=last_low,
        line_dash="dot",
        annotation_text="SSL reference",
    )

fig.update_layout(
    title=f"XAUUSD Candles — {timeframe}",
    template="plotly_dark",
    height=650,
    autosize=True,
    margin={"l": 10, "r": 10, "t": 50, "b": 30},
    xaxis_rangeslider_visible=False,
    xaxis_title="Time (UTC)",
    yaxis_title="Price (USD)",
    dragmode="pan",
    showlegend=True,
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("ICT Market Structure Learning")

st.markdown(
    """
    - **SH / SL:** Swing High / Swing Low.
    - **BSL / SSL:** Possible liquidity reference levels near swings.
    - **FVG:** Basic three-candle imbalance candidate.
    - **BOS / MSS:** Not automatically confirmed in this version.
    """
)

st.info(
    "Educational only. Swing and FVG labels are not guaranteed "
    "BUY/SELL signals. Demo prices are simulated."
)

if st.button("Refresh chart"):
    st.cache_data.clear()
    st.rerun()
