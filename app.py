import json
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
iframe {
    width: 100% !important;
    touch-action: pan-y !important;
}
body { overscroll-behavior-y: auto !important; }
</style>
""", unsafe_allow_html=True)

SYMBOL = "VANTAGE:XAUUSD"

st.title("👑 ABDUL RAUF KING")
st.caption("VANTAGE GOLD — XAUUSD")

# TradingView quote strip for the same Vantage Gold symbol.
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
    "1 Minute": "1",
    "5 Minutes": "5",
    "15 Minutes": "15",
    "1 Hour": "60",
    "4 Hours": "240",
}
selected = st.selectbox("Gold timeframe", list(timeframes.keys()), index=2)

CHART_HEIGHT = 650
widget_config = {
    "autosize": False,
    "height": CHART_HEIGHT,
    "width": "100%",
    "symbol": SYMBOL,
    "interval": timeframes[selected],
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

st.caption(
    "Original TradingView VANTAGE:XAUUSD candles. "
    "Custom ICT marks (Liquidity Sweep, MSS, FVG, BUY/SELL) are not overlaid yet: "
    "TradingView's embedded chart does not allow this app to inject custom Pine indicators. "
    "A compatible OHLC data connection or TradingView charting integration is required."
)
