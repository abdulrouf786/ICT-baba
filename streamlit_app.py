import json
import requests
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Abdul Rauf King - Vantage Gold",
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
h1 {
    font-size: 1.3rem !important;
    line-height: 1.15 !important;
    white-space: nowrap !important;
    margin-top: 0 !important;
    margin-bottom: 0.25rem !important;
}
[data-testid='stSelectbox'] { margin-bottom: 0.25rem !important; }
iframe { width: 100% !important; touch-action: pan-y !important; }
body { overscroll-behavior-y: auto !important; }
</style>
""", unsafe_allow_html=True)

SYMBOL = "VANTAGE:XAUUSD"

st.title("👑 ABDUL RAUF KING")
st.caption("VANTAGE GOLD — XAUUSD")

# Original TradingView Vantage Gold quote strip.
ticker_config = {
    "symbols": [{"proName": SYMBOL, "title": "Vantage Gold"}],
    "colorTheme": "dark",
    "isTransparent": False,
    "displayMode": "adaptive",
    "locale": "en",
}
ticker_html = f"""
<div class="tradingview-widget-container" style="width:100%;height:46px">
  <div class="tradingview-widget-container__widget"></div>
  <script type="text/javascript"
    src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js"
    async>
    {json.dumps(ticker_config)}
  </script>
</div>
"""
components.html(ticker_html, height=50, scrolling=False)

timeframes = {
    "1 Minute": ("1", "1m"),
    "5 Minutes": ("5", "5m"),
    "15 Minutes": ("15", "15m"),
    "1 Hour": ("60", "1h"),
    "4 Hours": ("240", "4h"),
}
selected = st.selectbox("Gold timeframe", list(timeframes.keys()), index=2)
tv_interval, api_interval = timeframes[selected]

# The original Vantage TradingView chart is preserved unchanged.
CHART_HEIGHT = 650
widget_config = {
    "autosize": False,
    "height": CHART_HEIGHT,
    "width": "100%",
    "symbol": SYMBOL,
    "interval": tv_interval,
    "timezone": "Asia/Karachi",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "allow_symbol_change": False,
    "calendar": False,
    "details": True,
    "hide_side_toolbar": True,
    "hide_top_toolbar": False,
    "hide_legend": False,
    "hide_volume": False,
    "hotlist": False,
    "save_image": False,
    "withdateranges": True,
    "support_host": "https://www.tradingview.com",
}
widget_html = f"""
<div class="tradingview-widget-container" style="height:{CHART_HEIGHT}px;width:100%">
  <div class="tradingview-widget-container__widget" style="height:{CHART_HEIGHT}px;width:100%"></div>
  <script type="text/javascript"
    src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js"
    async>
    {json.dumps(widget_config)}
  </script>
