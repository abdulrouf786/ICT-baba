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




def higher_timeframe_bias(df):
    """EMA20/EMA50 closed-candle directional filter; simple advisory proxy."""
    if df is None or len(df) < 55:
        return "NEUTRAL"
    d = df.iloc[:-1] if len(df) > 1 else df
    close = pd.to_numeric(d["close"], errors="coerce")
    ema20 = close.ewm(span=20, adjust=False).mean().iloc[-1]
    ema50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
    last = float(close.iloc[-1])
    if last > ema20 > ema50:
        return "BULLISH"
    if last < ema20 < ema50:
        return "BEARISH"
    return "NEUTRAL"


def mtf_confirmation(pair, direction, cache):
    """Return 1H/4H trend context for the direction of an ICT setup."""
    for tf in ("1h", "4h"):
        key = (pair, tf)
        if key not in cache:
            try:
                cache[key] = higher_timeframe_bias(fetch_ohlc(ASSETS[pair], tf))
            except Exception:
                cache[key] = "UNAVAILABLE"
    one_hour, four_hour = cache[(pair, "1h")], cache[(pair, "4h")]
    desired = "BULLISH" if direction == "BUY" else "BEARISH"
    aligned = sum(x == desired for x in (one_hour, four_hour))
    opposing = sum(x not in (desired, "NEUTRAL", "UNAVAILABLE") for x in (one_hour, four_hour))
    if aligned == 2:
        label = "STRONG HTF ALIGNMENT 🟢"
    elif aligned == 1 and opposing == 0:
        label = "PARTIAL HTF ALIGNMENT 🟡"
    elif opposing:
        label = "COUNTER-TREND / WEAK HTF 🔴"
    else:
        label = "HTF NEUTRAL / UNAVAILABLE ⚪"
    return one_hour, four_hour, label

def signal_quality(setups, side):
    """Score ICT confluence groups (heuristic, not predictive certainty)."""
    names = [name.lower() for name, direction, _ in setups if direction == side]
    groups = {
        "liquidity": ("liquidity sweep", "turtle soup", "judas swing"),
        "structure": ("mss", "choch", "structure"),
        "imbalance": ("fvg", "ifvg"),
        "block": ("order block", "mitigation", "breaker", "unicorn"),
        "location": ("ote", "silver bullet"),
    }
    score = sum(1 for terms in groups.values()
                if any(term in name for name in names for term in terms))
    if score >= 4:
        return score, "STRONG 🟢"
    if score >= 2:
        return score, "MODERATE 🟡"
    return score, "WEAK 🔴"


def detect_retest_zones(df):
    """Find recently formed FVG and displacement Order Block zones."""
    zones = []
    d = df.reset_index(drop=True)
    start = max(2, len(d) - 7)
    for i in range(start, len(d)):
        bar, two_back = d.iloc[i], d.iloc[i - 2]
        formed_at = str(bar.openTime)
        # Three-candle fair value gaps.
        if float(bar.low) > float(two_back.high):
            zones.append(("Bullish FVG", "BUY", float(two_back.high), float(bar.low),
                          formed_at, "Bullish three-candle imbalance; wait for price to retrace into the FVG"))
        if float(bar.high) < float(two_back.low):
            zones.append(("Bearish FVG", "SELL", float(bar.high), float(two_back.low),
                          formed_at, "Bearish three-candle imbalance; wait for price to retrace into the FVG"))
        # Approximate OB: last opposite candle before a close breaking recent structure.
        prior = d.iloc[max(0, i - 8):i]
        if len(prior) >= 3:
            if float(bar.close) > float(prior.high.max()):
                candidates = prior[prior.close < prior.open]
                if not candidates.empty:
                    ob = candidates.iloc[-1]
                    zones.append(("Bullish Order Block", "BUY", float(ob.low), float(ob.high),
                                  formed_at, "Bullish displacement broke recent structure; wait for OB retest"))
            if float(bar.close) < float(prior.low.min()):
                candidates = prior[prior.close > prior.open]
                if not candidates.empty:
                    ob = candidates.iloc[-1]
                    zones.append(("Bearish Order Block", "SELL", float(ob.low), float(ob.high),
                                  formed_at, "Bearish displacement broke recent structure; wait for OB retest"))
    # Keep only one zone per model/direction/formation candle.
    unique = {}
    for zone in zones:
        unique[(zone[0], zone[1], zone[4])] = zone
    return list(unique.values())


def price_decimals(pair):
    return 5 if pair == "EUR/USD" else (2 if pair in ("XAUUSD", "BTCUSDT", "ETHUSDT") else 3)


