import json
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="ICT Baba - Vantage Gold",
    page_icon="🥇",
    layout="wide",
)

SYMBOL = "VANTAGE:XAUUSD"

st.title("🥇 ICT BABA — VANTAGE GOLD")
st.caption("TradingView market chart | VANTAGE:XAUUSD")

timeframes = {
    "1 Minute": "1",
    "5 Minutes": "5",
    "15 Minutes": "15",
    "1 Hour": "60",
    "4 Hours": "240",
}

selected = st.selectbox("Gold timeframe", list(timeframes.keys()), index=2)

widget_config = {
    "autosize": True,
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
<div class="tradingview-widget-container" style="height:940px;width:100%">
  <div class="tradingview-widget-container__widget" style="height:920px;width:100%"></div>
  <script type="text/javascript"
    src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js"
    async>
    {json.dumps(widget_config)}
  </script>
</div>
"""

components.html(widget_html, height=960, scrolling=False)

st.info(
    "Chart TradingView ke VANTAGE:XAUUSD feed se aa raha hai. "
    "Liquidity Sweep, MSS, FVG aur BUY/SELL signals filhaal band hain; "
    "unhein activate karne ke liye isi Vantage feed ka verified OHLC data connection chahiye."
)

st.caption(
    "ICT Baba | TradingView chart is embedded for analysis. "
    "TradingView data availability and broker permissions apply."
)