</div>
"""
components.html(widget_html, height=CHART_HEIGHT + 20, scrolling=True)

st.divider()
st.subheader("📍 ICT BABA — Liquidity / MSS / FVG")
st.warning(
    "Original TradingView Vantage chart upar safe hai. Neeche ICT markings ek alag "
    "public MT5 XAUUSD data feed par calculate hoti hain; yeh Vantage broker candles "
    "nahi hain, isliye dono charts ke prices mein farq ho sakta hai."
)

@st.cache_data(ttl=30, show_spinner=False)
def load_ohlc(interval):
    url = f"https://biquote.io/api/XAUUSD/ohlc?interval={interval}&limit=500"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    payload = response.json()
    bars = payload.get("bars", [])
    if not bars:
        raise ValueError("Gold OHLC feed ne candles return nahi ki.")
    frame = pd.DataFrame(bars)
    required = ["openTime", "open", "high", "low", "close"]
    if not all(col in frame.columns for col in required):
        raise ValueError("OHLC response ka format expected format se different hai.")
    frame["openTime"] = pd.to_datetime(frame["openTime"], utc=True, errors="coerce")
    for col in ["open", "high", "low", "close"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame.dropna(subset=required).sort_values("openTime").drop_duplicates("openTime")
    return frame.tail(450).reset_index(drop=True)

def add_ict_marks(fig, df, swing_len=5):
    highs = df["high"].tolist()
    lows = df["low"].tolist()
    closes = df["close"].tolist()
    times = df["openTime"].tolist()

    last_ph = None
    last_pl = None
    swept_high = False
    swept_low = False
    swing_highs = []
    swing_lows = []

    # Confirm pivots only after swing_len bars have formed on the right.
    for i in range(len(df)):
        p = i - swing_len
        if p >= swing_len:
            window_h = highs[p - swing_len:p + swing_len + 1]
            window_l = lows[p - swing_len:p + swing_len + 1]
            if highs[p] == max(window_h) and window_h.count(highs[p]) == 1:
                last_ph = highs[p]
                swept_high = False
                swing_highs.append((p, last_ph))
            if lows[p] == min(window_l) and window_l.count(lows[p]) == 1:
                last_pl = lows[p]
                swept_low = False
                swing_lows.append((p, last_pl))

        # BSL / SSL reference levels
        if i == len(df) - 1:
            if last_ph is not None:
                fig.add_hline(y=last_ph, line_dash="dot", line_color="#ff5c6c",
                              annotation_text="BSL", annotation_position="top left")
            if last_pl is not None:
                fig.add_hline(y=last_pl, line_dash="dot", line_color="#35c9c0",
                              annotation_text="SSL", annotation_position="bottom left")

        # Liquidity sweep: wick runs the swing level, candle closes back through it.
        if last_ph is not None and not swept_high and highs[i] > last_ph and closes[i] < last_ph:
            fig.add_annotation(x=times[i], y=highs[i], text="BSL SWEEP",
                               showarrow=True, arrowhead=2, ax=0, ay=-35,
                               font=dict(color="#ff7b86", size=10))
            swept_high = True
        if last_pl is not None and not swept_low and lows[i] < last_pl and closes[i] > last_pl:
            fig.add_annotation(x=times[i], y=lows[i], text="SSL SWEEP",
                               showarrow=True, arrowhead=2, ax=0, ay=35,
                               font=dict(color="#35c9c0", size=10))
            swept_low = True

        # MSS: close crosses the latest confirmed swing level.
        prev_close = closes[i - 1] if i > 0 else closes[i]
        if last_ph is not None and prev_close <= last_ph < closes[i]:
            fig.add_annotation(x=times[i], y=last_ph, text="MSS ↑",
                               showarrow=True, arrowhead=2, ax=0, ay=-48,
                               font=dict(color="#75e69a", size=11))
            fig.add_trace(go.Scatter(
                x=[times[i]], y=[lows[i]], mode="markers+text",
                marker=dict(symbol="triangle-up", size=13, color="#75e69a"),
                text=["BUY"], textposition="bottom center",
                textfont=dict(color="#75e69a"), showlegend=False,
            ))
        if last_pl is not None and prev_close >= last_pl > closes[i]:
            fig.add_annotation(x=times[i], y=last_pl, text="MSS ↓",
                               showarrow=True, arrowhead=2, ax=0, ay=48,
                               font=dict(color="#ff7b86", size=11))
            fig.add_trace(go.Scatter(
                x=[times[i]], y=[highs[i]], mode="markers+text",
                marker=dict(symbol="triangle-down", size=13, color="#ff7b86"),
                text=["SELL"], textposition="top center",
                textfont=dict(color="#ff7b86"), showlegend=False,
            ))

        # Three-candle Fair Value Gaps.
        if i >= 2 and lows[i] > highs[i - 2]:
            fig.add_shape(
                type="rect", x0=times[i - 2], x1=times[i],
                y0=highs[i - 2], y1=lows[i],
                fillcolor="rgba(55,210,130,0.16)",
                line=dict(color="rgba(55,210,130,0.65)", width=1),
                layer="below",
            )
            fig.add_annotation(x=times[i], y=(highs[i - 2] + lows[i]) / 2,
                               text="Bull FVG", showarrow=False,
                               font=dict(color="#75e69a", size=8))
        if i >= 2 and highs[i] < lows[i - 2]:
            fig.add_shape(
                type="rect", x0=times[i - 2], x1=times[i],
                y0=highs[i], y1=lows[i - 2],
                fillcolor="rgba(255,85,100,0.14)",
                line=dict(color="rgba(255,85,100,0.65)", width=1),
                layer="below",
            )
            fig.add_annotation(x=times[i], y=(highs[i] + lows[i - 2]) / 2,
                               text="Bear FVG", showarrow=False,
                               font=dict(color="#ff7b86", size=8))

try:
    with st.spinner("Gold candles aur ICT levels load ho rahe hain..."):
        ict_df = load_ohlc(api_interval)

    # Calculate common technical indicators on the same XAUUSD OHLC feed.
    close = ict_df["close"]
    high = ict_df["high"]
    low = ict_df["low"]
    ict_df["EMA 20"] = close.ewm(span=20, adjust=False).mean()
    ict_df["EMA 50"] = close.ewm(span=50, adjust=False).mean()

    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss.replace(0, float("nan"))
    ict_df["RSI 14"] = 100 - (100 / (1 + rs))

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    ict_df["MACD"] = ema12 - ema26
    ict_df["MACD Signal"] = ict_df["MACD"].ewm(span=9, adjust=False).mean()

    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    ict_df["BB Upper"] = bb_mid + 2 * bb_std
    ict_df["BB Middle"] = bb_mid
    ict_df["BB Lower"] = bb_mid - 2 * bb_std

    previous_close = close.shift(1)
    true_range = pd.concat(
        [(high - low), (high - previous_close).abs(), (low - previous_close).abs()],
        axis=1,
    ).max(axis=1)
    ict_df["ATR 14"] = true_range.ewm(alpha=1/14, adjust=False).mean()

    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
    atr_safe = ict_df["ATR 14"].replace(0, float("nan"))
    plus_di = 100 * plus_dm.ewm(alpha=1/14, adjust=False).mean() / atr_safe
    minus_di = 100 * minus_dm.ewm(alpha=1/14, adjust=False).mean() / atr_safe
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, float("nan"))
    ict_df["ADX 14"] = dx.ewm(alpha=1/14, adjust=False).mean()

    last = ict_df.iloc[-1]
    price_col1, price_col2, price_col3 = st.columns(3)
    price_col1.metric("MT5 XAUUSD price", f"{last['close']:,.2f}")
    price_col2.metric("Feed timeframe", selected)
    price_col3.metric("Bars loaded", f"{len(ict_df)}")

    fig = go.Figure(data=[go.Candlestick(
        x=ict_df["openTime"],
        open=ict_df["open"],
        high=ict_df["high"],
        low=ict_df["low"],
        close=ict_df["close"],
        name="MT5 XAUUSD",
        increasing_line_color="#26a69a",
        decreasing_line_color="#ef5350",
    )])
    fig.add_trace(go.Scatter(
        x=ict_df["openTime"], y=ict_df["EMA 20"],
        mode="lines", name="EMA 20",
        line=dict(color="#f5c542", width=1.5),
    ))
    fig.add_trace(go.Scatter(
        x=ict_df["openTime"], y=ict_df["EMA 50"],
        mode="lines", name="EMA 50",
        line=dict(color="#42a5f5", width=1.5),
    ))
    add_ict_marks(fig, ict_df)
    fig.update_layout(
        height=620,
        template="plotly_dark",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        margin=dict(l=8, r=8, t=30, b=20),
        xaxis_rangeslider_visible=False,
        xaxis_title="Time (UTC)",
        yaxis_title="Gold price (USD/oz)",
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
    st.subheader("📊 Technical Indicators — EMA, RSI + 4")
    st.caption("Same XAUUSD OHLC feed par calculate kiye gaye indicators; EMA 20/50 chart par bhi plotted hain.")
    ind1, ind2, ind3 = st.columns(3)
    ind1.metric("EMA 20", f"{last['EMA 20']:,.2f}")
    ind2.metric("EMA 50", f"{last['EMA 50']:,.2f}")
    ind3.metric("RSI 14", "—" if pd.isna(last["RSI 14"]) else f"{last['RSI 14']:.1f}")
    ind4, ind5, ind6 = st.columns(3)
    ind4.metric("MACD", "—" if pd.isna(last["MACD"]) else f"{last['MACD']:.3f}")
    ind5.metric("Bollinger Upper", "—" if pd.isna(last["BB Upper"]) else f"{last['BB Upper']:,.2f}")
    ind6.metric("Bollinger Lower", "—" if pd.isna(last["BB Lower"]) else f"{last['BB Lower']:,.2f}")
    ind7, ind8 = st.columns(2)
    ind7.metric("ATR 14", "—" if pd.isna(last["ATR 14"]) else f"{last['ATR 14']:.3f}")
    ind8.metric("ADX 14", "—" if pd.isna(last["ADX 14"]) else f"{last['ADX 14']:.1f}")

    bullish_checks = [
        last["close"] > last["EMA 20"] > last["EMA 50"],
        pd.notna(last["RSI 14"]) and last["RSI 14"] > 50,
        pd.notna(last["MACD"]) and last["MACD"] > last["MACD Signal"],
    ]
    bearish_checks = [
        last["close"] < last["EMA 20"] < last["EMA 50"],
        pd.notna(last["RSI 14"]) and last["RSI 14"] < 50,
        pd.notna(last["MACD"]) and last["MACD"] < last["MACD Signal"],
    ]
    bullish_score = sum(bool(x) for x in bullish_checks)
    bearish_score = sum(bool(x) for x in bearish_checks)
    score1, score2 = st.columns(2)
    score1.metric("Basic bullish checks", f"{bullish_score}/3")
    score2.metric("Basic bearish checks", f"{bearish_score}/3")

    # Pipflow-style rule-based confluence summary (analysis only; no orders).
    st.subheader("🤖 AI CONFLUENCE — EMA + RSI + 4 INDICATORS")
    ema_bull = bool(last["close"] > last["EMA 20"] > last["EMA 50"])
    ema_bear = bool(last["close"] < last["EMA 20"] < last["EMA 50"])
    rsi_bull = bool(pd.notna(last["RSI 14"]) and last["RSI 14"] > 50)
    rsi_bear = bool(pd.notna(last["RSI 14"]) and last["RSI 14"] < 50)
    macd_bull = bool(pd.notna(last["MACD"]) and last["MACD"] > last["MACD Signal"])
    macd_bear = bool(pd.notna(last["MACD"]) and last["MACD"] < last["MACD Signal"])
    bb_bull = bool(pd.notna(last["BB Middle"]) and last["close"] > last["BB Middle"])
    bb_bear = bool(pd.notna(last["BB Middle"]) and last["close"] < last["BB Middle"])
    bull_total = sum([ema_bull, rsi_bull, macd_bull, bb_bull])
    bear_total = sum([ema_bear, rsi_bear, macd_bear, bb_bear])

    ai_left, ai_right = st.columns(2)
    ai_left.metric("Bullish confluence", f"{bull_total}/4")
    ai_right.metric("Bearish confluence", f"{bear_total}/4")
    if bull_total >= 3 and bull_total > bear_total:
        st.success("AI-style bias: BULLISH — multiple indicators agree. Wait for ICT entry confirmation.")
    elif bear_total >= 3 and bear_total > bull_total:
        st.error("AI-style bias: BEARISH — multiple indicators agree. Wait for ICT entry confirmation.")
    else:
        st.info("AI-style bias: NEUTRAL / MIXED — indicators do not agree strongly.")

    adx_value = last["ADX 14"]
    atr_value = last["ATR 14"]
    rsi_value = last["RSI 14"]
    rsi_state = "Overbought zone" if pd.notna(rsi_value) and rsi_value >= 70 else ("Oversold zone" if pd.notna(rsi_value) and rsi_value <= 30 else "Middle range")
    adx_state = "Strong trend" if pd.notna(adx_value) and adx_value >= 25 else "Weak / developing trend"
    atr_state = "High volatility" if pd.notna(atr_value) and atr_value > ict_df["ATR 14"].tail(50).median() else "Normal / low volatility"
    s1, s2, s3 = st.columns(3)
    s1.metric("RSI condition", rsi_state)
    s2.metric("ADX condition", adx_state)
    s3.metric("ATR condition", atr_state)
    st.caption("This is a transparent indicator checklist, not machine-learning prediction or a guaranteed trade signal. It does not place orders.")

    st.caption("ADX trend strength aur ATR volatility measure karta hai; Bollinger Bands price range/volatility dikhate hain. Yeh analysis hai, guaranteed BUY/SELL signal nahi.")

    st.caption(
        "ICT labels are rule-based technical markers for study, not guaranteed trade entries. "
        "Pivot levels confirm only after the selected swing length; current candle may still be open."
    )
    if st.button("Refresh ICT data"):
        st.cache_data.clear()
        st.rerun()
except Exception as exc:
    st.error(f"ICT data load nahi ho saka: {exc}")
    st.info("Original TradingView Vantage chart upar available rehna chahiye. Thori dair baad refresh karein.")

