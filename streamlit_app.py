
import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

st.set_page_config(
    page_title="ICT Baba",
    page_icon="🥇",
    layout="wide"
)

API_URL = "https://api.twelvedata.com"

st.title("🥇 ICT BABA — GOLD TRADING")
st.caption("Real XAU/USD OHLC Market Data | Twelve Data")

# Read API key securely
try:
    API_KEY = st.secrets["TWELVE_DATA_API_KEY"]
except Exception:
    API_KEY = ""

if not API_KEY:
    st.error("API key missing. Streamlit Secrets check karein.")
    st.stop()


@st.cache_data(ttl=20)
def get_price():
    response = requests.get(
        f"{API_URL}/price",
        params={
            "symbol": "XAU/USD",
            "apikey": API_KEY
        },
        timeout=20
    )
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

    data = response.json()

    if "values" not in data:
        raise ValueError(data.get("message", str(data)))

    df = pd.DataFrame(data["values"])

    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.dropna()
    df = df.sort_values("datetime")

    return df


# Live price
try:
    price = get_price()
    st.metric("LIVE GOLD PRICE — XAU/USD", f"${price:,.2f}")
except Exception as e:
    st.warning(f"Live price error: {e}")

st.divider()

# Timeframes
timeframes = {
    "1 Minute": "1min",
    "5 Minutes": "5min",
    "15 Minutes": "15min",
    "1 Hour": "1h",
    "4 Hours": "4h"
}

selected = st.selectbox(
    "Select Gold Timeframe",
    list(timeframes.keys())
)

interval = timeframes[selected]

if st.button("🔄 Refresh Market Data"):
    st.cache_data.clear()
    st.rerun()

# Real OHLC chart
try:
    df = get_candles(interval)

    if df.empty:
        st.error("Gold candles available nahi hain.")
        st.stop()

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df["datetime"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        increasing_line_color="#00C853",
        decreasing_line_color="#FF1744",
        name="XAU/USD"
    ))

    fig.update_layout(
        title=f"XAU/USD REAL GOLD — {selected}",
        xaxis_title="Time (UTC)",
        yaxis_title="Gold Price (USD)",
        template="plotly_dark",
        height=650,
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=50, b=10)
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Latest Gold OHLC")

    latest = df.iloc[-1]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("OPEN", f"{latest['open']:.2f}")
    c2.metric("HIGH", f"{latest['high']:.2f}")
    c3.metric("LOW", f"{latest['low']:.2f}")
    c4.metric("CLOSE", f"{latest['close']:.2f}")

    with st.expander("View OHLC Data"):
        st.dataframe(
            df.tail(50).iloc[::-1],
            use_container_width=True
        )

    st.success(
        f"Gold data loaded: {len(df)} real OHLC candles"
    )

except Exception as e:
    st.error(f"Gold data error: {e}")
    st.info(
        "Twelve Data API plan, API credits aur XAU/USD access check karein."
    )

st.divider()
st.caption("ICT BABA | XAU/USD | Powered by Twelve Data")
