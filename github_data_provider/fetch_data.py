import json
import os
import time
from datetime import datetime, timezone

import requests
import pandas as pd

# Crypto candles come directly from Binance public market-data API (no API key).
# XAUUSD is kept separate and uses Twelve Data when configured, with Yahoo fallback.
SYMBOLS = {
    "XAUUSD": {"provider": "twelve_yahoo", "twelve": "XAU/USD", "yahoo": "GC=F"},
    "BTCUSDT": {"provider": "binance", "binance": "BTCUSDT"},
    "ETHUSDT": {"provider": "binance", "binance": "ETHUSDT"},
    "PAXGUSDT": {"provider": "binance", "binance": "PAXGUSDT"},
}
TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h"]
HEADERS = {"User-Agent": "Mozilla/5.0 ICT-Baba-GitHub-Data/1.1"}
OUT = "data/market_data.json"


def fetch_binance(symbol, tf):
    pair = SYMBOLS[symbol]["binance"]
    response = requests.get(
        "https://api.binance.vision/api/v3/klines",
        params={"symbol": pair, "interval": tf, "limit": 500},
        headers=HEADERS,
        timeout=25,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise RuntimeError(str(payload))
    rows = []
    for candle in payload:
        rows.append({
            "time": datetime.fromtimestamp(candle[0] / 1000, timezone.utc).isoformat(),
            "open": float(candle[1]),
            "high": float(candle[2]),
            "low": float(candle[3]),
            "close": float(candle[4]),
            "volume": float(candle[5]),
        })
    if not rows:
        raise RuntimeError(f"Binance returned no candles for {pair}")
    return rows, "Binance Spot API", f"{pair} spot market OHLC; this is not broker XAUUSD pricing."


def fetch_yahoo(symbol, tf):
    ticker = SYMBOLS[symbol]["yahoo"]
    source_interval = "60m" if tf == "4h" else tf
    period = "7d" if tf == "1m" else ("60d" if tf in ("5m", "15m") else "2y")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    response = requests.get(
        url, params={"range": period, "interval": source_interval},
        headers=HEADERS, timeout=25
    )
    response.raise_for_status()
    payload = response.json()
    result = (payload.get("chart") or {}).get("result")
    if not result:
        error = (payload.get("chart") or {}).get("error") or {}
        raise RuntimeError(error.get("description") or "Yahoo returned no data")
    item = result[0]
    timestamps = item.get("timestamp") or []
    quote = item.get("indicators", {}).get("quote", [{}])[0]
    rows = []
    for i, ts in enumerate(timestamps):
        vals = [quote.get(k, [None] * len(timestamps))[i] for k in ("open", "high", "low", "close")]
        if any(v is None for v in vals):
            continue
        rows.append({
            "time": datetime.fromtimestamp(ts, timezone.utc).isoformat(),
            "open": float(vals[0]), "high": float(vals[1]),
            "low": float(vals[2]), "close": float(vals[3]),
            "volume": float((quote.get("volume") or [0] * len(timestamps))[i] or 0),
        })
    if tf == "4h":
        frame = pd.DataFrame(rows)
        if not frame.empty:
            frame["time"] = pd.to_datetime(frame["time"], utc=True)
            frame = frame.set_index("time").resample("4h").agg({
                "open": "first", "high": "max", "low": "min",
                "close": "last", "volume": "sum"
            }).dropna(subset=["open", "high", "low", "close"])
            rows = [{"time": idx.isoformat(), **{k: float(v) for k, v in row.items()}}
                    for idx, row in frame.iterrows()]
    return rows[-500:], "Yahoo Finance Gold Futures (GC=F)", "Gold futures proxy, NOT broker spot XAUUSD; verify against broker."


def fetch_twelve(symbol, tf, api_key):
    interval = {"1m": "1min", "5m": "5min", "15m": "15min", "1h": "1h", "4h": "4h"}[tf]
    response = requests.get("https://api.twelvedata.com/time_series", params={
        "symbol": SYMBOLS[symbol]["twelve"], "interval": interval,
        "outputsize": 500, "apikey": api_key, "format": "JSON"
    }, timeout=25)
    response.raise_for_status()
    payload = response.json()
    if "values" not in payload:
        raise RuntimeError(payload.get("message", "Twelve Data returned no values"))
    rows = []
    for row in reversed(payload["values"]):
        rows.append({
            "time": row["datetime"],
            "open": float(row["open"]), "high": float(row["high"]),
            "low": float(row["low"]), "close": float(row["close"]),
            "volume": float(row.get("volume") or 0),
        })
    return rows, "Twelve Data", "Provider XAU/USD feed; verify spot pricing and plan limits."


def main():
    api_key = os.getenv("TWELVE_DATA_API_KEY", "").strip()
    result = {
        "service": "ICT Baba GitHub Data",
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "refresh_target_minutes": 5,
        "symbols": {},
        "notes": [
            "Crypto OHLC candles are fetched from Binance public market-data mirror (api.binance.vision), no API key required.",
            "BTCUSDT, ETHUSDT and PAXGUSDT are Binance trading pairs; PAXGUSDT is not broker XAUUSD.",
            "XAUUSD uses Twelve Data for spot when configured; fallback GC=F is gold futures, NOT spot XAUUSD.",
            "This is a GitHub-hosted data snapshot, not a continuously running server.",
            "GitHub Actions schedules can be delayed; a 5-minute schedule is not guaranteed.",
            "Never use unverified data for automatic live order execution."
        ]
    }
    failures = []
    for symbol, config in SYMBOLS.items():
        result["symbols"][symbol] = {}
        for tf in TIMEFRAMES:
            try:
                if config["provider"] == "binance":
                    candles, source, note = fetch_binance(symbol, tf)
                else:
                    if api_key:
                        try:
                            candles, source, note = fetch_twelve(symbol, tf, api_key)
                        except Exception as twelve_error:
                            print(f"Twelve Data failed {symbol} {tf}: {twelve_error}")
                            candles, source, note = fetch_yahoo(symbol, tf)
                    else:
                        candles, source, note = fetch_yahoo(symbol, tf)
                if not candles:
                    raise RuntimeError("No valid OHLC candles")
                result["symbols"][symbol][tf] = {
                    "source": source, "instrument_note": note,
                    "count": len(candles), "candles": candles
                }
                print(f"OK {symbol} {tf}: {len(candles)} candles from {source}")
            except Exception as exc:
                failures.append(f"{symbol} {tf}: {type(exc).__name__}: {exc}")
                result["symbols"][symbol][tf] = {
                    "source": None, "count": 0, "candles": [], "error": str(exc)
                }
            time.sleep(0.25)
    os.makedirs("data", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, separators=(",", ":"))
    print(f"Saved {OUT}; errors={len(failures)}")
    for failure in failures:
        print("DATA ERROR:", failure)
    if all(not result["symbols"][s][tf]["candles"] for s in SYMBOLS for tf in TIMEFRAMES):
        raise SystemExit("All market data requests failed; refusing to publish an empty snapshot.")


if __name__ == "__main__":
    main()
