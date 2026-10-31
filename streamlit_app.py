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
    zoom: 0.92;
    padding-top: 0.15rem !important;
    padding-left: 0.15rem !important;
    padding-right: 0.15rem !important;
    padding-bottom: 0 !important;
}
h1 { font-size: 1.45rem !important; margin-bottom: 0.35rem !important; }
[data-testid='stSelectbox'] { margin-bottom: 0.25rem !important; }
iframe { width: 100% !important; }
</style>
""", unsafe_allow_html=True)

SYMBOL = "VANTAGE:XAUUSD"
st.markdown(
    "<div style=\"font-size:22px;font-weight:800;line-height:1.2;margin:2px 0 10px 0;\">👑 ABDUL RAUF KING</div>"
    "<div style=\"font-size:11px;opacity:0.8;margin-top:-7px;margin-bottom:10px;\">VANTAGE GOLD — XAUUSD</div>",
    unsafe_allow_html=True,
)

timeframes = {
    "1 Minute": "1",
    "5 Minutes": "5",
    "15 Minutes": "15",
    "1 Hour": "60",
    "4 Hours": "240",
}
selected = st.selectbox("Gold timeframe", list(timeframes.keys()), index=2)

# Only the chart height is increased; the rest of the app layout is unchanged.
CHART_HEIGHT = 1200

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

components.html(
    widget_html,
    height=CHART_HEIGHT + 20,
    scrolling=False,
)

st.info(
    "TradingView VANTAGE:XAUUSD chart. ICT Sweep, MSS, FVG aur BUY/SELL "
    "signals tabhi enable honge jab isi Vantage feed ka verified OHLC data connection milega."
)
