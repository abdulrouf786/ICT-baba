import json
import requests
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import streamlit.components.v1 as components

def send_whatsapp_message(recipient, message):
    """Send a WhatsApp Cloud API text message using Streamlit Secrets."""
    token = st.secrets.get("WHATSAPP_ACCESS_TOKEN", "")
    phone_number_id = st.secrets.get("WHATSAPP_PHONE_NUMBER_ID", "")
    if not token or not phone_number_id:
        raise RuntimeError("WhatsApp Access Token ya Phone Number ID Secrets mein missing hai.")
    url = f"https://graph.facebook.com/v23.0/{phone_number_id}/messages"
    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": message},
        },
        timeout=(5, 20),
    )
    if not response.ok:
        raise RuntimeError(f"WhatsApp API error {response.status_code}: {response.text[:500]}")
    return response.json()

st.set_page_config(
    page_title="Abdul Rauf King - Multi Market AI",
    page_icon="🥇",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
:root { color-scheme:dark; }
.stApp { background:radial-gradient(ellipse at 8% -8%,#253b62 0%,transparent 38%),radial-gradient(ellipse at 95% 10%,#173e3c 0%,transparent 28%),linear-gradient(145deg,#070d18 0%,#0b1422 52%,#080e18 100%); color:#edf4ff; }
.block-container { max-width:1240px !important; padding:.8rem .85rem 2.5rem !important; }
h1 { font-size:1.55rem !important; line-height:1.15 !important; margin:0 0 .3rem !important; }
h2,h3,p,label,[data-testid="stMarkdownContainer"] { color:#e8edf7; }
[data-testid="stSelectbox"] { margin-bottom:.35rem; }
[data-testid="stSelectbox"] > div > div { background:linear-gradient(135deg,#172943,#101c30) !important; border:1px solid #496184 !important; border-radius:14px !important; min-height:46px; box-shadow:inset 0 1px #ffffff0a,0 7px 18px #0003; }
[data-testid="stSelectbox"] label { color:#b9c9e1 !important; font-size:12px !important; font-weight:800 !important; letter-spacing:.35px; }
[data-testid="stMetric"] { background:linear-gradient(145deg,#1a2b45,#101a2b) !important; border:1px solid #3b5274 !important; padding:14px 15px !important; border-radius:17px !important; box-shadow:0 10px 26px #0004,inset 0 1px #ffffff0a; }
[data-testid="stMetricLabel"] { color:#a9bdd9 !important; font-size:12px !important; font-weight:700 !important; }
[data-testid="stMetricValue"] { color:#f6f8ff !important; font-weight:850 !important; }
[data-testid="stMetricDelta"] { font-weight:750 !important; }
div[data-testid="stAlert"] { border-radius:15px !important; border:1px solid #405879 !important; background:#14243acc !important; }
.stButton button { min-height:44px; border-radius:13px; border:1px solid #59749a; background:linear-gradient(135deg,#24466b,#152b46); color:#f5f8ff; font-weight:800; box-shadow:0 7px 18px #0003; }
.stButton button:hover { border-color:#d8b86a; color:#fff; background:linear-gradient(135deg,#31577f,#1b3858); }
.ark-hero { background:radial-gradient(ellipse at 90% 0%,#c7a75b22 0%,transparent 42%),linear-gradient(118deg,#1b3455 0%,#111e32 56%,#122c31 100%); border:1px solid #6b7890; border-radius:22px; padding:21px 20px; margin:10px 0 16px; box-shadow:0 16px 38px #0006,inset 0 1px #ffffff18; position:relative; overflow:hidden; }
.ark-hero:after { content:""; position:absolute; width:170px; height:170px; right:-62px; bottom:-105px; border:1px solid #d7b96a66; border-radius:50%; box-shadow:0 0 0 16px #d7b96a0b,0 0 0 34px #d7b96a08; pointer-events:none; }
.ark-profile-row { display:flex; align-items:center; gap:17px; position:relative; z-index:1; }
.ark-avatar { width:104px; height:104px; flex:0 0 104px; object-fit:cover; object-position:center 28%; border-radius:50%; border:3px solid #d8b86a; padding:3px; background:#101a2a; box-shadow:0 0 0 5px #d8b86a20,0 8px 22px #0007; }
.ark-profile-copy { min-width:0; }
@media(max-width:520px) { .ark-hero { padding:15px 13px; } .ark-profile-row { gap:12px; } .ark-avatar { width:82px; height:82px; flex-basis:82px; } .ark-title { font-size:22px !important; } .ark-kicker { font-size:9px; letter-spacing:1.1px; } .ark-sub { font-size:10px; } }
.ark-kicker { color:#e0c783; font-size:10px; letter-spacing:2px; font-weight:900; }
.ark-title { color:#fff; font-size:clamp(23px,4vw,31px); font-weight:950; margin-top:6px; letter-spacing:.15px; text-shadow:0 3px 18px #0008; }
.ark-sub { color:#c0cde0; font-size:12px; margin-top:7px; line-height:1.6; letter-spacing:.35px; }
.ark-pill { display:inline-flex; align-items:center; gap:5px; padding:7px 12px; border-radius:99px; font-size:11px; font-weight:900; letter-spacing:.8px; background:#48212b; color:#ffadb6; border:1px solid #a34d5c; }
.ark-pill.bull { background:#123c31; color:#8df2c2; border-color:#328568; }
.ark-pill.neutral { background:#40351b; color:#ffe69a; border-color:#92763c; }
.ark-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; margin:13px 0 18px; }
.ark-card { background:linear-gradient(145deg,#1a2b44,#101a2a) !important; border:1px solid #3b5271 !important; border-radius:17px !important; padding:14px !important; min-width:0; box-shadow:0 9px 23px #0003,inset 0 1px #ffffff09; }
.ark-label { color:#aebfda; font-size:10px; font-weight:900; letter-spacing:.9px; text-transform:uppercase; }
.ark-value { color:#f7f9ff; font-size:21px; font-weight:900; margin-top:7px; overflow-wrap:anywhere; font-variant-numeric:tabular-nums; }
.ark-note { color:#9aacc7; font-size:10px; margin-top:5px; line-height:1.5; }
.ark-section { color:#f6f8ff; font-size:17px; font-weight:900; margin:23px 0 9px; letter-spacing:.2px; padding-left:10px; border-left:3px solid #d8b86a; }
.ark-score-wrap { background:linear-gradient(145deg,#1a2b44,#101a2a); border:1px solid #3b5271; border-radius:17px; padding:15px; margin:11px 0; box-shadow:0 9px 23px #0003; }
.ark-score-row { display:flex; justify-content:space-between; gap:10px; color:#bdcbe0; font-size:12px; margin:7px 0; }
.ark-score-row strong { color:#fff; font-weight:850; }
.ark-track { height:9px; border-radius:99px; background:#2b3c55; overflow:hidden; margin-bottom:12px; box-shadow:inset 0 1px 3px #0008; }
.ark-fill-bull { height:100%; background:linear-gradient(90deg,#15966d,#65e9b0); border-radius:99px; box-shadow:0 0 12px #45d99b66; }
.ark-fill-bear { height:100%; background:linear-gradient(90deg,#b83c58,#ff8997); border-radius:99px; box-shadow:0 0 12px #ff6c8066; }
[data-testid="stPlotlyChart"] { background:linear-gradient(145deg,#111e30,#0b1422); border:1px solid #344a68; border-radius:18px; padding:5px; box-shadow:0 12px 28px #0004; overflow:hidden; }
[data-testid="stDataFrame"],[data-testid="stTable"] { border:1px solid #344a68; border-radius:14px; overflow:hidden; }
hr { border-color:#344762 !important; opacity:.8; }
@media (min-width:700px) { .ark-grid { grid-template-columns:repeat(4,minmax(0,1fr)); } }
@media (max-width:480px) {
 .block-container { padding-left:.55rem !important; padding-right:.55rem !important; }
 .ark-hero { padding:16px 14px; border-radius:18px; }
 .ark-title { font-size:23px; }
 .ark-value { font-size:18px; }
 .ark-card { padding:11px !important; border-radius:14px !important; }
 .ark-section { font-size:15px; margin-top:19px; }
 [data-testid="stMetric"] { padding:10px !important; border-radius:14px !important; }
}
iframe { width:100% !important; touch-action:pan-y !important; border-radius:15px; }
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

# Load the owner's profile portrait from this repository.
try:
    profile_b64 = requests.get(
        "https://raw.githubusercontent.com/abdulrouf786/ict-baba/main/profile_photo.b64",
        timeout=12,
    ).text.strip()
    profile_photo_html = (
        f'<img src="data:image/jpeg;base64,{profile_b64}" '
        'class="ark-avatar" alt="Abdul Rauf King profile photo">'
    )
except Exception:
    profile_photo_html = ""

st.markdown(f"""
<div class="ark-hero" style="margin-top:4px">
  <div class="ark-profile-row">
    {profile_photo_html}
    <div class="ark-profile-copy">
      <div class="ark-kicker">✦ PREMIUM MARKET TERMINAL · FREE ANALYSIS</div>
      <div class="ark-title">👑 ABDUL RAUF KING</div>
      <div class="ark-sub">{ASSET_LABEL.upper()} · {FEED_SYMBOL} · ICT SMART MONEY + MULTI-INDICATOR SUITE</div>
    </div>
  </div>
  <div style="display:flex;flex-wrap:wrap;gap:7px;margin-top:14px">
    <span class="ark-pill bull">● LIVE MARKET</span>
    <span class="ark-pill neutral">✦ ICT ANALYSIS</span>
    <span class="ark-pill">⚡ STRONG SIGNAL FILTER</span>
  </div>
</div>
""", unsafe_allow_html=True)

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
if FEED_SYMBOL == "XAUUSD":
    st.warning(
        "Gold ICT markings public XAUUSD feed se calculate hoti hain. "
        "Yeh Vantage broker candles se mukhtalif ho sakti hain."
    )
elif FEED_SYMBOL in ("BTCUSDT", "ETHUSDT"):
    st.info(
        "Crypto ICT candles Binance public SPOT data se calculate hoti hain. "
        "TradingView chart aur spot feed mein price ka halka farq ho sakta hai."
    )
else:
    st.info(
        "Forex ICT candles Yahoo Finance public reference data se calculate hoti hain; "
        "yeh broker feed se mukhtalif ho sakti hain."
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
            "volume": quote.get("volume", [float("nan")] * len(timestamps)),
        })
        if interval == "4h":
            frame = frame.set_index("openTime").resample("4h").agg({
                "open": "first", "high": "max", "low": "min", "close": "last"
            }).dropna().reset_index()
    else:
        # Binance public spot klines for BTCUSDT and ETHUSDT; no API key required.
        # Binance's official market-data mirror is more accessible where
        # api.binance.com is region/WAF blocked. Fall back to the primary host.
        params = {"symbol": feed_symbol, "interval": interval, "limit": 500}
        response = None
        last_error = None
        for base_url in (
            "https://data-api.binance.vision/api/v3/klines",
            "https://api.binance.com/api/v3/klines",
        ):
            try:
                response = requests.get(
                    base_url, params=params, timeout=(5, 15), headers=headers
                )
                response.raise_for_status()
                break
            except requests.RequestException as exc:
                last_error = exc
        if response is None or not response.ok:
            raise RuntimeError(
                f"Binance public candle feed unavailable ({type(last_error).__name__})"
            )
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
    ict_df["+DI 14"] = plus_di
    ict_df["-DI 14"] = minus_di
    ict_df["ADX 14"] = dx.ewm(alpha=1/14, adjust=False).mean()

    # Additional confirmations: session VWAP, Stochastic RSI and volume.
    if "volume" not in ict_df.columns:
        ict_df["volume"] = float("nan")
    ict_df["volume"] = pd.to_numeric(ict_df["volume"], errors="coerce")
    typical_price = (high + low + close) / 3
    session_key = ict_df["openTime"].dt.date
    cum_pv = (typical_price * ict_df["volume"].fillna(0)).groupby(session_key).cumsum()
    cum_vol = ict_df["volume"].fillna(0).groupby(session_key).cumsum()
    ict_df["VWAP"] = (cum_pv / cum_vol.replace(0, float("nan")))

    rsi_min = ict_df["RSI 14"].rolling(14).min()
    rsi_max = ict_df["RSI 14"].rolling(14).max()
    stoch_raw = 100 * (ict_df["RSI 14"] - rsi_min) / (rsi_max - rsi_min).replace(0, float("nan"))
    ict_df["Stoch RSI K"] = stoch_raw.rolling(3).mean()
    ict_df["Stoch RSI D"] = ict_df["Stoch RSI K"].rolling(3).mean()
    ict_df["Volume SMA 20"] = ict_df["volume"].rolling(20).mean()

    last = ict_df.iloc[-1]
    price_col1, price_col2, price_col3 = st.columns(3)
    price_col1.metric("Selected market price", f"{last['close']:,.2f}")
    price_col2.metric("Feed timeframe", selected)
    price_col3.metric("Bars loaded", f"{len(ict_df)}")

    # Mobile-friendly candle view: fewer bars and only the two key EMAs.
    # The full dataframe remains available for indicator and signal calculations.
    chart_df = ict_df.tail(120).copy()
    fig = go.Figure(data=[go.Candlestick(
        x=chart_df["openTime"],
        open=chart_df["open"],
        high=chart_df["high"],
        low=chart_df["low"],
        close=chart_df["close"],
        name=FEED_SYMBOL,
        increasing_line_color="#26a69a",
        decreasing_line_color="#ef5350",
        increasing_fillcolor="#26a69a",
        decreasing_fillcolor="#ef5350",
        whiskerwidth=0.7,
    )])
    fig.add_trace(go.Scatter(
        x=chart_df["openTime"], y=chart_df["EMA 20"],
        mode="lines", name="EMA 20",
        line=dict(color="#f5c542", width=1.8),
    ))
    fig.add_trace(go.Scatter(
        x=chart_df["openTime"], y=chart_df["EMA 50"],
        mode="lines", name="EMA 50",
        line=dict(color="#42a5f5", width=1.8),
    ))
    add_ict_marks(fig, chart_df)
    fig.update_layout(
        height=480,
        template="plotly_dark",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        margin=dict(l=8, r=8, t=30, b=20),
        xaxis_rangeslider_visible=False,
        xaxis_title="Time (UTC)",
        yaxis_title=f"{ASSET_LABEL} price",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=10)),
        xaxis=dict(showgrid=False, rangeslider=dict(visible=False), tickfont=dict(size=10)),
        yaxis=dict(fixedrange=False, tickfont=dict(size=10), automargin=True),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False, "scrollZoom": True})

    # Show each indicator's current directional reading directly below the chart.
    indicator_rows = [
        ("EMA 20 / 50", "BUY" if bool(last["close"] > last["EMA 20"] > last["EMA 50"]) else ("SELL" if bool(last["close"] < last["EMA 20"] < last["EMA 50"]) else "NEUTRAL")),
        ("RSI 14", "BUY" if pd.notna(last["RSI 14"]) and last["RSI 14"] > 50 else ("SELL" if pd.notna(last["RSI 14"]) and last["RSI 14"] < 50 else "NEUTRAL")),
        ("MACD", "BUY" if pd.notna(last["MACD"]) and pd.notna(last["MACD Signal"]) and last["MACD"] > last["MACD Signal"] else ("SELL" if pd.notna(last["MACD"]) and pd.notna(last["MACD Signal"]) and last["MACD"] < last["MACD Signal"] else "NEUTRAL")),
        ("Bollinger", "BUY" if pd.notna(last["BB Middle"]) and last["close"] > last["BB Middle"] else ("SELL" if pd.notna(last["BB Middle"]) and last["close"] < last["BB Middle"] else "NEUTRAL")),
        ("Supertrend", "BUY" if last["Supertrend Direction"] == "BULLISH" else ("SELL" if last["Supertrend Direction"] == "BEARISH" else "NEUTRAL")),
        ("VWAP", "BUY" if pd.notna(last["VWAP"]) and last["close"] > last["VWAP"] else ("SELL" if pd.notna(last["VWAP"]) and last["close"] < last["VWAP"] else "NEUTRAL")),
        ("Stoch RSI", "BUY" if pd.notna(last["Stoch RSI K"]) and pd.notna(last["Stoch RSI D"]) and last["Stoch RSI K"] > last["Stoch RSI D"] else ("SELL" if pd.notna(last["Stoch RSI K"]) and pd.notna(last["Stoch RSI D"]) and last["Stoch RSI K"] < last["Stoch RSI D"] else "NEUTRAL")),
        ("DMI +DI / -DI", "BUY" if pd.notna(last["+DI 14"]) and pd.notna(last["-DI 14"]) and last["+DI 14"] > last["-DI 14"] else ("SELL" if pd.notna(last["+DI 14"]) and pd.notna(last["-DI 14"]) and last["-DI 14"] > last["+DI 14"] else "NEUTRAL")),
        ("Volume", "CONFIRM" if pd.notna(last["volume"]) and pd.notna(last["Volume SMA 20"]) and last["volume"] > last["Volume SMA 20"] else "LOW / N.A."),
    ]
    indicator_html = "".join(
        f'<div style="display:flex;justify-content:space-between;gap:12px;padding:9px 11px;border-bottom:1px solid #29384d">'
        f'<span style="color:#d5deeb;font-weight:650">{name}</span>'
        f'<strong style="color:{"#35d6a0" if state == "BUY" or state == "CONFIRM" else ("#ff7185" if state == "SELL" else "#aab6c8")};white-space:nowrap">{state}</strong></div>'
        for name, state in indicator_rows
    )
    buy_count = sum(state == "BUY" for _, state in indicator_rows)
    sell_count = sum(state == "SELL" for _, state in indicator_rows)
    st.markdown('<div class="ark-section">🧭 Har indicator ka BUY / SELL</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="ark-score-wrap"><div style="display:flex;justify-content:space-between;gap:8px;padding:4px 10px 10px;color:#dce6f5">'
        f'<strong style="color:#35d6a0">BUY: {buy_count}</strong><strong style="color:#ff7185">SELL: {sell_count}</strong></div>{indicator_html}'
        f'<div class="ark-note" style="padding:10px">Har indicator ka apna direction hai; final trade signal ke liye neeche ICT confirmation aur risk checks bhi zaroori hain.</div></div>',
        unsafe_allow_html=True,
    )
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
    vwap_bull = bool(pd.notna(last["VWAP"]) and last["close"] > last["VWAP"])
    vwap_bear = bool(pd.notna(last["VWAP"]) and last["close"] < last["VWAP"])
    stoch_bull = bool(pd.notna(last["Stoch RSI K"]) and pd.notna(last["Stoch RSI D"]) and last["Stoch RSI K"] > last["Stoch RSI D"] and last["Stoch RSI K"] > 50)
    stoch_bear = bool(pd.notna(last["Stoch RSI K"]) and pd.notna(last["Stoch RSI D"]) and last["Stoch RSI K"] < last["Stoch RSI D"] and last["Stoch RSI K"] < 50)
    dmi_bull = bool(pd.notna(last["+DI 14"]) and last["+DI 14"] > last["-DI 14"])
    dmi_bear = bool(pd.notna(last["+DI 14"]) and last["-DI 14"] > last["+DI 14"])
    volume_confirm = bool(pd.notna(last["volume"]) and pd.notna(last["Volume SMA 20"]) and last["volume"] > last["Volume SMA 20"])
    bull_total = sum([ema_bull, rsi_bull, macd_bull, bb_bull, supertrend_bull, vwap_bull, stoch_bull, dmi_bull, volume_confirm])
    bear_total = sum([ema_bear, rsi_bear, macd_bear, bb_bear, supertrend_bear, vwap_bear, stoch_bear, dmi_bear, volume_confirm])

    if bull_total >= 5 and bull_total > bear_total:
        bias, pill_class, bias_detail = "BULLISH", "bull", "Bullish conditions are stronger; wait for ICT entry confirmation."
    elif bear_total >= 5 and bear_total > bull_total:
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
      <div class="ark-card"><div class="ark-label">VWAP</div><div class="ark-value">{last["VWAP"]:,.2f}</div><div class="ark-note">Session fair value</div></div>
      <div class="ark-card"><div class="ark-label">STOCH RSI K/D</div><div class="ark-value">{last["Stoch RSI K"]:.1f} / {last["Stoch RSI D"]:.1f}</div><div class="ark-note">Momentum trigger</div></div>
      <div class="ark-card"><div class="ark-label">DMI +DI / -DI</div><div class="ark-value">{last["+DI 14"]:.1f} / {last["-DI 14"]:.1f}</div><div class="ark-note">Directional trend</div></div>
      <div class="ark-card"><div class="ark-label">VOLUME CONFIRM</div><div class="ark-value">{"YES" if volume_confirm else "NO / N.A."}</div><div class="ark-note">Current vs 20-bar average</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="ark-section">🧠 Signal confluence</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="ark-score-wrap">
      <div class="ark-score-row"><span>Bullish confirmation</span><strong>{bull_total}/9</strong></div>
      <div class="ark-track"><div class="ark-fill-bull" style="width:{bull_total / 9 * 100}%"></div></div>
      <div class="ark-score-row"><span>Bearish confirmation</span><strong>{bear_total}/9</strong></div>
      <div class="ark-track"><div class="ark-fill-bear" style="width:{bear_total / 9 * 100}%"></div></div>
      <div class="ark-note">EMA · RSI · MACD · Bollinger · Supertrend · VWAP · Stoch RSI · DMI · Volume</div>
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

    # ICT setup monitor: these are educational pattern checks, not guaranteed entries.
    ict_setups = []
    if len(closed) >= 25:
        cur = closed.iloc[-1]
        prev = closed.iloc[-2]
        recent = closed.tail(20)
        direction_up = float(cur["close"]) > float(recent["high"].iloc[:-1].max())
        direction_down = float(cur["close"]) < float(recent["low"].iloc[:-1].min())
        bull_sweep = float(recent["low"].iloc[-1]) < float(recent["low"].iloc[:-1].min()) and float(cur["close"]) > float(recent["low"].iloc[:-1].min())
        bear_sweep = float(recent["high"].iloc[-1]) > float(recent["high"].iloc[:-1].max()) and float(cur["close"]) < float(recent["high"].iloc[:-1].max())
        bull_fvg = float(cur["low"]) > float(closed.iloc[-3]["high"])
        bear_fvg = float(cur["high"]) < float(closed.iloc[-3]["low"])
        # Order block: last opposite candle before a close beyond the recent range.
        bull_ob = direction_up and bool((closed.iloc[-8:-1]["close"] < closed.iloc[-8:-1]["open"]).any())
        bear_ob = direction_down and bool((closed.iloc[-8:-1]["close"] > closed.iloc[-8:-1]["open"]).any())
        # Rejection block proxy: wick sweeps a recent extreme and closes back inside.
        bull_rejection = bull_sweep and (min(float(cur["open"]), float(cur["close"])) - float(cur["low"])) > abs(float(cur["close"]-cur["open"]))
        bear_rejection = bear_sweep and (float(cur["high"]) - max(float(cur["open"]), float(cur["close"]))) > abs(float(cur["close"]-cur["open"]))
        # OTE zone from the recent 50-bar dealing range (62%-79% retracement).
        dealing = closed.tail(50)
        swing_hi, swing_lo = float(dealing["high"].max()), float(dealing["low"].min())
        dealing_range = max(swing_hi - swing_lo, 0.0)
        bull_ote = dealing_range > 0 and swing_hi - 0.79*dealing_range <= float(cur["close"]) <= swing_hi - 0.62*dealing_range
        bear_ote = dealing_range > 0 and swing_lo + 0.62*dealing_range <= float(cur["close"]) <= swing_lo + 0.79*dealing_range
        # Breaker / mitigation are simplified level-retest proxies; confirm with chart context.
        bull_breaker = bull_sweep and direction_up
        bear_breaker = bear_sweep and direction_down
        bull_mitigation = bull_ob and float(cur["low"]) <= float(closed.iloc[-2]["high"]) and float(cur["close"]) > float(cur["open"])
        bear_mitigation = bear_ob and float(cur["high"]) >= float(closed.iloc[-2]["low"]) and float(cur["close"]) < float(cur["open"])
        # Unicorn requires breaker context plus a same-direction FVG.
        bull_unicorn = bull_breaker and bull_fvg
        bear_unicorn = bear_breaker and bear_fvg
        # Additional ICT concepts: heuristic pattern checks, not guaranteed trade entries.
        candle_body = abs(float(cur["close"] - cur["open"]))
        avg_body = float((closed["close"] - closed["open"]).abs().tail(20).mean())
        atr_now = max(float(cur["ATR 14"]) if pd.notna(cur["ATR 14"]) else 0.0, 1e-12)
        bull_displacement = float(cur["close"]) > float(cur["open"]) and candle_body > 1.5 * max(avg_body, 1e-12) and float(cur["close"]) > float(prev["high"])
        bear_displacement = float(cur["close"]) < float(cur["open"]) and candle_body > 1.5 * max(avg_body, 1e-12) and float(cur["close"]) < float(prev["low"])
        equal_highs = abs(float(recent["high"].nlargest(2).iloc[0]) - float(recent["high"].nlargest(2).iloc[1])) <= 0.08 * atr_now
        equal_lows = abs(float(recent["low"].nsmallest(2).iloc[0]) - float(recent["low"].nsmallest(2).iloc[1])) <= 0.08 * atr_now
        bull_turtle, bear_turtle = bull_sweep, bear_sweep
        midpoint = (swing_hi + swing_lo) / 2
        bull_discount, bear_premium = float(cur["close"]) < midpoint, float(cur["close"]) > midpoint
        prior_range = closed.iloc[-12:-3]
        was_range_bound = (float(prior_range["high"].max()) - float(prior_range["low"].min())) < 2.5 * atr_now
        bull_amd = was_range_bound and bull_sweep and (bull_displacement or direction_up)
        bear_amd = was_range_bound and bear_sweep and (bear_displacement or direction_down)
        hour_utc = pd.Timestamp(cur["openTime"]).hour
        london_kz, newyork_kz = 7 <= hour_utc < 10, 12 <= hour_utc < 15
        ict_setups = [
            ("Liquidity sweep + MSS", "BUY" if bull_sweep and direction_up else ("SELL" if bear_sweep and direction_down else "WAIT")),
            ("Fair Value Gap (FVG)", "BUY" if bull_fvg else ("SELL" if bear_fvg else "WAIT")),
            ("Order Block (OB)", "BUY" if bull_ob else ("SELL" if bear_ob else "WAIT")),
            ("Breaker Block", "BUY" if bull_breaker else ("SELL" if bear_breaker else "WAIT")),
            ("Mitigation Block", "BUY" if bull_mitigation else ("SELL" if bear_mitigation else "WAIT")),
            ("Rejection Block", "BUY" if bull_rejection else ("SELL" if bear_rejection else "WAIT")),
            ("OTE 62%-79%", "BUY" if bull_ote else ("SELL" if bear_ote else "WAIT")),
            ("Unicorn (Breaker + FVG)", "BUY" if bull_unicorn else ("SELL" if bear_unicorn else "WAIT")),
            ("Turtle Soup", "BUY" if bull_turtle else ("SELL" if bear_turtle else "WAIT")),
            ("Displacement", "BUY" if bull_displacement else ("SELL" if bear_displacement else "WAIT")),
            ("Equal Highs / BSL pool", "SELL" if equal_highs else "WAIT"),
            ("Equal Lows / SSL pool", "BUY" if equal_lows else "WAIT"),
            ("Premium / Discount", "SELL" if bear_premium else ("BUY" if bull_discount else "WAIT")),
            ("AMD / Power of 3 proxy", "BUY" if bull_amd else ("SELL" if bear_amd else "WAIT")),
            ("London Killzone (UTC approx.)", "ACTIVE" if london_kz else "INACTIVE"),
            ("New York Killzone (UTC approx.)", "ACTIVE" if newyork_kz else "INACTIVE"),
            ("SMT Divergence", "NEEDS CORRELATED DATA"),
            ("Judas Swing", "NEEDS SESSION CONFIRMATION"),
        ]
    else:
        ict_names = ["Liquidity sweep + MSS", "Fair Value Gap (FVG)", "Order Block (OB)", "Breaker Block", "Mitigation Block", "Rejection Block", "OTE 62%-79%", "Unicorn (Breaker + FVG)", "Turtle Soup", "Displacement", "Equal Highs / BSL pool", "Equal Lows / SSL pool", "Premium / Discount", "AMD / Power of 3 proxy", "London Killzone (UTC approx.)", "New York Killzone (UTC approx.)", "SMT Divergence", "Judas Swing"]
        ict_setups = [(name, "WAIT") for name in ict_names]

    st.markdown('<div class="ark-section">🏹 ICT entry models</div>', unsafe_allow_html=True)
    ict_rows = "".join(
        f'<div style="display:flex;justify-content:space-between;gap:10px;padding:9px 11px;border-bottom:1px solid #29384d">'
        f'<span style="color:#d5deeb;font-weight:650">{name}</span>'
        f'<strong style="color:{"#35d6a0" if side == "BUY" else ("#ff7185" if side == "SELL" else "#aab6c8")};white-space:nowrap">{side}</strong></div>'
        for name, side in ict_setups
    )
    st.markdown(
        f'<div class="ark-score-wrap">{ict_rows}<div class="ark-note" style="padding:10px">BUY/SELL ka matlab heuristic pattern detect hua hai, automatic trade call nahi. Killzone UTC approximation hai aur DST se shift ho sakta hai. SMT ko correlated market data aur Judas Swing ko session-specific confirmation chahiye.</div></div>',
        unsafe_allow_html=True,
    )
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
                    if mss_confirmed and fvg_confirmed and bull_total >= 7 and float(closed.iloc[-1]["ADX 14"]) >= 25:
                        signal_side = "BUY"
                        signal_reasons = ["Sell-side liquidity sweep", "Bullish MSS", "Bullish FVG", f"{bull_total}/9 bullish indicator checks · STRONG"]
                else:
                    mss_confirmed = bool((later["close"] < structure_level).any())
                    fvg_confirmed = bool(any(
                        float(closed.iloc[i]["high"]) < float(closed.iloc[i - 2]["low"])
                        for i in range(max(sj + 1, len(closed) - 8), len(closed))
                        if i >= 2
                    ))
                    if mss_confirmed and fvg_confirmed and bear_total >= 7 and float(closed.iloc[-1]["ADX 14"]) >= 25:
                        signal_side = "SELL"
                        signal_reasons = ["Buy-side liquidity sweep", "Bearish MSS", "Bearish FVG", f"{bear_total}/9 bearish indicator checks · STRONG"]

    signal_entry = float(closed.iloc[-1]["close"])
    signal_atr = float(closed.iloc[-1]["ATR 14"]) if pd.notna(closed.iloc[-1]["ATR 14"]) else 0.0
    signal_sl = signal_tp1 = signal_tp2 = signal_tp3 = None
    signal_rr = "—"
    if signal_side == "BUY" and signal_atr > 0:
        signal_sl = float(closed["low"].tail(5).min()) - 0.10 * signal_atr
        risk = signal_entry - signal_sl
        if risk > 0:
            signal_tp1, signal_tp2, signal_tp3 = signal_entry + 5*risk, None, None
            signal_rr = "1:5"
        else:
            signal_side = "WAIT"
    elif signal_side == "SELL" and signal_atr > 0:
        signal_sl = float(closed["high"].tail(5).max()) + 0.10 * signal_atr
        risk = signal_sl - signal_entry
        if risk > 0:
            signal_tp1, signal_tp2, signal_tp3 = signal_entry - 5*risk, None, None
            signal_rr = "1:5"
        else:
            signal_side = "WAIT"
    else:
        signal_side = "WAIT"


    # WhatsApp alert controls. Recipient must be the verified/opted-in destination number.
    st.markdown('<div class="ark-section">📲 WhatsApp ICT alerts</div>', unsafe_allow_html=True)
    wa_recipient = st.text_input(
        "Your WhatsApp number (international format, e.g. 923001234567)",
        value=st.session_state.get("wa_recipient", ""),
        key="wa_recipient_input",
        help="Country code + number, digits only. Do not include +, spaces or dashes.",
    ).strip().replace("+", "").replace(" ", "").replace("-", "")
    st.session_state["wa_recipient"] = wa_recipient
    wa_col1, wa_col2 = st.columns(2)
    with wa_col1:
        if st.button("Send test WhatsApp message", use_container_width=True):
            if not wa_recipient.isdigit() or len(wa_recipient) < 8:
                st.error("Pehle valid WhatsApp number country code ke saath enter karein.")
            else:
                try:
                    send_whatsapp_message(
                        wa_recipient,
                        "ICT Baba: WhatsApp connection test successful. Alerts ke liye internet on rakhein.",
                    )
                    st.success("Test message WhatsApp API ko send ho gaya. Apna WhatsApp check karein.")
                except Exception as exc:
                    st.error(f"WhatsApp test failed: {exc}")
    with wa_col2:
        st.caption("Confirmed ICT BUY/SELL setup par alert bhejne ki koshish app ke refresh par hogi. Streamlit app background mein hamesha run nahi karti.")

    # Send each confirmed closed-candle setup once per browser session.
    if signal_side in ("BUY", "SELL") and wa_recipient and wa_recipient.isdigit():
        candle_key = str(closed.iloc[-1]["openTime"])
        alert_key = f"{FEED_SYMBOL}|{api_interval}|{signal_side}|{candle_key}"
        sent_alerts = st.session_state.setdefault("wa_sent_alerts", [])
        if alert_key not in sent_alerts:
            alert_text = (
                f"ICT BABA {signal_side} CONFIRMED\\n"
                f"Pair: {FEED_SYMBOL}\\nTimeframe: {api_interval}\\n"
                f"Setup: Liquidity Sweep + MSS + FVG\\n"
                f"Entry: {signal_entry:.5f}\\nSL: {signal_sl:.5f}\\n"
                f"TP: {signal_tp1:.5f}\\nRR: {signal_rr}\\n"
                f"Reasons: {', '.join(signal_reasons)}\\n"
                "Educational signal only; verify spread and broker prices."
            )
            try:
                send_whatsapp_message(wa_recipient, alert_text)
                sent_alerts.append(alert_key)
                st.session_state["wa_sent_alerts"] = sent_alerts[-100:]
                st.success("Confirmed ICT signal WhatsApp par bhej diya.")
            except Exception as exc:
                st.warning(f"Confirmed signal mila, lekin WhatsApp alert send nahi hua: {exc}")

    st.markdown('<div class="ark-section">🎯 Full trading signal</div>', unsafe_allow_html=True)
    if signal_side == "WAIT":
        st.info("WAIT — abhi confirmed ICT entry nahi mili. Neeche reference levels sirf planning ke liye hain; inhein live trade signal na samjhein.")
        # Show the complete SL/TP panel on every refresh. When ICT is not
        # confirmed, derive clearly-labelled provisional levels from ATR and
        # the indicator bias; neutral conditions keep risk levels blank.
        plan_side = "BUY" if bias == "BULLISH" else ("SELL" if bias == "BEARISH" else "WAIT")
        plan_entry = float(closed.iloc[-1]["close"])
        plan_sl = plan_tp1 = plan_tp2 = plan_tp3 = None
        plan_rr = "—"
        if plan_side == "BUY" and signal_atr > 0:
            plan_sl = plan_entry - 0.5 * signal_atr
            plan_risk = plan_entry - plan_sl
            plan_tp1, plan_tp2, plan_tp3 = plan_entry + 5*plan_risk, None, None
            plan_rr = "1:5"
        elif plan_side == "SELL" and signal_atr > 0:
            plan_sl = plan_entry + 0.5 * signal_atr
            plan_risk = plan_sl - plan_entry
            plan_tp1, plan_tp2, plan_tp3 = plan_entry - 5*plan_risk, None, None
            plan_rr = "1:5"
        def fmt_plan(value):
            return f"{value:,.2f}" if value is not None else "WAIT"
        st.markdown(f"""
        <div class="ark-hero">
          <div class="ark-kicker">{FEED_SYMBOL} · {selected} · INDICATIVE LEVELS</div>
          <div class="ark-title">{plan_side} PLAN — NOT AN ICT ENTRY</div>
          <div class="ark-sub">Levels use the last closed candle and 0.5× ATR (tight SL). Wait for sweep + MSS + FVG confirmation.</div>
        </div>
        <div class="ark-grid">
          <div class="ark-card"><div class="ark-label">ENTRY REFERENCE</div><div class="ark-value">{fmt_plan(plan_entry)}</div><div class="ark-note">Last closed candle; not a live fill price</div></div>
          <div class="ark-card"><div class="ark-label">STOP LOSS</div><div class="ark-value">{fmt_plan(plan_sl)}</div><div class="ark-note">Indicative 0.5× ATR (tight SL)</div></div>
          <div class="ark-card"><div class="ark-label">TAKE PROFIT</div><div class="ark-value">{fmt_plan(plan_tp1)}</div><div class="ark-note">5R target · risk/reward 1:5</div></div>
          <div class="ark-card"><div class="ark-label">RISK / REWARD</div><div class="ark-value">{plan_rr}</div><div class="ark-note">Indicative, before spread/slippage</div></div>
        </div>
        """, unsafe_allow_html=True)
        st.caption("Signal logic: recent 20-bar liquidity level, confirmed candle close, recent FVG aur kam az kam 7/9 indicator checks (EMA, RSI, MACD, Bollinger, Supertrend, VWAP, Stoch RSI, DMI, volume) aur ADX >= 25. Latest open candle ignore ki gayi hai.")
    else:
        st.markdown(f"""
        <div class="ark-hero">
          <div class="ark-kicker">{FEED_SYMBOL} · {selected} · CLOSED-CANDLE SETUP</div>
          <div class="ark-title">STRONG {signal_side} SIGNAL</div>
          <div class="ark-sub">Strong setup: ICT sweep + MSS + FVG, at least 7/9 indicator checks and ADX >= 25. Closed candles only.</div>
        </div>
        """, unsafe_allow_html=True)
        def fmt_level(value):
            return f"{value:,.2f}" if value is not None else "—"
        st.markdown(f"""
        <div class="ark-grid">
          <div class="ark-card"><div class="ark-label">ENTRY reference</div><div class="ark-value">{fmt_level(signal_entry)}</div><div class="ark-note">Last closed candle; not a live fill price</div></div>
          <div class="ark-card"><div class="ark-label">STOP LOSS</div><div class="ark-value">{fmt_level(signal_sl)}</div><div class="ark-note">Beyond recent 8-bar swing + ATR buffer</div></div>
          <div class="ark-card"><div class="ark-label">TAKE PROFIT</div><div class="ark-value">{fmt_level(signal_tp1)}</div><div class="ark-note">5R target · risk/reward 1:5</div></div>
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

