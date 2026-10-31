import json
import requests
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Abdul Rauf King - Multi Market AI",
    page_icon="🥇",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.stApp { background: #080d18; color: #e8edf7; }
.block-container {
    max-width: 1120px !important;
    padding-top: .7rem !important;
    padding-left: .8rem !important;
    padding-right: .8rem !important;
    padding-bottom: 2rem !important;
}
h1 { font-size: 1.55rem !important; line-height: 1.15 !important; margin: 0 0 .2rem 0 !important; }
h2, h3, p, label, [data-testid="stMarkdownContainer"] { color: #e8edf7; }
[data-testid="stSelectbox"] > div > div { background: #111a2b; border: 1px solid #26344d; border-radius: 12px; }
[data-testid="stMetric"] { background: #111a2b; border: 1px solid #26344d; padding: 12px 14px; border-radius: 13px; }
[data-testid="stMetricLabel"] { color: #91a2bd !important; }
[data-testid="stMetricValue"] { color: #f4f7ff !important; }
div[data-testid="stAlert"] { border-radius: 14px; }
.ark-hero { background: linear-gradient(120deg,#121f35,#101827 65%,#172b40); border:1px solid #2a3c59; border-radius:17px; padding:17px; margin:8px 0 14px; }
.ark-kicker { color:#8ea5c7; font-size:11px; letter-spacing:1.5px; font-weight:700; }
.ark-title { color:#f7f9ff; font-size:23px; font-weight:800; margin-top:3px; }
.ark-sub { color:#9aabc4; font-size:12px; margin-top:4px; }
.ark-pill { display:inline-block; padding:6px 11px; border-radius:99px; font-size:11px; font-weight:800; letter-spacing:.7px; background:#3b1b25; color:#ff8d9a; border:1px solid #71313d; }
.ark-pill.bull { background:#123629; color:#72e3ad; border-color:#24664a; }
.ark-pill.neutral { background:#342d18; color:#f2d27c; border-color:#66552a; }
.ark-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:9px; margin:12px 0 16px; }
.ark-card { background:#111a2b; border:1px solid #26344d; border-radius:13px; padding:12px; min-width:0; }
.ark-label { color:#8ea0bb; font-size:11px; font-weight:650; letter-spacing:.35px; }
.ark-value { color:#f5f7fc; font-size:20px; font-weight:750; margin-top:5px; overflow-wrap:anywhere; }
.ark-note { color:#8293ad; font-size:10px; margin-top:3px; }
.ark-section { color:#f2f5fc; font-size:16px; font-weight:800; margin:18px 0 7px; }
.ark-score-wrap { background:#111a2b; border:1px solid #26344d; border-radius:14px; padding:13px; margin:10px 0; }
.ark-score-row { display:flex; justify-content:space-between; gap:10px; color:#a9b8ce; font-size:12px; margin:5px 0; }
.ark-track { height:7px; border-radius:99px; background:#25334a; overflow:hidden; margin-bottom:10px; }
.ark-fill-bull { height:100%; background:#28c58b; }
.ark-fill-bear { height:100%; background:#ed6474; }
@media (min-width:700px) { .ark-grid { grid-template-columns:repeat(4,minmax(0,1fr)); } }
iframe { width:100% !important; touch-action:pan-y !important; }
body { overscroll-behavior-y:auto !important; }
</style>
""", unsafe_allow_html=True)

ASSETS = {
    "Gold (XAUUSD)": {"tv": "VANTAGE:XAUUSD", "feed": "XAUUSD", "label": "Gold"},
    "Bitcoin (BTCUSDT)": {"tv": "BINANCE:BTCUSDT", "feed": "BTCUSDT", "label": "Bitcoin"},
    "Ethereum (ETHUSDT)": {"tv": "BINANCE:ETHUSDT", "feed": "ETHUSDT", "label": "Ethereum"},
    "EUR/USD": {"tv": "FX:EURUSD", "feed": "YAHOO:EURUSD=X", "label": "Euro / US Dollar"},
    "GBP/USD": {"tv": "FX:GBPUSD", "feed": "YAHOO:GBPUSD=X", "label": "British Pound / US Dollar"},
    "USD/JPY": {"tv": "FX:USDJPY", "feed": "YAHOO:USDJPY=X", "label": "US Dollar / Japanese Yen"},
}
selected_asset = st.selectbox("Market pair", list(ASSETS.keys()), index=0)
asset = ASSETS[selected_asset]
SYMBOL = asset["tv"]
FEED_SYMBOL = asset["feed"]
ASSET_LABEL = asset["label"]

st.title("👑 ABDUL RAUF KING")
st.caption(f"{ASSET_LABEL.upper()} — {FEED_SYMBOL}")

# TradingView market quote strip for the selected pair.
ticker_config = {
    "symbols": [{"proName": SYMBOL, "title": ASSET_LABEL}],
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
selected = st.selectbox("Chart timeframe", list(timeframes.keys()), index=2)
tv_interval, api_interval = timeframes[selected]

# TradingView chart follows the selected market pair.
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
st.subheader(f"📍 ICT BABA — {FEED_SYMBOL} Liquidity / MSS / FVG")
st.warning(
    "Original TradingView Vantage chart upar safe hai. Neeche ICT markings ek alag "
    "public MT5 XAUUSD data feed par calculate hoti hain; yeh Vantage broker candles "
    "nahi hain, isliye dono charts ke prices mein farq ho sakta hai."
)

@st.cache_data(ttl=30, show_spinner=False)
def load_ohlc(feed_symbol, interval):
    headers = {"Accept": "application/json", "User-Agent": "AbdulRaufKing-Chart/1.0"}
    if feed_symbol == "XAUUSD":
        url = f"https://biquote.io/api/XAUUSD/ohlc?interval={interval}&limit=500"
        response = requests.get(url, timeout=(5, 15), headers=headers)
        response.raise_for_status()
        if len(response.content) > 2_000_000:
            raise ValueError("Market data response is unexpectedly large.")
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Market data response format is invalid.")
        bars = payload.get("bars", [])
        if not isinstance(bars, list) or not bars or len(bars) > 1000:
            raise ValueError("Gold feed ne valid candle list return nahi ki.")
        frame = pd.DataFrame(bars)
    elif feed_symbol.startswith("YAHOO:"):
        # Public Yahoo Finance FX candles; no API key is required.
        yahoo_symbol = feed_symbol.split(":", 1)[1]
        yahoo_interval = "60m" if interval == "4h" else interval
        period = "5d" if interval == "1m" else "1mo"
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
        response = requests.get(
            url,
            params={"interval": yahoo_interval, "range": period},
            timeout=(5, 15),
            headers={**headers, "User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()
        if len(response.content) > 2_000_000:
            raise ValueError("FX data response is unexpectedly large.")
        payload = response.json()
        result = payload.get("chart", {}).get("result")
        if not result:
            raise ValueError("Yahoo FX feed ne candles return nahi ki.")
        quote = result[0].get("indicators", {}).get("quote", [{}])[0]
        timestamps = result[0].get("timestamp", [])
        if not timestamps or not quote:
            raise ValueError("FX candle data is empty.")
        frame = pd.DataFrame({
            "openTime": pd.to_datetime(timestamps, unit="s", utc=True),
            "open": quote.get("open", []),
            "high": quote.get("high", []),
            "low": quote.get("low", []),
            "close": quote.get("close", []),
        })
        if interval == "4h":
            frame = frame.set_index("openTime").resample("4h").agg({
                "open": "first", "high": "max", "low": "min", "close": "last"
            }).dropna().reset_index()
    else:
        # Binance public spot klines for BTCUSDT and ETHUSDT; no API key required.
        url = "https://api.binance.com/api/v3/klines"
        response = requests.get(
            url,
            params={"symbol": feed_symbol, "interval": interval, "limit": 500},
            timeout=(5, 15),
            headers=headers,
        )
        response.raise_for_status()
        if len(response.content) > 2_000_000:
            raise ValueError("Market data response is unexpectedly large.")
        bars = response.json()
        if not isinstance(bars, list) or not bars or len(bars) > 500:
            raise ValueError("Crypto feed ne valid candle list return nahi ki.")
        frame = pd.DataFrame(bars, columns=[
            "openTime", "open", "high", "low", "close", "volume",
            "closeTime", "quoteVolume", "trades", "takerBuyBase",
            "takerBuyQuote", "ignore",
        ])
    required = ["openTime", "open", "high", "low", "close"]
    if not all(col in frame.columns for col in required):
        raise ValueError("OHLC response ka format expected format se different hai.")
    if feed_symbol in ("BTCUSDT", "ETHUSDT"):
        frame["openTime"] = pd.to_datetime(frame["openTime"], unit="ms", utc=True, errors="coerce")
    else:
        frame["openTime"] = pd.to_datetime(frame["openTime"], utc=True, errors="coerce")
    for col in ["open", "high", "low", "close"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame.dropna(subset=required).sort_values("openTime").drop_duplicates("openTime")
    return frame.tail(450).reset_index(drop=True)

def add_ict_marks(fig, df, swing_len=5):
    """Draw a small, recent set of ICT marks so labels stay readable on mobile."""
    highs = df["high"].tolist()
    lows = df["low"].tolist()
    closes = df["close"].tolist()
    times = df["openTime"].tolist()

    last_ph = None
    last_pl = None
    swept_high = False
    swept_low = False
    recent_from = max(0, len(df) - 80)
    sweep_events = []
    mss_events = []
    fvg_events = []

    # Process all bars to keep swing structure correct; only display recent marks.
    for i in range(len(df)):
        p = i - swing_len
        if p >= swing_len:
            window_h = highs[p - swing_len:p + swing_len + 1]
            window_l = lows[p - swing_len:p + swing_len + 1]
            if highs[p] == max(window_h) and window_h.count(highs[p]) == 1:
                last_ph = highs[p]
                swept_high = False
            if lows[p] == min(window_l) and window_l.count(lows[p]) == 1:
                last_pl = lows[p]
                swept_low = False

        if i >= recent_from:
            if last_ph is not None and not swept_high and highs[i] > last_ph and closes[i] < last_ph:
                sweep_events.append((times[i], highs[i], "BSL sweep", "#ff7b86", -30))
                swept_high = True
            if last_pl is not None and not swept_low and lows[i] < last_pl and closes[i] > last_pl:
                sweep_events.append((times[i], lows[i], "SSL sweep", "#35c9c0", 30))
                swept_low = True

            prev_close = closes[i - 1] if i > 0 else closes[i]
            if last_ph is not None and prev_close <= last_ph < closes[i]:
                mss_events.append((times[i], last_ph, "MSS ↑", "#75e69a", -38))
            if last_pl is not None and prev_close >= last_pl > closes[i]:
                mss_events.append((times[i], last_pl, "MSS ↓", "#ff7b86", 38))

            # Keep only recent FVG zones; do not print a text label on every candle.
            if i >= 2 and lows[i] > highs[i - 2]:
                fvg_events.append((times[i - 2], times[i], highs[i - 2], lows[i], "bull"))
            if i >= 2 and highs[i] < lows[i - 2]:
                fvg_events.append((times[i - 2], times[i], highs[i], lows[i - 2], "bear"))

    if last_ph is not None:
        fig.add_hline(y=last_ph, line_dash="dot", line_color="#ff5c6c",
                      annotation_text="BSL", annotation_position="top left")
    if last_pl is not None:
        fig.add_hline(y=last_pl, line_dash="dot", line_color="#35c9c0",
                      annotation_text="SSL", annotation_position="bottom left")

    # Limit labels to the latest two events of each type.
    for x, y, label, color, offset in sweep_events[-2:]:
        fig.add_annotation(x=x, y=y, text=label, showarrow=True, arrowhead=2,
                           ax=0, ay=offset, font=dict(color=color, size=9))
    for x, y, label, color, offset in mss_events[-2:]:
        fig.add_annotation(x=x, y=y, text=label, showarrow=True, arrowhead=2,
                           ax=0, ay=offset, font=dict(color=color, size=10))

    for x0, x1, y0, y1, direction in fvg_events[-5:]:
        bullish = direction == "bull"
        color = "rgba(55,210,130,0.14)" if bullish else "rgba(255,85,100,0.12)"
        edge = "rgba(55,210,130,0.55)" if bullish else "rgba(255,85,100,0.50)"
        fig.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                      fillcolor=color, line=dict(color=edge, width=1), layer="below")

try:
    with st.spinner(f"{ASSET_LABEL} candles aur ICT levels load ho rahe hain..."):
        ict_df = load_ohlc(FEED_SYMBOL, api_interval)

    # Calculate common technical indicators on the selected market feed.
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

    # Supertrend (10, 3): ATR-based trend direction and trailing line.
    st_period = 10
    st_multiplier = 3.0
    st_atr = true_range.ewm(alpha=1/st_period, adjust=False).mean()
    hl2 = (high + low) / 2
    basic_upper = hl2 + st_multiplier * st_atr
    basic_lower = hl2 - st_multiplier * st_atr
    final_upper = basic_upper.copy()
    final_lower = basic_lower.copy()
    st_line = pd.Series(index=ict_df.index, dtype="float64")
    st_direction = pd.Series(index=ict_df.index, dtype="object")
    for i in range(len(ict_df)):
        if i > 0:
            final_upper.iloc[i] = basic_upper.iloc[i] if basic_upper.iloc[i] < final_upper.iloc[i-1] or close.iloc[i-1] > final_upper.iloc[i-1] else final_upper.iloc[i-1]
            final_lower.iloc[i] = basic_lower.iloc[i] if basic_lower.iloc[i] > final_lower.iloc[i-1] or close.iloc[i-1] < final_lower.iloc[i-1] else final_lower.iloc[i-1]
        if i == 0:
            st_direction.iloc[i] = "BULLISH" if close.iloc[i] >= hl2.iloc[i] else "BEARISH"
        elif st_direction.iloc[i-1] == "BEARISH":
            st_direction.iloc[i] = "BULLISH" if close.iloc[i] > final_upper.iloc[i] else "BEARISH"
        else:
            st_direction.iloc[i] = "BEARISH" if close.iloc[i] < final_lower.iloc[i] else "BULLISH"
        st_line.iloc[i] = final_lower.iloc[i] if st_direction.iloc[i] == "BULLISH" else final_upper.iloc[i]
    ict_df["Supertrend 10,3"] = st_line
    ict_df["Supertrend Direction"] = st_direction

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
    price_col1.metric("Selected market price", f"{last['close']:,.2f}")
    price_col2.metric("Feed timeframe", selected)
    price_col3.metric("Bars loaded", f"{len(ict_df)}")

    fig = go.Figure(data=[go.Candlestick(
        x=ict_df["openTime"],
        open=ict_df["open"],
        high=ict_df["high"],
        low=ict_df["low"],
        close=ict_df["close"],
        name=FEED_SYMBOL,
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
    fig.add_trace(go.Scatter(x=ict_df["openTime"], y=ict_df["Supertrend 10,3"].where(ict_df["Supertrend Direction"] == "BULLISH"), mode="lines", name="Supertrend bullish", line=dict(color="#27d69a", width=2)))
    fig.add_trace(go.Scatter(x=ict_df["openTime"], y=ict_df["Supertrend 10,3"].where(ict_df["Supertrend Direction"] == "BEARISH"), mode="lines", name="Supertrend bearish", line=dict(color="#ff6577", width=2)))
    add_ict_marks(fig, ict_df)
    fig.update_layout(
        height=620,
        template="plotly_dark",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        margin=dict(l=8, r=8, t=30, b=20),
        xaxis_rangeslider_visible=False,
        xaxis_title="Time (UTC)",
        yaxis_title=f"{ASSET_LABEL} price",
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
    # Pipflow-inspired mobile-first analysis dashboard.
    ema_bull = bool(last["close"] > last["EMA 20"] > last["EMA 50"])
    ema_bear = bool(last["close"] < last["EMA 20"] < last["EMA 50"])
    rsi_bull = bool(pd.notna(last["RSI 14"]) and last["RSI 14"] > 50)
    rsi_bear = bool(pd.notna(last["RSI 14"]) and last["RSI 14"] < 50)
    macd_bull = bool(pd.notna(last["MACD"]) and last["MACD"] > last["MACD Signal"])
    macd_bear = bool(pd.notna(last["MACD"]) and last["MACD"] < last["MACD Signal"])
    bb_bull = bool(pd.notna(last["BB Middle"]) and last["close"] > last["BB Middle"])
    bb_bear = bool(pd.notna(last["BB Middle"]) and last["close"] < last["BB Middle"])
    supertrend_bull = bool(last["Supertrend Direction"] == "BULLISH")
    supertrend_bear = bool(last["Supertrend Direction"] == "BEARISH")
    bull_total = sum([ema_bull, rsi_bull, macd_bull, bb_bull, supertrend_bull])
    bear_total = sum([ema_bear, rsi_bear, macd_bear, bb_bear, supertrend_bear])

    if bull_total >= 3 and bull_total > bear_total:
        bias, pill_class, bias_detail = "BULLISH", "bull", "Bullish conditions are stronger; wait for ICT entry confirmation."
    elif bear_total >= 3 and bear_total > bull_total:
        bias, pill_class, bias_detail = "BEARISH", "", "Bearish conditions are stronger; wait for ICT entry confirmation."
    else:
        bias, pill_class, bias_detail = "NEUTRAL", "neutral", "Signals are mixed; wait for a clearer setup."

    rsi_value = last["RSI 14"]
    adx_value = last["ADX 14"]
    atr_value = last["ATR 14"]
    macd_value = last["MACD"]
    bb_upper = last["BB Upper"]
    bb_lower = last["BB Lower"]
    rsi_text = "—" if pd.isna(rsi_value) else f"{rsi_value:.1f}"
    macd_text = "—" if pd.isna(macd_value) else f"{macd_value:.3f}"
    bb_upper_text = "—" if pd.isna(bb_upper) else f"{bb_upper:,.2f}"
    bb_lower_text = "—" if pd.isna(bb_lower) else f"{bb_lower:,.2f}"
    atr_text = "—" if pd.isna(atr_value) else f"{atr_value:.3f}"
    adx_text = "—" if pd.isna(adx_value) else f"{adx_value:.1f}"
    rsi_state = "Overbought" if pd.notna(rsi_value) and rsi_value >= 70 else ("Oversold" if pd.notna(rsi_value) and rsi_value <= 30 else "Middle range")
    adx_state = "Strong trend" if pd.notna(adx_value) and adx_value >= 25 else "Weak / developing"
    atr_state = "High volatility" if pd.notna(atr_value) and atr_value > ict_df["ATR 14"].tail(50).median() else "Normal volatility"

    st.markdown(f"""
    <div class="ark-hero">
      <div class="ark-kicker">ABDUL RAUF KING · {ASSET_LABEL.upper()} MARKET INTELLIGENCE</div>
      <div class="ark-title">AI Market Analyst</div>
      <div class="ark-sub">{FEED_SYMBOL} · {selected} · Rule-based indicator confluence</div>
      <div style="margin-top:13px"><span class="ark-pill {pill_class}">{bias} MARKET BIAS</span></div>
      <div class="ark-sub" style="margin-top:10px">{bias_detail}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="ark-section">📊 Indicator dashboard</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="ark-grid">
      <div class="ark-card"><div class="ark-label">EMA 20</div><div class="ark-value">{last["EMA 20"]:,.2f}</div><div class="ark-note">Short trend</div></div>
      <div class="ark-card"><div class="ark-label">EMA 50</div><div class="ark-value">{last["EMA 50"]:,.2f}</div><div class="ark-note">Long trend</div></div>
      <div class="ark-card"><div class="ark-label">RSI 14</div><div class="ark-value">{rsi_text}</div><div class="ark-note">{rsi_state}</div></div>
      <div class="ark-card"><div class="ark-label">MACD</div><div class="ark-value">{macd_text}</div><div class="ark-note">Momentum</div></div>
      <div class="ark-card"><div class="ark-label">Bollinger upper</div><div class="ark-value">{bb_upper_text}</div><div class="ark-note">Upper volatility band</div></div>
      <div class="ark-card"><div class="ark-label">Bollinger lower</div><div class="ark-value">{bb_lower_text}</div><div class="ark-note">Lower volatility band</div></div>
      <div class="ark-card"><div class="ark-label">ATR 14</div><div class="ark-value">{atr_text}</div><div class="ark-note">{atr_state}</div></div>
      <div class="ark-card"><div class="ark-label">ADX 14</div><div class="ark-value">{adx_text}</div><div class="ark-note">{adx_state}</div></div>
      <div class="ark-card"><div class="ark-label">SUPERTREND 10,3</div><div class="ark-value">{last["Supertrend Direction"]}</div><div class="ark-note">ATR trend confirmation</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="ark-section">🧠 Signal confluence</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="ark-score-wrap">
      <div class="ark-score-row"><span>Bullish confirmation</span><strong>{bull_total}/5</strong></div>
      <div class="ark-track"><div class="ark-fill-bull" style="width:{bull_total * 20}%"></div></div>
      <div class="ark-score-row"><span>Bearish confirmation</span><strong>{bear_total}/5</strong></div>
      <div class="ark-track"><div class="ark-fill-bear" style="width:{bear_total * 20}%"></div></div>
      <div class="ark-note">EMA trend · RSI momentum · MACD momentum · Bollinger position · Supertrend direction</div>
    </div>
    """, unsafe_allow_html=True)
    if bias == "BULLISH":
        st.success("BULLISH BIAS — ICT sweep, MSS aur FVG confirmation ka intezar karein.")
    elif bias == "BEARISH":
        st.error("BEARISH BIAS — ICT sweep, MSS aur FVG confirmation ka intezar karein.")
    else:
        st.info("NEUTRAL BIAS — abhi indicators ek direction par agree nahi kar rahe.")



    # Full ICT + indicator signal. Use closed candles only to avoid intrabar repaint.
    closed = ict_df.iloc[:-1].copy() if len(ict_df) > 3 else ict_df.copy()
    signal_side = "WAIT"
    signal_reasons = []
    sweep_index = None
    mss_confirmed = False
    fvg_confirmed = False
    if len(closed) >= 30:
        recent_start = max(20, len(closed) - 12)
        for j in range(recent_start, len(closed)):
            prior = closed.iloc[max(0, j - 20):j]
            bar = closed.iloc[j]
            prior_low = float(prior["low"].min())
            prior_high = float(prior["high"].max())
            if float(bar["low"]) < prior_low and float(bar["close"]) > prior_low:
                sweep_index = (j, "BUY", prior_high)
            elif float(bar["high"]) > prior_high and float(bar["close"]) < prior_high:
                sweep_index = (j, "SELL", prior_low)

        if sweep_index is not None:
            sj, sweep_direction, structure_level = sweep_index
            later = closed.iloc[sj + 1:]
            if not later.empty:
                if sweep_direction == "BUY":
                    mss_confirmed = bool((later["close"] > structure_level).any())
                    fvg_confirmed = bool(any(
                        float(closed.iloc[i]["low"]) > float(closed.iloc[i - 2]["high"])
                        for i in range(max(sj + 1, len(closed) - 8), len(closed))
                        if i >= 2
                    ))
                    if mss_confirmed and fvg_confirmed and bull_total >= 2:
                        signal_side = "BUY"
                        signal_reasons = ["Sell-side liquidity sweep", "Bullish MSS", "Bullish FVG", f"{bull_total}/5 bullish indicator checks"]
                else:
                    mss_confirmed = bool((later["close"] < structure_level).any())
                    fvg_confirmed = bool(any(
                        float(closed.iloc[i]["high"]) < float(closed.iloc[i - 2]["low"])
                        for i in range(max(sj + 1, len(closed) - 8), len(closed))
                        if i >= 2
                    ))
                    if mss_confirmed and fvg_confirmed and bear_total >= 2:
                        signal_side = "SELL"
                        signal_reasons = ["Buy-side liquidity sweep", "Bearish MSS", "Bearish FVG", f"{bear_total}/5 bearish indicator checks"]

    signal_entry = float(closed.iloc[-1]["close"])
    signal_atr = float(closed.iloc[-1]["ATR 14"]) if pd.notna(closed.iloc[-1]["ATR 14"]) else 0.0
    signal_sl = signal_tp1 = signal_tp2 = signal_tp3 = None
    signal_rr = "—"
    if signal_side == "BUY" and signal_atr > 0:
        signal_sl = float(closed["low"].tail(8).min()) - 0.15 * signal_atr
        risk = signal_entry - signal_sl
        if risk > 0:
            signal_tp1, signal_tp2, signal_tp3 = signal_entry + risk, signal_entry + 2*risk, signal_entry + 3*risk
            signal_rr = "1:1 / 1:2 / 1:3"
        else:
            signal_side = "WAIT"
    elif signal_side == "SELL" and signal_atr > 0:
        signal_sl = float(closed["high"].tail(8).max()) + 0.15 * signal_atr
        risk = signal_sl - signal_entry
        if risk > 0:
            signal_tp1, signal_tp2, signal_tp3 = signal_entry - risk, signal_entry - 2*risk, signal_entry - 3*risk
            signal_rr = "1:1 / 1:2 / 1:3"
        else:
            signal_side = "WAIT"
    else:
        signal_side = "WAIT"

    st.markdown('<div class="ark-section">🎯 Full trading signal</div>', unsafe_allow_html=True)
    if signal_side == "WAIT":
        st.info("WAIT — abhi closed candles par Liquidity Sweep + MSS + FVG aur indicator confirmation ek saath nahi mile. Entry, SL aur TP abhi issue nahi kiye gaye.")
        st.caption("Signal logic: recent 20-bar liquidity level, confirmed candle close, recent FVG aur kam az kam 2/5 indicator checks (EMA, RSI, MACD, Bollinger, Supertrend). Latest open candle ignore ki gayi hai.")
    else:
        st.markdown(f"""
        <div class="ark-hero">
          <div class="ark-kicker">{FEED_SYMBOL} · {selected} · CLOSED-CANDLE SETUP</div>
          <div class="ark-title">{signal_side} SIGNAL</div>
          <div class="ark-sub">ICT sweep + MSS + FVG and indicator confluence confirmed by the rule set.</div>
        </div>
        """, unsafe_allow_html=True)
        def fmt_level(value):
            return f"{value:,.2f}" if value is not None else "—"
        st.markdown(f"""
        <div class="ark-grid">
          <div class="ark-card"><div class="ark-label">ENTRY reference</div><div class="ark-value">{fmt_level(signal_entry)}</div><div class="ark-note">Last closed candle; not a live fill price</div></div>
          <div class="ark-card"><div class="ark-label">STOP LOSS</div><div class="ark-value">{fmt_level(signal_sl)}</div><div class="ark-note">Beyond recent 8-bar swing + ATR buffer</div></div>
          <div class="ark-card"><div class="ark-label">TAKE PROFIT 1</div><div class="ark-value">{fmt_level(signal_tp1)}</div><div class="ark-note">1R target</div></div>
          <div class="ark-card"><div class="ark-label">TAKE PROFIT 2</div><div class="ark-value">{fmt_level(signal_tp2)}</div><div class="ark-note">2R target</div></div>
          <div class="ark-card"><div class="ark-label">TAKE PROFIT 3</div><div class="ark-value">{fmt_level(signal_tp3)}</div><div class="ark-note">3R target</div></div>
          <div class="ark-card"><div class="ark-label">RISK / REWARD</div><div class="ark-value">{signal_rr}</div><div class="ark-note">Calculated from entry to stop</div></div>
        </div>
        """, unsafe_allow_html=True)
        st.success("Signal confirmations: " + " · ".join(signal_reasons))
        st.warning("Ye educational rule-based setup hai, guaranteed prediction ya broker order nahi. Spread, slippage, contract size aur broker digits check karke demo par verify karein.")

    st.caption("ADX trend strength aur ATR volatility measure karta hai; Bollinger Bands price range/volatility dikhate hain. Yeh analysis hai, guaranteed BUY/SELL signal nahi.")

    st.caption(
        "ICT labels are rule-based technical markers for study, not guaranteed trade entries. "
        "Pivot levels confirm only after the selected swing length; current candle may still be open."
    )
    if st.button("Refresh ICT data"):
        st.cache_data.clear()
        st.rerun()
except Exception:
    # Avoid exposing raw upstream/server exception details in the public UI.
    st.error("ICT data load nahi ho saka. Data feed ya network temporarily unavailable ho sakta hai.")
    st.info("Selected market feed ya network check karein, phir refresh karein.")

