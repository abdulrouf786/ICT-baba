import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import ccxt
from datetime import datetime, timezone

st.set_page_config(page_title="ICT Baba Live", page_icon="📈", layout="wide")
st.title("📈 ICT BABA — LIVE TRADING")
st.caption("Real exchange candles • Live price • ICT-style analysis")

PAIRS = {"BTC/USDT": ["BTC/USDT", "BTC/USD"], "ETH/USDT": ["ETH/USDT", "ETH/USD"], "SOL/USDT": ["SOL/USDT", "SOL/USD"]}

@st.cache_resource
def exchanges():
    clients=[]
    for name, cls in [("Binance", ccxt.binance), ("OKX", ccxt.okx), ("Kraken", ccxt.kraken), ("Coinbase", ccxt.coinbase)]:
        try: clients.append((name, cls({"enableRateLimit": True, "timeout": 12000, "options": {"defaultType":"spot"}})))
        except Exception: pass
    return clients

EXCHANGES=exchanges()
with st.sidebar:
    market=st.selectbox("Market", list(PAIRS), index=0)
    tf=st.selectbox("Timeframe", ["1m","5m","15m","1h","4h"], index=1)
    limit=st.selectbox("Candles", [50,100,150,200], index=1)
    show_fvg=st.checkbox("Show FVG", True)
    show_liq=st.checkbox("Show liquidity levels", True)
    show_mss=st.checkbox("Show possible MSS / sweeps", True)

def load_data():
    errors=[]
    for name, ex in EXCHANGES:
        for pair in PAIRS[market]:
            try:
                markets=ex.load_markets()
                if pair not in markets: continue
                raw=ex.fetch_ohlcv(pair, timeframe=tf, limit=limit)
                if not raw: continue
                df=pd.DataFrame(raw, columns=["Time","Open","High","Low","Close","Volume"])
                df["Time"]=pd.to_datetime(df["Time"], unit="ms", utc=True)
                ticker=ex.fetch_ticker(pair)
                price=ticker.get("last") or float(df.Close.iloc[-1])
                return df, float(price), name, pair
            except Exception as e:
                errors.append(f"{name}/{pair}: {type(e).__name__}: {str(e)[:100]}")
    raise RuntimeError("All public exchanges failed. " + " | ".join(errors[-4:]))

def get_markers(df):
    out=[]
    for i in range(10,len(df)):
        row=df.iloc[i]; prior=df.iloc[i-10:i]
        hi=float(prior.High.max()); lo=float(prior.Low.min())
        if row.High>hi and row.Close<hi: out.append((i,"Possible sweep high","down"))
        elif row.Low<lo and row.Close>lo: out.append((i,"Possible sweep low","up"))
        if i>=5:
            p=df.iloc[i-5:i]; rh=float(p.High.max()); rl=float(p.Low.min())
            if row.Close>rh and df.Close.iloc[i-1]<=rh: out.append((i,"Possible bullish MSS","up"))
            elif row.Close<rl and df.Close.iloc[i-1]>=rl: out.append((i,"Possible bearish MSS","down"))
    return out

@st.fragment(run_every="10s")
def chart():
    try:
        df, price, source, pair=load_data()
        prev=float(df.Close.iloc[-2]) if len(df)>1 else price
        a,b,c,d=st.columns(4)
        a.metric(f"{market} LIVE PRICE", f"{price:,.6g}", f"{price-prev:+.6g} ({((price-prev)/prev*100 if prev else 0):+.2f}%)")
        b.metric("Latest close", f"{float(df.Close.iloc[-1]):,.6g}")
        c.metric("Latest volume", f"{float(df.Volume.iloc[-1]):,.4g}")
        d.metric("Data source", source)
        if pair.endswith("/USD") and market.endswith("/USDT"):
            st.info(f"Fallback source uses {pair} (USD quote), not USDT.")
        st.caption("Updated UTC: "+datetime.now(timezone.utc).strftime("%H:%M:%S")+" • Auto-refresh target 10s; delays may occur.")
        fig=go.Figure(go.Candlestick(x=df.Time,open=df.Open,high=df.High,low=df.Low,close=df.Close,name="Real OHLC candles",increasing_line_color="#16a34a",decreasing_line_color="#dc2626"))
        if show_liq and len(df)>12:
            r=df.tail(30).iloc[:-1]
            fig.add_hline(y=float(r.High.max()),line_dash="dot",line_color="orange",annotation_text="Liquidity high")
            fig.add_hline(y=float(r.Low.min()),line_dash="dot",line_color="deepskyblue",annotation_text="Liquidity low")
        if show_fvg:
            for i in range(max(2,len(df)-40),len(df)):
                fh,fl=float(df.High.iloc[i-2]),float(df.Low.iloc[i-2]); th,tl=float(df.High.iloc[i]),float(df.Low.iloc[i])
                if tl>fh: fig.add_shape(type="rect",x0=df.Time.iloc[i-2],x1=df.Time.iloc[i],y0=fh,y1=tl,fillcolor="rgba(22,163,74,.16)",line_width=0,layer="below")
                elif th<fl: fig.add_shape(type="rect",x0=df.Time.iloc[i-2],x1=df.Time.iloc[i],y0=th,y1=fl,fillcolor="rgba(220,38,38,.16)",line_width=0,layer="below")
        markers=get_markers(df) if show_mss else []
        for i,label,direction in markers[-15:]:
            up=direction=="up"
            fig.add_trace(go.Scatter(x=[df.Time.iloc[i]],y=[float(df.Low.iloc[i]) if up else float(df.High.iloc[i])],mode="markers",marker=dict(symbol="triangle-up" if up else "triangle-down",size=10,color="#16a34a" if up else "#dc2626"),name=label,showlegend=False,hovertemplate=label+"<br>%{x}<br>%{y}<extra></extra>"))
        fig.update_layout(title=f"{market} — {tf} ({source})",template="plotly_dark",height=600,xaxis_rangeslider_visible=False,hovermode="x unified",margin=dict(l=8,r=8,t=50,b=8))
        fig.update_yaxes(side="right")
        st.plotly_chart(fig,use_container_width=True,config={"scrollZoom":True,"displaylogo":False})
        with st.expander("Recent real candle data (OHLCV)"):
            st.dataframe(df.tail(15).sort_values("Time",ascending=False),use_container_width=True,hide_index=True)
        with st.expander("Possible ICT markers"):
            st.dataframe(pd.DataFrame([{"Time UTC":df.Time.iloc[i],"Marker":label,"Direction":direction,"Close":float(df.Close.iloc[i])} for i,label,direction in markers[-15:]]),use_container_width=True,hide_index=True) if markers else st.info("No possible markers found in these candles.")
    except Exception as e:
        st.error("Market data load nahi ho saka.")
        st.code(f"{type(e).__name__}: {e}")
        st.info("Binance, OKX, Kraken aur Coinbase try kiye gaye. Agar sab fail hon to Streamlit server/network par restriction ho sakti hai.")

chart()
st.warning("FVG, liquidity aur MSS markers simplified estimates hain, guaranteed signals nahi. App trade execute nahi karti.")