def process_retest_alerts(pair, tf, symbol, df, state):
    """Send a pending-zone alert, then a retest-confirmed alert with 1:5 RR."""
    pending = state.setdefault("pending_retests", {})
    current = df.iloc[-1]
    candle_time = str(current.openTime)
    current_high, current_low, current_close = map(
        float, (current.high, current.low, current.close)
    )

    for model, direction, zone_low, zone_high, formed_at, reason in detect_retest_zones(df):
        key = f"{pair}|{tf}|{model}|{direction}|{formed_at}"
        if key not in pending:
            entry_plan = (zone_low + zone_high) / 2
            stop_plan = zone_low if direction == "BUY" else zone_high
            risk_plan = abs(entry_plan - stop_plan)
            target_plan = entry_plan + (5 * risk_plan if direction == "BUY" else -5 * risk_plan)
            decimals = price_decimals(pair)
            send_telegram(
                "📡 ICT BABA SETUP FOUND — RETEST PENDING\n\n"
                f"📊 Pair: {symbol}\n"
                f"⏱ Timeframe: {tf}\n"
                f"🎯 Model: {model}\n"
                f"📈 Direction: {'🟢 BUY' if direction == 'BUY' else '🔴 SELL'}\n"
                f"📍 Zone: {zone_low:.{decimals}f} – {zone_high:.{decimals}f}\n"
                f"💰 Planned Entry (zone midpoint): {entry_plan:.{decimals}f}\n"
                f"🛑 Planned SL: {stop_plan:.{decimals}f}\n"
                f"🎯 Planned TP: {target_plan:.{decimals}f}\n"
                "⚖️ Risk/Reward: 1:5\n"
                "⌛ Status: FVG/OB retest abhi baqi hai\n"
                f"📝 Reason: {reason}\n\n"
                "⚠️ Yeh planned zone hai, confirmed entry nahi."
            )
            pending[key] = {
                "pair": pair, "tf": tf, "model": model, "direction": direction,
                "low": zone_low, "high": zone_high, "formed_at": formed_at,
                "status": "pending",
            }

    # Check existing pending zones against the latest fully closed candle.
    for key, zone in list(pending.items()):
        if zone.get("pair") != pair or zone.get("tf") != tf or zone.get("status") != "pending":
            continue
        if candle_time <= zone.get("formed_at", ""):
            continue
        low, high = float(zone["low"]), float(zone["high"])
        touched = current_low <= high and current_high >= low
        direction = zone["direction"]
        confirmed = touched and (
            (direction == "BUY" and current_close > high) or
            (direction == "SELL" and current_close < low)
        )
        invalidated = (
            (direction == "BUY" and current_close < low) or
            (direction == "SELL" and current_close > high)
        )
        if confirmed:
            entry_price = current_close
            stop_price = low if direction == "BUY" else high
            risk = abs(entry_price - stop_price)
            if risk <= 0:
                zone["status"] = "invalidated"
                zone["invalidated_at"] = candle_time
                continue
            target_price = entry_price + (5 * risk if direction == "BUY" else -5 * risk)
            decimals = price_decimals(pair)
            send_telegram(
                "🚨 ICT BABA ENTRY RETEST CONFIRMED\n\n"
                f"📊 Pair: {symbol}\n"
                f"⏱ Timeframe: {tf}\n"
                f"🎯 Model: {zone['model']}\n"
                f"📈 Direction: {'🟢 BUY' if direction == 'BUY' else '🔴 SELL'}\n"
                f"📍 Retested Zone: {low:.{decimals}f} – {high:.{decimals}f}\n"
                f"💰 Entry (confirmation close): {entry_price:.{decimals}f}\n"
                f"🛑 Stop Loss: {stop_price:.{decimals}f}\n"
                f"🎯 Take Profit: {target_price:.{decimals}f}\n"
                "⚖️ Risk/Reward: 1:5\n"
                "✅ Price retested the zone and closed back in the trade direction.\n\n"
                "⚠️ Educational setup; verify execution costs and risk before trading."
            )
            zone["status"] = "confirmed"
            zone["confirmed_at"] = candle_time
        elif invalidated:
            zone["status"] = "invalidated"
            zone["invalidated_at"] = candle_time

    # Keep state bounded: discard zones older than 7 days.
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=7)
    for key, zone in list(pending.items()):
        try:
            if pd.to_datetime(zone.get("formed_at"), utc=True) < cutoff:
                del pending[key]
        except Exception:
            del pending[key]

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
    htf_cache = {}
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
                process_retest_alerts(pair, tf, symbol, df, state)
                for model, direction, reason in setups:
                    # FVG and OB alerts are handled by the two-stage
                    # RETEST PENDING -> ENTRY RETEST CONFIRMED flow above.
                    if model in ("Bullish FVG", "Bearish FVG",
                                 "Bullish Order Block", "Bearish Order Block"):
                        continue
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
                    take_profit = entry + (5 * risk if direction == "BUY" else -5 * risk)
                    decimals = price_decimals(pair)
                    fmt = lambda value: f"{value:.{decimals}f}"
                    target = entry + (5 * risk if direction == "BUY" else -5 * risk)
                    quality_score, quality_label = signal_quality(setups, direction)
                    htf_1h, htf_4h, htf_label = mtf_confirmation(pair, direction, htf_cache)
                    msg = (
                        "🌍 ICT BABA ICT CONDITION ALERT\n"
                        "\n"
                        f"📊 Pair: {symbol}\n"
                        f"⏱ Timeframe: {tf}\n"
                        f"🎯 Model: {model}\n"
                        f"📈 Direction: {'🟢 BUY' if direction == 'BUY' else '🔴 SELL'}\n"
                        f"🧠 Signal Quality: {quality_label} ({quality_score}/5)\n"
                        f"🧭 1H Trend: {htf_1h}\n"
                        f"🧭 4H Trend: {htf_4h}\n"
                        f"🔎 MTF Confirmation: {htf_label}\n"
                        f"💰 Entry Reference: {fmt(entry)}\n"
                        f"🛑 Stop Loss: {fmt(stop_loss)}\n"
                        f"🎯 Take Profit: {fmt(target)}\n"
                        "⚖️ Risk/Reward: 1:5\n"
                        f"📝 Reason: {reason}\n\n"
                        "⚠️ ICT condition alert; confirm the setup and execution manually."
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
