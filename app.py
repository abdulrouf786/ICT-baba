import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import ccxt
from datetime import datetime, timezone

st.set_page_config(page_title="ICT Baba Trading", page_icon="📈", layout="wide")

st.title("📈 ICT Baba — Live Crypto Chart")
st.caption("Real exchange OHLC candles • Public Binance market data • Not financial advice")

@st.cache_resource
def get_exchange():
    return ccxt.binance({"enableRateLimit": True, "timeout": 15000})

exchange = get_exchange()

with st.sidebar:
    st.header("Chart Settings")
    symbol = st.selectbox("Market", ["BTC/USDT", "ETH/USDT", "SOL/USDT"], index=0)
    timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h"], index=1)
    candle_count = st.slider("Candles on chart", min_value=50, max_value=250, value=120, step=10)
    show_fvg = st.checkbox("Show Fair Value Gaps (FVG)", value=True)
    show_liquidity = st.checkbox("Show recent liquidity levels", value=True)
    st.caption("Auto-refresh target: every 5 seconds")

def fetch_market_data(selected_symbol, selected_timeframe, limit):
    candles = exchange.fetch_ohlcv(
        selected_symbol, timeframe=selected_timeframe, limit=limit
    )
    if not candles:
        raise RuntimeError("Exchange ne candle data return nahi kiya.")
    df = pd.DataFrame(
        candles, columns=["Timestamp", "Open", "High", "Low", "Close", "Volume"]
    )
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit="ms", utc=True)
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna().reset_index(drop=True)
    ticker = exchange.fetch_ticker(selected_symbol)
    price = ticker.get("last")
    if price is None:
        price = float(df["Close"].iloc[-1])
    return df, float(price), ticker

def detect_structure(df):
    result = []
    # Simple heuristic markers, not a full ICT rules engine.
    window = 10
    for i in range(window, len(df)):
        prior_high = df["High"].iloc[i-window:i].max()
        prior_low = df["Low"].iloc[i-window:i].min()
        row = df.iloc[i]
        prev = df.iloc[i-1]
        if row["High"] > prior_high and row["Close"] < prior_high:
            result.append((i, "Liquidity sweep high", "down"))
        elif row["Low"] < prior_low and row["Close"] > prior_low:
            result.append((i, "Liquidity sweep low", "up"))

        # Basic MSS approximation: close breaks recent 5-candle structure.
        if i >= 5:
            recent_high = df["High"].iloc[i-5:i].max()
            recent_low = df["Low"].iloc[i-5:i].min()
            if row["Close"] > recent_high and prev["Close"] <= recent_high:
                result.append((i, "Possible bullish MSS", "up"))
            elif row["Close"] < recent_low and prev["Close"] >= recent_low:
                result.append((i, "Possible bearish MSS", "down"))
    return result

def build_chart(df, selected_symbol, selected_timeframe, fvg_on, liquidity_on):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df["Timestamp"],
        open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        name="Real OHLC candles",
        increasing_line_color="#16a34a",
        decreasing_line_color="#dc2626",
        increasing_fillcolor="#16a34a",
        decreasing_fillcolor="#dc2626",
    ))

    if liquidity_on and len(df) >= 12:
        recent = df.tail(30)
        liq_high = float(recent["High"].iloc[:-1].max())
        liq_low = float(recent["Low"].iloc[:-1].min())
        fig.add_hline(y=liq_high, line_dash="dot", line_color="#f59e0b",
                      annotation_text="Recent liquidity high")
        fig.add_hline(y=liq_low, line_dash="dot", line_color="#38bdf8",
                      annotation_text="Recent liquidity low")

    if fvg_on and len(df) >= 3:
        # Three-candle FVG approximation: bullish if candle 3 low > candle 1 high;
        # bearish if candle 3 high < candle 1 low.
        start = max(2, len(df) - 45)
        for i in range(start, len(df)):
            left_time = df["Timestamp"].iloc[i-2]
            right_time = df["Timestamp"].iloc[i]
            first_high = float(df["High"].iloc[i-2])
            first_low = float(df["Low"].iloc[i-2])
            third_high = float(df["High"].iloc[i])
            third_low = float(df["Low"].iloc[i])
            if third_low > first_high:
                fig.add_shape(
                    type="rect", x0=left_time, x1=right_time,
                    y0=first_high, y1=third_low,
                    fillcolor="rgba(22,163,74,0.16)",
                    line=dict(width=0), layer="below"
                )
            elif third_high < first_low:
                fig.add_shape(
                    type="rect", x0=left_time, x1=right_time,
                    y0=third_high, y1=first_low,
                    fillcolor="rgba(220,38,38,0.16)",
                    line=dict(width=0), layer="below"
                )

    signals = detect_structure(df)
    for i, label, direction in signals[-12:]:
        color = "#16a34a" if direction == "up" else "#dc2626"
        y = df["Low"].iloc[i] if direction == "up" else df["High"].iloc[i]
        fig.add_trace(go.Scatter(
            x=[df["Timestamp"].iloc[i]], y=[y],
            mode="markers",
            marker=dict(symbol="triangle-up" if direction == "up" else "triangle-down",
                        size=10, color=color),
            name=label, showlegend=False,
            hovertemplate=f"{label}<br>%{{x}}<br>Price: %{{y}}<extra></extra>"
        ))

    fig.update_layout(
        title=f"{selected_symbol} · {selected_timeframe}",
        template="plotly_dark",
        height=650,
        margin=dict(l=10, r=10, t=55, b=10),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(150,150,150,0.15)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(150,150,150,0.15)", side="right")
    return fig, signals

@st.fragment(run_every="5s")
def live_panel():
    try:
        df, price, ticker = fetch_market_data(symbol, timeframe, candle_count)
        previous_close = float(df["Close"].iloc[-2]) if len(df) > 1 else price
        change = price - previous_close
        pct = (change / previous_close * 100) if previous_close else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"{symbol} live price", f"{price:,.6g}", f"{change:+.6g} ({pct:+.2f}%)")
        c2.metric("Latest candle close", f"{float(df['Close'].iloc[-1]):,.6g}")
        c3.metric("Latest candle volume", f"{float(df['Volume'].iloc[-1]):,.4g}")
        c4.metric("Last update (UTC)", datetime.now(timezone.utc).strftime("%H:%M:%S"))

        st.caption(
            "Data source: Binance public API. Price updates are polled every 5 seconds; "
            "the exchange may delay or limit data. The newest candle can still be forming."
        )
        fig, signals = build_chart(df, symbol, timeframe, show_fvg, show_liquidity)
        st.plotly_chart(fig, width="stretch", config={"scrollZoom": True, "displaylogo": False})

        with st.expander("Recent ICT-style markers and OHLC data"):
            if signals:
                rows = []
                for i, label, direction in signals[-15:]:
                    rows.append({
                        "Time (UTC)": df["Timestamp"].iloc[i],
                        "Marker": label,
                        "Direction": direction,
                        "Price": float(df["Close"].iloc[i]),
                    })
                st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
            else:
                st.info("Abhi recent heuristic markers nahi mile. Yeh normal hai.")
            st.dataframe(df.tail(10).sort_values("Timestamp", ascending=False),
                         width="stretch", hide_index=True)

    except Exception as exc:
        st.error("Market data load nahi ho saka.")
        st.write(f"Details: {type(exc).__name__}: {exc}")
        st.info("Internet connection check karein, ya kuch der baad page refresh karein.")

live_panel()

st.warning(
    "ICT sweep, MSS aur FVG markers simplified heuristic dete hain; "
    "yeh guaranteed signals nahi hain. Trade se pehle chart ko khud verify karein."
)
