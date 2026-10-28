
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import ccxt
from datetime import datetime, timezone

st.set_page_config(
    page_title="ICT Baba Trading",
    page_icon="📈",
    layout="wide"
)

st.title("📈 ICT BABA — LIVE TRADING")
st.caption("Real market candles | Live price | ICT analysis")

@st.cache_resource
def connect_exchange():
    return ccxt.binance({
        "enableRateLimit": True,
        "timeout": 20000
    })

exchange = connect_exchange()

with st.sidebar:
    st.header("Chart Settings")

    symbol = st.selectbox(
        "Select Market",
        ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    )

    timeframe = st.selectbox(
        "Timeframe",
        ["1m", "5m", "15m", "1h", "4h"],
        index=1
    )

    candle_limit = st.selectbox(
        "Number of candles",
        [50, 100, 150, 200],
        index=1
    )

    show_fvg = st.checkbox("Show FVG", value=True)
    show_liquidity = st.checkbox(
        "Show Liquidity Levels", value=True
    )
    show_signals = st.checkbox(
        "Show MSS / Sweep Markers", value=True
    )

@st.fragment(run_every="5s")
def trading_chart():
    try:
        candles = exchange.fetch_ohlcv(
            symbol,
            timeframe=timeframe,
            limit=candle_limit
        )

        if not candles:
            st.error("Market se candle data nahi mila.")
            return

        df = pd.DataFrame(
            candles,
            columns=[
                "Time", "Open", "High",
                "Low", "Close", "Volume"
            ]
        )

        df["Time"] = pd.to_datetime(
            df["Time"], unit="ms", utc=True
        )

        for col in ["Open", "High", "Low", "Close", "Volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna().reset_index(drop=True)

        ticker = exchange.fetch_ticker(symbol)
        price = ticker.get("last")

        if price is None:
            price = float(df["Close"].iloc[-1])

        price = float(price)
        previous = float(df["Close"].iloc[-2])
        change = price - previous
        percent = change / previous * 100 if previous else 0

        a, b, c, d = st.columns(4)

        a.metric(
            f"{symbol} LIVE PRICE",
            f"{price:,.6g}",
            f"{change:+.6g} ({percent:+.2f}%)"
        )

        b.metric("Latest Open", f"{df['Open'].iloc[-1]:,.6g}")
        c.metric("Latest High", f"{df['High'].iloc[-1]:,.6g}")
        d.metric("Latest Low", f"{df['Low'].iloc[-1]:,.6g}")

        st.caption(
            "Last update UTC: "
            + datetime.now(timezone.utc).strftime("%H:%M:%S")
        )

        fig = go.Figure()

        # REAL OHLC CANDLESTICKS
        fig.add_trace(go.Candlestick(
            x=df["Time"],
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Real Candles",
            increasing_line_color="#00c176",
            decreasing_line_color="#ff4b4b",
            increasing_fillcolor="#00c176",
            decreasing_fillcolor="#ff4b4b"
        ))

        # RECENT LIQUIDITY LEVELS
        if show_liquidity and len(df) >= 20:
            recent = df.tail(30).iloc[:-1]

            high_level = float(recent["High"].max())
            low_level = float(recent["Low"].min())

            fig.add_hline(
                y=high_level,
                line_dash="dot",
                line_color="orange",
                annotation_text="Liquidity High"
            )

            fig.add_hline(
                y=low_level,
                line_dash="dot",
                line_color="deepskyblue",
                annotation_text="Liquidity Low"
            )

        # FAIR VALUE GAP — THREE-CANDLE APPROXIMATION
        if show_fvg and len(df) >= 3:
            start = max(2, len(df) - 40)

            for i in range(start, len(df)):
                first_high = float(df["High"].iloc[i - 2])
                first_low = float(df["Low"].iloc[i - 2])
                third_high = float(df["High"].iloc[i])
                third_low = float(df["Low"].iloc[i])

                if third_low > first_high:
                    fig.add_shape(
                        type="rect",
                        x0=df["Time"].iloc[i - 2],
                        x1=df["Time"].iloc[i],
                        y0=first_high,
                        y1=third_low,
                        fillcolor="rgba(0,193,118,0.18)",
                        line_width=0,
                        layer="below"
                    )

                elif third_high < first_low:
                    fig.add_shape(
                        type="rect",
                        x0=df["Time"].iloc[i - 2],
                        x1=df["Time"].iloc[i],
                        y0=third_high,
                        y1=first_low,
                        fillcolor="rgba(255,75,75,0.18)",
                        line_width=0,
                        layer="below"
                    )

        # POSSIBLE SWEEP AND MARKET STRUCTURE SHIFT
        signals = []

        if show_signals and len(df) > 12:
            for i in range(10, len(df)):
                row = df.iloc[i]
                previous_rows = df.iloc[i - 10:i]

                old_high = float(previous_rows["High"].max())
                old_low = float(previous_rows["Low"].min())

                if row["High"] > old_high and row["Close"] < old_high:
                    signals.append(
                        (i, "Possible Sweep High", "down")
                    )

                elif row["Low"] < old_low and row["Close"] > old_low:
                    signals.append(
                        (i, "Possible Sweep Low", "up")
                    )

                if i >= 5:
                    recent = df.iloc[i - 5:i]
                    swing_high = float(recent["High"].max())
                    swing_low = float(recent["Low"].min())

                    if (
                        row["Close"] > swing_high
                        and df["Close"].iloc[i - 1] <= swing_high
                    ):
                        signals.append(
                            (i, "Possible Bullish MSS", "up")
                        )

                    elif (
                        row["Close"] < swing_low
                        and df["Close"].iloc[i - 1] >= swing_low
                    ):
                        signals.append(
                            (i, "Possible Bearish MSS", "down")
                        )

            for i, label, direction in signals[-20:]:
                marker_color = (
                    "#00c176" if direction == "up"
                    else "#ff4b4b"
                )

                marker_symbol = (
                    "triangle-up" if direction == "up"
                    else "triangle-down"
                )

                marker_y = (
                    float(df["Low"].iloc[i])
                    if direction == "up"
                    else float(df["High"].iloc[i])
                )

                fig.add_trace(go.Scatter(
                    x=[df["Time"].iloc[i]],
                    y=[marker_y],
                    mode="markers",
                    marker=dict(
                        symbol=marker_symbol,
                        size=11,
                        color=marker_color
                    ),
                    name=label,
                    showlegend=False,
                    hovertemplate=(
                        label + "<br>Price: %{y}<extra></extra>"
                    )
                ))

        fig.update_layout(
            title=f"{symbol} — {timeframe} Candlestick Chart",
            template="plotly_dark",
            height=650,
            xaxis_rangeslider_visible=False,
            hovermode="x unified",
            margin=dict(l=10, r=10, t=55, b=10)
        )

        fig.update_yaxes(side="right")

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "scrollZoom": True,
                "displaylogo": False
            }
        )

        with st.expander("Recent Candle Data"):
            st.dataframe(
                df.tail(15).sort_values(
                    "Time", ascending=False
                ),
                use_container_width=True,
                hide_index=True
            )

        with st.expander("ICT Markers"):
            if signals:
                marker_data = []

                for i, label, direction in signals[-20:]:
                    marker_data.append({
                        "Time UTC": df["Time"].iloc[i],
                        "Signal": label,
                        "Direction": direction,
                        "Close": float(df["Close"].iloc[i])
                    })

                st.dataframe(
                    pd.DataFrame(marker_data),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Abhi koi possible marker nahi mila.")

    except Exception as error:
        st.error("Market data load nahi ho saka.")
        st.code(f"{type(error).__name__}: {error}")
        st.info(
            "Internet, exchange availability aur Logs check karein."
        )

trading_chart()

st.warning(
    "ICT markers simplified estimates hain, guaranteed signals nahi. "
    "Live price aur candle updates exchange/network par depend karte hain. "
    "Yeh app trade execute nahi karti."
                )
