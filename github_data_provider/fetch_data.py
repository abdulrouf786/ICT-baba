import json
import os
import time
from datetime import datetime, timezone

import requests
import pandas as pd

SYMBOLS = {
    "XAUUSD": {"yahoo": "XAUUSD=X", "twelve": "XAU/USD"},
    "EURUSD": {"yahoo": "EURUSD=X", "twelve": "EUR/USD"},
    "GBPUSD": {"yahoo": "GBPUSD=X", "twelve": "GBP/USD"},
}
TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h"]
HEADERS = {"User-Agent": "Mozilla/5.0 ICT-Baba-GitHub-Data/1.0"}
OUT = "data/market_data.json"
RAW_BASE = "https://raw.githubusercontent.com/abdulrouf786/ICT-baba/main/data"


def fetch_yahoo(symbol, tf):
    ticker = SYMBOLS[symbol]["yahoo"]
    source_interval = "60m" if tf == "4h" else tf
    period = "7d" if tf == "1m" else ("60d" if tf in ("5m", "15m") else "2y")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    response = requests.get(url, params={"range": period, "interval": source_interval},
                            headers=HEADERS, timeout=25)
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
    return rows[-500:], "Yahoo Finance", "Unofficial Yahoo feed; verify against your broker."


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
    return rows, "Twelve Data", "Provider symbol feed; verify spot pricing and plan limits."


def main():
    api_key = os.getenv("TWELVE_DATA_API_KEY", "").strip()
    result = {
        "service": "ICT Baba GitHub Data",
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "refresh_target_minutes": 5,
        "symbols": {},
        "notes": [
            "This is a GitHub-hosted data snapshot, not a continuously running server.",
            "GitHub Actions schedules can be delayed; a 5-minute schedule is not guaranteed.",
            "Market data is supplied by Yahoo Finance or Twelve Data; GitHub is not the market-data origin.",
            "Yahoo XAUUSD=X availability and quality can change. Always compare with your broker.",
            "Never use unverified data for automatic live order execution."
        ]
    }
    failures = []
    for symbol in SYMBOLS:
        result["symbols"][symbol] = {}
        for tf in TIMEFRAMES:
            try:
                if api_key:
                    try:
                        candles, source, note = fetch_twelve(symbol, tf, api_key)
                    except Exception:
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
                result["symbols"][symbol][tf] = {"source": None, "count": 0, "candles": [], "error": str(exc)}
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
