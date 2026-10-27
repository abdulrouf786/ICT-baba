
import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import random

st.set_page_config(
    page_title="ICT Market Structure Learning",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Gold Chart Learning Dashboard")
st.caption("XAUUSD • Candlesticks • ICT learning")

interval = st.selectbox(
    "Timeframe",
    ["1m", "5m", "15m", "1h"]
)

count = st.slider("Candles", 50, 200, 100)

@st.cache_data(ttl=30)
def get_data(interval, count):
    url = "https://biquote.io/api/XAUUSD/ohlc"
    response = requests.get(
        url,
        params={"interval": interval, "limit": count},
        timeout=15
    )
    response.raise_for_status()
    data = response.json()

    if not data.get("bars"):
        raise ValueError("No candles returned")

    df = pd.DataFrame(data["bars"])
    required = ["openTime", "open", "high", "low", "close"]

    if not all(col in df.columns for col in required):
        raise ValueError("Unexpected candle format")

    df["openTime"] = pd.to_datetime(
        df["openTime"], utc=True, errors="coerce"
    )

    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=required)
    return df.sort_values("openTime").tail(count).reset_index(drop=True)


def demo_data(count):
    random.seed(7)
    rows = []
    price = 4300.0

    for i in range(count):
        op = price
        cl = op + random.uniform(-4, 4)
        hi = max(op, cl) + random.uniform(0.2, 2)
        lo = min(op, cl) - random.uniform(0.2, 2)

        rows.append({
            "openTime": pd.Timestamp.now(tz="UTC")
                        - pd.Timedelta(minutes=count-i),
            "open": op,
            "high": hi,
            "low": lo,
            "close": cl
        })
        price = cl

    return pd.DataFrame(rows)


try:
    df = get_data(interval, count)
    st.success("Market data received from API")
    is_demo = False

except Exception:
    df = demo_data(count)
    st.warning(
        "DEMO MODE: Live data load nahi hua. "
        "Yeh asli market prices nahi hain."
    )
    is_demo = True

# Detect simple swing points
df["SwingHigh"] = False
df["SwingLow"] = False

for i in range(1, len(df)-1):
    df.loc[i, "SwingHigh"] = (
        df.loc[i, "high"] > df.loc[i-1, "high"]
        and df.loc[i, "high"] > df.loc[i+1, "high"]
    )
    df.loc[i, "SwingLow"] = (
        df.loc[i, "low"] < df.loc[i-1, "low"]
        and df.loc[i, "low"] < df.loc[i+1, "low"]
    )

fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df["openTime"],
    open=df["open"],
    high=df["high"],
    low=df["low"],
    close=df["close"],
    name="Demo" if is_demo else "XAUUSD"
))

highs = df.index[df["SwingHigh"]].tolist()
lows = df.index[df["SwingLow"]].tolist()

fig.add_trace(go.Scatter(
    x=df.loc[highs, "openTime"],
    y=df.loc[highs, "high"],
    mode="markers+text",
    text=["SH"] * len(highs),
    textposition="top center",
    name="Swing High"
))

fig.add_trace(go.Scatter(
    x=df.loc[lows, "openTime"],
    y=df.loc[lows, "low"],
    mode="markers+text",
    text=["SL"] * len(lows),
    textposition="bottom center",
    name="Swing Low"
))

# Basic three-candle FVG zones
for i in range(2, len(df)):
    if df.loc[i, "low"] > df.loc[i-2, "high"]:
        fig.add_hrect(
            y0=float(df.loc[i-2, "high"]),
            y1=float(df.loc[i, "low"]),
            fillcolor="green",
            opacity=0.15,
            line_width=0
        )

    if df.loc[i, "high"] < df.loc[i-2, "low"]:
        fig.add_hrect(
            y0=float(df.loc[i, "high"]),
            y1=float(df.loc[i-2, "low"]),
            fillcolor="red",
            opacity=0.15,
            line_width=0
        )


fig.update_layout(
    title="XAUUSD Candlestick Chart",
    template="plotly_dark",
    height=700,
    autosize=True,
    margin=dict(l=10, r=10, t=50, b=30),
    xaxis_rangeslider_visible=False,
    xaxis_title="Time (UTC)",
    yaxis_title="Price (USD)",
    dragmode="pan",
    xaxis=dict(
        type="date",
        showgrid=True,
        rangeslider=dict(visible=False)
    ),
    yaxis=dict(
        side="right",
        fixedrange=False,
        showgrid=True
    ),
    showlegend=True
)

fig.update_traces(
    increasing_line_color="#00c853",
    decreasing_line_color="#ff1744",
    increasing_fillcolor="#00c853",
    decreasing_fillcolor="#ff1744"
)
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("📘 ICT Market Structure Learning")

st.markdown("""
- **SH / SL:** Possible swing high and swing low.
- **BSL:** Buy-side liquidity reference near highs.
- **SSL:** Sell-side liquidity reference near lows.
- **FVG:** Three-candle imbalance candidate.
- **BOS / MSS:** Structure breaks that require separate
  confirmation logic; they are not automatically confirmed here.
""")

st.info(
    "Educational chart only. Demo data is simulated. "
    "Swing points and FVGs are not guaranteed trading signals."
)

if st.button("🔄 Reload data"):
    st.cache_data.clear()
    st.rerun()
