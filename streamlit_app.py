
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="XAUUSD ICT Learning Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("🥇 XAUUSD Gold ICT Dashboard")
st.caption("Learning dashboard — not financial advice.")

timeframe = st.selectbox(
    "Chart timeframe",
    ["1 minute", "5 minutes", "15 minutes"]
)

intervals = {
    "1 minute": "1",
    "5 minutes": "5",
    "15 minutes": "15"
}
interval = intervals[timeframe]

st.subheader("Live market chart")
st.info(
    "Chart TradingView se load hota hai. "
    "Price aur availability broker/data source par depend karte hain."
)

chart_html = f"""
<div class="tradingview-widget-container" style="height:500px;width:100%">
  <div id="tradingview_chart" style="height:480px;width:100%"></div>
  <script type="text/javascript"
    src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
    new TradingView.widget({{
      "autosize": true,
      "symbol": "OANDA:XAUUSD",
      "interval": "{interval}",
      "timezone": "Etc/UTC",
      "theme": "dark",
      "style": "1",
      "locale": "en",
      "enable_publishing": false,
      "allow_symbol_change": true,
      "hide_side_toolbar": false,
      "container_id": "tradingview_chart"
    }});
  </script>
</div>
"""

components.html(chart_html, height=510, scrolling=False)

st.subheader("ICT learning notes")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Liquidity sweep")
    st.write(
        "Price kisi previous high ya low ke paar ja kar "
        "wapas aaye to candles ko dhyan se observe karein."
    )

with col2:
    st.markdown("### Fair Value Gap (FVG)")
    st.write(
        "Three-candle pattern mein possible imbalance ko "
        "chart par manually identify karna seekhein."
    )

st.warning(
    "Yeh chart khud verified BUY/SELL signal calculate nahi karta. "
    "TradingView chart embed hona Python ko candle data nahi deta."
)
