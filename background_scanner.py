import json
import os
import time
from pathlib import Path

import pandas as pd
import requests

ASSETS = {
    "XAUUSD": "XAUUSD",
    "BTCUSDT": "BTCUSDT",
    "ETHUSDT": "ETHUSDT",
    "EUR/USD": "YAHOO:EURUSD=X",
}
TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h"]
STATE_FILE = Path("alert_state.json")
HEADERS = {"User-Agent": "ICT-Baba-Background-Scanner/1.0", "Accept": "application/json"}


def fetch_ohlc(symbol, interval):
    if symbol == "XAUUSD":
        r = requests.get(
            f"https://biquote.io/api/XAUUSD/ohlc?interval={interval}&limit=500",
            headers=HEADERS, timeout=20,
        )
        r.raise_for_status()
        bars = r.json().get("bars", [])
        df = pd.DataFrame(bars)
    elif symbol.startswith("YAHOO:"):
        ticker = symbol.split(":", 1)[1]
        yahoo_interval = "60m" if interval == "4h" else interval
        period = "5d" if interval == "1m" else "1mo"
        r = requests.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
            params={"interval": yahoo_interval, "range": period},
            headers={**HEADERS, "User-Agent": "Mozilla/5.0"}, timeout=20,
        )
        r.raise_for_status()
        result = r.json().get("chart", {}).get("result")
        if not result:
            raise ValueError("Yahoo returned no candles")
        q = result[0]["indicators"]["quote"][0]
        ts = result[0].get("timestamp", [])
        df = pd.DataFrame({
            "openTime": pd.to_datetime(ts, unit="s", utc=True),
            "open": q.get("open", []), "high": q.get("high", []),
            "low": q.get("low", []), "close": q.get("close", []),
        })
        if interval == "4h":
            df = df.set_index("openTime").resample("4h").agg({
                "open": "first", "high": "max", "low": "min", "close": "last"
            }).dropna().reset_index()
    else:
        params = {"symbol": symbol, "interval": interval, "limit": 500}
        last_error = None
        for url in ("https://data-api.binance.vision/api/v3/klines",
                    "https://api.binance.com/api/v3/klines"):
            try:
                r = requests.get(url, params=params, headers=HEADERS, timeout=20)
                r.raise_for_status()
                break
            except requests.RequestException as exc:
                last_error = exc
        else:
            raise RuntimeError(f"Binance feed unavailable: {last_error}")
        bars = r.json()
        df = pd.DataFrame(bars, columns=[
            "openTime", "open", "high", "low", "close", "volume",
            "closeTime", "quoteVolume", "trades", "takerBuyBase",
            "takerBuyQuote", "ignore",
        ])
    if df.empty:
        raise ValueError("No OHLC candles")
    if symbol in ("BTCUSDT", "ETHUSDT"):
        df["openTime"] = pd.to_datetime(df["openTime"], unit="ms", utc=True)
    else:
        df["openTime"] = pd.to_datetime(df["openTime"], utc=True)
    for col in ("open", "high", "low", "close"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["openTime", "open", "high", "low", "close"]).sort_values("openTime").drop_duplicates("openTime").tail(450).reset_index(drop=True)


