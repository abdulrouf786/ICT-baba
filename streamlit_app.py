
import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

st.set_page_config(
    page_title="Gold XAUUSD ICT",
    layout="wide"
)

st.title("Gold XAUUSD ICT Dashboard")
st.caption("Real market data only — no simulated candles")

timeframe = st.selectbox(
    "Timeframe",
    ["1m", "5m", "15m", "1h"]
)

limit = st.slider(
    "Candles",
    min_value=50,
    max_value=200,
    value=100,
    step=50
)

@st.cache_data(ttl=30)
def load_data(interval, candle_limit):
    url = "https://biquote.io/api/XAUUSD/ohlc"

    response = requests.get(
        url,
        params={
            "interval": interval,
            "limit": candle_limit
        },
        timeout=20
    )
    response.raise_for_status()

    result = response.json()

    if not isinstance(result, dict):
        raise ValueError("Provider returned an unexpected response.")

    bars = result.get("bars")

    if not bars:
        raise ValueError("Provider returned no candles.")

    df = pd.DataFrame(bars)

    required = [
        "openTime", "open", "high", "low", "close"
    ]

    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(
            "Unexpected candle format. Missing: "
            + ", ".join(missing)
        )

    df["openTime"] = pd.to_datetime(
        df["openTime"], utc=True, errors="coerce"
    )

    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=required)
    df = df.sort_values("openTime")
    df = df.drop_duplicates("openTime")
    df = df.tail(candle_limit).reset_index(drop=True)

    if df.empty:
        raise ValueError("No valid candle data was returned.")

    if (df["high"] < df["low"]).any():
        raise ValueError("Invalid candle prices received.")

    return df


if st.button("Refresh real market data"):
    st.cache_data.clear()

try:
    df = load_data(timeframe, limit)

    st.success(
        "Provider se candle data receive hua. "
        "Price aur timestamp neeche check karein."
    )

    st.write("Latest candles:")
    st.dataframe(
        df[["openTime", "open", "high", "low", "close"]].tail(5),
        use_container_width=True
    )

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

    fig.add_trace(go.Candlestick(
        x=df["openTime"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="XAUUSD",
        increasing_line_color="#00c853",
        decreasing_line_color="#ff1744"
    ))

    highs = df[df["SwingHigh"]]
    lows = df[df["SwingLow"]]

    fig.add_trace(go.Scatter(
        x=highs["openTime"],
        y=highs["high"],
        mode="markers+text",
        text=["SH"] * len(highs),
        textposition="top center",
        name="Swing High"
    ))

    fig.add_trace(go.Scatter(
        x=lows["openTime"],
        y=lows["low"],
        mode="markers+text",
        text=["SL"] * len(lows),
        textposition="bottom center",
        name="Swing Low"
    ))

    for i in range(2, len(df)):
        if df.loc[i, "low"] > df.loc[i - 2, "high"]:
            fig.add_hrect(
                y0=float(df.loc[i - 2, "high"]),
                y1=float(df.loc[i, "low"]),
                fillcolor="green",
                opacity=0.15,
                line_width=0
            )

        if df.loc[i, "high"] < df.loc[i - 2, "low"]:
            fig.add_hrect(
                y0=float(df.loc[i, "high"]),
                y1=float(df.loc[i - 2, "low"]),
                fillcolor="red",
                opacity=0.15,
                line_width=0
            )

    fig.update_layout(
        title=f"XAUUSD Real-Data Chart — {timeframe}",
        template="plotly_dark",
        height=650,
        xaxis_rangeslider_visible=False,
        xaxis_title="Time (UTC)",
        yaxis_title="Price (USD)"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("ICT Market Structure Learning")

    st.markdown("""
    - **SH:** Swing High
    - **SL:** Swing Low
    - **FVG:** Possible three-candle imbalance
    - **BOS / MSS:** Abhi automatic confirmation enabled nahi hai.
    """)

    st.info(
        "Chart provider ke data par based hai. "
        "Data receive hona is baat ki guarantee nahi ke "
        "price live ya broker-matched hai. "
        "BUY/SELL signals guaranteed nahi hote."
    )

except Exception as error:
    st.error("Asli market candles load nahi ho sakin.")
    st.write("Data provider ka error:")
    st.code(str(error))
    st.warning(
        "Fake/demo candles nahi dikhayi ja rahi. "
        "Provider unavailable ya format different ho sakta hai."
    )
