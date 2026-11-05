import os, requests, math
import pandas as pd
import numpy as np
from datetime import datetime, timezone

API_KEY = os.getenv("TWELVEDATA_API_KEY") or os.getenv("TWELVE_DATA_API_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SYMBOL = os.getenv("BACKTEST_SYMBOL", "XAU/USD")
INTERVAL = os.getenv("BACKTEST_INTERVAL", "5min")
OUTPUTSIZE = int(os.getenv("BACKTEST_OUTPUTSIZE", "5000"))
RR = float(os.getenv("BACKTEST_RR", "2.0"))

def send_telegram(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram secrets missing; report printed to Actions log.")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=30)
    r.raise_for_status()

def get_data():
    if not API_KEY:
        raise RuntimeError("Missing Twelve Data API key. Add TWELVEDATA_API_KEY or TWELVE_DATA_API_KEY in GitHub Secrets.")
    url = "https://api.twelvedata.com/time_series"
    params = {"symbol": SYMBOL, "interval": INTERVAL, "outputsize": OUTPUTSIZE,
              "timezone": "UTC", "format": "JSON", "apikey": API_KEY}
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    js = r.json()
    if "values" not in js:
        raise RuntimeError(f"Twelve Data response: {js}")
    df = pd.DataFrame(js["values"])
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    for c in ["open","high","low","close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna().sort_values("datetime").reset_index(drop=True)
    if len(df) < 300:
        raise RuntimeError(f"Not enough candles returned ({len(df)}). Need at least 300.")
    return df

def indicators(df):
    d = df.copy()
    d["ema20"] = d.close.ewm(span=20, adjust=False).mean()
    d["ema50"] = d.close.ewm(span=50, adjust=False).mean()
    prev = d.close.shift(1)
    tr = pd.concat([d.high-d.low, (d.high-prev).abs(), (d.low-prev).abs()], axis=1).max(axis=1)
    d["atr"] = tr.rolling(14).mean()
    d["swing_hi"] = d.high.shift(1).rolling(20).max()
    d["swing_lo"] = d.low.shift(1).rolling(20).min()
    return d

# Signal values: +1 long, -1 short, 0 no signal. Only uses completed signal candle and prior candles.
def signals(d, strategy):
    s = pd.Series(0, index=d.index, dtype=int)
    o,h,l,c = d.open,d.high,d.low,d.close
    body = (c-o).abs()
    rng = (h-l).replace(0, np.nan)
    lower_wick = np.minimum(o,c)-l
    upper_wick = h-np.maximum(o,c)
    if strategy == "Sweep + Reclaim":
        s[(l < d.swing_lo) & (c > d.swing_lo) & (c > o) & (lower_wick >= body*1.2)] = 1
        s[(h > d.swing_hi) & (c < d.swing_hi) & (c < o) & (upper_wick >= body*1.2)] = -1
    elif strategy == "Failed Breakout":
        s[(h > d.swing_hi) & (c < d.swing_hi) & (upper_wick/rng >= 0.35) & (c < o)] = -1
        s[(l < d.swing_lo) & (c > d.swing_lo) & (lower_wick/rng >= 0.35) & (c > o)] = 1
    elif strategy == "EMA Trend Pullback":
        s[(d.ema20 > d.ema50) & (l <= d.ema20) & (c > d.ema20) & (c > o)] = 1
        s[(d.ema20 < d.ema50) & (h >= d.ema20) & (c < d.ema20) & (c < o)] = -1
    elif strategy == "MSS + FVG":
        # Candle i-2 to i gap, plus close breaks prior 10-candle structure.
        prev_hi = h.shift(1).rolling(10).max()
        prev_lo = l.shift(1).rolling(10).min()
        bull_fvg = l > h.shift(2)
        bear_fvg = h < l.shift(2)
        s[bull_fvg & (c > prev_hi) & (c > o)] = 1
        s[bear_fvg & (c < prev_lo) & (c < o)] = -1
    return s

def run_backtest(d, strategy):
    sig = signals(d, strategy)
    trades=[]
    # Entry is next candle open. Exit on SL/TP. Conservative same-candle assumption: SL first.
    for i in range(60, len(d)-1):
        direction = int(sig.iloc[i])
        if direction == 0 or not np.isfinite(d.atr.iloc[i]) or d.atr.iloc[i] <= 0:
            continue
        entry = float(d.open.iloc[i+1])
        atr = float(d.atr.iloc[i])
        candle_extreme = float(d.low.iloc[i]) if direction == 1 else float(d.high.iloc[i])
        raw_risk = (entry-candle_extreme) if direction == 1 else (candle_extreme-entry)
        risk = max(raw_risk, 0.5*atr)
        if risk <= 0: continue
        sl = entry-direction*risk
        tp = entry+direction*RR*risk
        outcome=None; exit_idx=None
        for j in range(i+1, len(d)):
            hi,lo=float(d.high.iloc[j]),float(d.low.iloc[j])
            hit_sl = lo <= sl if direction==1 else hi >= sl
            hit_tp = hi >= tp if direction==1 else lo <= tp
            if hit_sl and hit_tp:
                outcome=-1.0; exit_idx=j; break
            if hit_sl:
                outcome=-1.0; exit_idx=j; break
            if hit_tp:
                outcome=RR; exit_idx=j; break
        if outcome is None:
            # Unclosed at end; exclude from win-rate, but report separately.
            continue
        trades.append({"strategy":strategy,"signal_time":str(d.datetime.iloc[i]),"entry_time":str(d.datetime.iloc[i+1]),
                       "direction":"BUY" if direction==1 else "SELL","entry":entry,"SL":sl,"TP":tp,
                       "R":outcome,"exit_time":str(d.datetime.iloc[exit_idx])})
    return trades

def metrics(trades):
    if not trades: return {"trades":0,"winrate":0,"profit_factor":0,"net_R":0,"max_dd_R":0,"expectancy_R":0}
    r=np.array([x["R"] for x in trades], dtype=float)
    wins=r[r>0].sum(); losses=abs(r[r<0].sum())
    eq=np.cumsum(r); peak=np.maximum.accumulate(np.r_[0,eq]); dd=peak[1:]-eq
    return {"trades":len(r),"winrate":round(100*(r>0).mean(),1),
            "profit_factor":round(wins/losses,2) if losses else "∞",
            "net_R":round(r.sum(),2),"max_dd_R":round(dd.max() if len(dd) else 0,2),
            "expectancy_R":round(r.mean(),3)}

def main():
    d=indicators(get_data())
    strategies=["Sweep + Reclaim","Failed Breakout","EMA Trend Pullback","MSS + FVG"]
    all_trades=[]; rows=[]
    for st in strategies:
        tr=run_backtest(d,st); all_trades.extend(tr)
        m=metrics(tr); m["strategy"]=st; rows.append(m)
    result=pd.DataFrame(rows).sort_values(["profit_factor","expectancy_R"],ascending=False)
    pd.DataFrame(all_trades).to_csv("backtest_trades.csv",index=False)
    result.to_csv("backtest_summary.csv",index=False)
    start=d.datetime.iloc[0].strftime("%Y-%m-%d")
    end=d.datetime.iloc[-1].strftime("%Y-%m-%d")
    report=f"🧪 ICT BABA BACKTEST LAB\nSymbol: {SYMBOL} ({INTERVAL})\nData: {start} → {end}\nCandles: {len(d)} | RR: 1:{RR:g}\n\n"
    for _,row in result.iterrows():
        pf=row["profit_factor"]
        report += (f"📌 {row['strategy']}\nTrades: {int(row['trades'])} | Win: {row['winrate']}%\n"
                   f"PF: {pf} | Net: {row['net_R']}R | Max DD: {row['max_dd_R']}R\n"
                   f"Expectancy: {row['expectancy_R']}R/trade\n\n")
    report += "Note: historical test only; spread/slippage/commission not included. Same-candle TP+SL assumes SL first. No strategy is trap-free."
    print(report)
    send_telegram(report[:4000])

if __name__ == "__main__":
    main()