def scan_ict_setups(df):
    found = []
    if len(df) < 30:
        return found
    d = df.reset_index(drop=True)
    i = len(d) - 1
    b, p1, p2 = d.iloc[i], d.iloc[i-1], d.iloc[i-2]
    prior = d.iloc[max(0, i-20):i]
    ph, pl = float(prior.high.max()), float(prior.low.min())
    o, h, l, c = map(float, (b.open, b.high, b.low, b.close))
    bull_sweep, bear_sweep = l < pl and c > pl, h > ph and c < ph
    bull_fvg, bear_fvg = float(b.low) > float(p2.high), float(b.high) < float(p2.low)
    recent = d.iloc[max(0, i-8):i]
    bull_mss, bear_mss = c > float(recent.high.max()), c < float(recent.low.min())
    if bull_sweep: found.append(("Liquidity Sweep / Turtle Soup", "BUY", "SSL swept and close returned above prior 20-bar low"))
    if bear_sweep: found.append(("Liquidity Sweep / Turtle Soup", "SELL", "BSL swept and close returned below prior 20-bar high"))
    if bull_mss: found.append(("Bullish MSS / CHoCH", "BUY", "Close broke recent 8-bar structure high"))
    if bear_mss: found.append(("Bearish MSS / CHoCH", "SELL", "Close broke recent 8-bar structure low"))
    if bull_fvg: found.append(("Bullish FVG", "BUY", "Three-candle imbalance"))
    if bear_fvg: found.append(("Bearish FVG", "SELL", "Three-candle imbalance"))
    ob_bull = ob_bear = None
    for k in range(i-1, max(-1, i-9), -1):
        row = d.iloc[k]
        if ob_bull is None and float(row.close) < float(row.open) and bull_mss:
            ob_bull = (float(row.low), float(row.high))
        if ob_bear is None and float(row.close) > float(row.open) and bear_mss:
            ob_bear = (float(row.low), float(row.high))
    if ob_bull: found.append(("Bullish Order Block", "BUY", "Last bearish candle before bullish displacement"))
    if ob_bear: found.append(("Bearish Order Block", "SELL", "Last bullish candle before bearish displacement"))
    if ob_bull and l <= ob_bull[1] and c > ob_bull[1]: found.append(("Bullish Mitigation Block", "BUY", "Retest of bullish OB"))
    if ob_bear and h >= ob_bear[0] and c < ob_bear[0]: found.append(("Bearish Mitigation Block", "SELL", "Retest of bearish OB"))
    if ob_bull and c < ob_bull[0]: found.append(("Bullish Breaker Block", "SELL", "Bullish OB failed"))
    if ob_bear and c > ob_bear[1]: found.append(("Bearish Breaker Block", "BUY", "Bearish OB failed"))
    if i >= 3:
        old = d.iloc[i-3]
        if float(p1.low) > float(old.high) and c < float(old.high): found.append(("Bearish IFVG", "SELL", "Close through prior bullish FVG"))
        if float(p1.high) < float(old.low) and c > float(old.low): found.append(("Bullish IFVG", "BUY", "Close through prior bearish FVG"))
    swing_hi, swing_lo = float(d.iloc[i-20:i].high.max()), float(d.iloc[i-20:i].low.min())
    span = swing_hi - swing_lo
    if span > 0:
        if c > float(d.iloc[i-20].close) and swing_hi-.79*span <= c <= swing_hi-.62*span:
            found.append(("Bullish OTE (62%-79%)", "BUY", "Approximate OTE retracement zone"))
        if c < float(d.iloc[i-20].close) and swing_lo+.62*span <= c <= swing_lo+.79*span:
            found.append(("Bearish OTE (62%-79%)", "SELL", "Approximate OTE retracement zone"))
    unique = {}
    for name, side, reason in found:
        unique[(name, side)] = reason
    return [(n, s, r) for (n, s), r in unique.items()]


def send_telegram(text):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text}, timeout=20,
    )
    response.raise_for_status()
    if not response.json().get("ok"):
        raise RuntimeError("Telegram rejected the alert")


def main():
    state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
    sent = 0
    errors = []
    for pair, symbol in ASSETS.items():
        for tf in TIMEFRAMES:
            try:
                df = fetch_ohlc(symbol, tf)
                # Ignore the currently forming candle; evaluate the last closed candle.
                if len(df) < 31:
                    raise ValueError("Not enough candles")
                df = df.iloc[:-1].copy().reset_index(drop=True)
                candle_time = str(df.iloc[-1].openTime)
                setups = scan_ict_setups(df)
                for model, direction, reason in setups:
                    key = f"{pair}|{tf}|{model}|{direction}"
                    previous = state.get(key)
                    now_ts = time.time()
                    if isinstance(previous, dict):
                        last_sent = float(previous.get("sent_at", 0))
                        if now_ts - last_sent < 4 * 60 * 60:
                            continue
                    elif previous:
                        # Migrate the old candle-timestamp format without resending immediately.
                        if previous == candle_time:
                            continue
                        state[key] = {"sent_at": now_ts, "candle": str(previous)}
                        continue
                    last_candle = df.iloc[-1]
                    entry = float(last_candle.close)
                    stop_loss = float(last_candle.low if direction == "BUY" else last_candle.high)
                    risk = abs(entry - stop_loss)
                    if risk <= 0:
                        continue
                    take_profit = entry + (2 * risk if direction == "BUY" else -2 * risk)
                    decimals = 3 if pair == "USD/JPY" else (5 if pair in ("EUR/USD", "GBP/USD") else 2)
                    fmt = lambda value: f"{value:.{decimals}f}"
                    msg = (
                        "🌍 ICT BABA ALL-PAIR ALERT\n"
                        "\n"
                        f"📊 Pair: {symbol}\n"
                        f"⏱ Timeframe: {tf}\n"
                        f"🎯 Model: {model}\n"
                        f"📈 Direction: {'🟢 BUY' if direction == 'BUY' else '🔴 SELL'}\n"
                        f"💰 Close: {fmt(entry)}\n"
                        f"📝 Reason: {reason}\n\n"
                        "⚠️ Educational setup; verify before trading."
                    )
                    send_telegram(msg)
                    state[key] = {"sent_at": time.time(), "candle": candle_time}
                    sent += 1
                time.sleep(0.15)
            except Exception as exc:
                errors.append(f"{pair} {tf}: {type(exc).__name__}: {exc}")
    STATE_FILE.write_text(json.dumps(state, indent=2))
    print(f"Background scan finished. New Telegram alerts: {sent}. Feed errors: {len(errors)}")
    for error in errors:
        print(error)


if __name__ == "__main__":
    main()
