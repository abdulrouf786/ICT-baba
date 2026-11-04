import os
import time
from datetime import datetime, timezone
from typing import Optional

import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

APP_NAME = "ICT Baba Data API"
TWELVE_DATA_KEY = os.getenv("TWELVE_DATA_API_KEY", "").strip()
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "20"))
cache = {}

app = FastAPI(title=APP_NAME, version="1.0.0", description="OHLC API for Gold and major FX pairs.")

SYMBOLS = {
    "XAUUSD": {"twelve": "XAU/USD", "yahoo": "GC=F", "label": "Gold (Yahoo fallback is COMEX futures)"},
    "EURUSD": {"twelve": "EUR/USD", "yahoo": "EURUSD=X", "label": "Euro / US Dollar"},
    "GBPUSD": {"twelve": "GBP/USD", "yahoo": "GBPUSD=X", "label": "British Pound / US Dollar"},
}
INTERVALS = {"1m": "1min", "5m": "5min", "15m": "15min", "1h": "1h", "4h": "4h"}
YAHOO_INTERVALS = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "60m", "4h": "60m"}

def _twelve_data(symbol: str, interval: str, outputsize: int):
    params = {
        "symbol": SYMBOLS[symbol]["twelve"],
        "interval": INTERVALS[interval],
        "outputsize": min(max(outputsize, 1), 5000),
        "apikey": TWELVE_DATA_KEY,
        "format": "JSON",
    }
    response = requests.get("https://api.twelvedata.com/time_series", params=params, timeout=20)
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") == "error" or "values" not in payload:
        raise RuntimeError(payload.get("message", "Twelve Data returned no candle values"))
    values = []
    for row in reversed(payload["values"]):
        values.append({
            "time": row["datetime"],
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": float(row.get("volume") or 0),
        })
    return values, "Twelve Data", "provider-reported spot/FX symbol"

def _yahoo_data(symbol: str, interval: str, outputsize: int):
    ticker = SYMBOLS[symbol]["yahoo"]
    yahoo_interval = YAHOO_INTERVALS[interval]
    period = "7d" if interval == "1m" else ("60d" if interval in ("5m", "15m") else "2y")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, params={"range": period, "interval": yahoo_interval}, headers=headers, timeout=20)
    response.raise_for_status()
    result = response.json().get("chart", {}).get("result")
    if not result:
        error = response.json().get("chart", {}).get("error") or {}
        raise RuntimeError(error.get("description", "Yahoo Finance returned no candles"))
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
    # Yahoo does not provide native 4-hour candles; aggregate four 1-hour bars.
    if interval == "4h":
        grouped = []
        for start in range(0, len(rows), 4):
            chunk = rows[start:start + 4]
            if len(chunk) != 4:
                continue
            grouped.append({
                "time": chunk[0]["time"], "open": chunk[0]["open"],
                "high": max(x["high"] for x in chunk),
                "low": min(x["low"] for x in chunk),
                "close": chunk[-1]["close"],
                "volume": sum(x["volume"] for x in chunk),
            })
        rows = grouped
    return rows[-outputsize:], "Yahoo Finance", ("COMEX gold futures (GC=F), not spot XAUUSD" if symbol == "XAUUSD" else "Yahoo Finance FX quote")

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>ICT Baba Data API</title><style>
    body{font-family:Arial;background:#101722;color:#eef4ff;max-width:850px;margin:40px auto;padding:20px}
    .card{background:#1b2838;border:1px solid #34465c;border-radius:14px;padding:20px;margin:14px 0}
    a{color:#71c7ff}code{color:#9ee6b0}button{background:#2477bd;color:white;border:0;padding:10px 14px;border-radius:8px}
    </style></head><body><h1>ICT Baba Data API</h1>
    <p>Your market-data gateway for the ICT Scanner.</p>
    <div class="card"><h2>Supported symbols</h2><p>XAUUSD · EURUSD · GBPUSD</p>
    <p>Timeframes: 1m · 5m · 15m · 1h · 4h</p></div>
    <div class="card"><h2>Try an endpoint</h2>
    <p><a href="/ohlc/XAUUSD?interval=1m&limit=20">Gold 1-minute OHLC</a></p>
    <p><a href="/ohlc/EURUSD?interval=5m&limit=20">EURUSD 5-minute OHLC</a></p>
    <p><a href="/ohlc/GBPUSD?interval=1h&limit=20">GBPUSD 1-hour OHLC</a></p>
    <p><a href="/docs">Interactive API documentation</a></p></div>
    <p>Data source is identified in every API response. Free upstream feeds can be delayed, rate-limited, or changed.</p>
    </body></html>
    """

@app.get("/health")
def health():
    return {"ok": True, "service": APP_NAME, "time_utc": datetime.now(timezone.utc).isoformat(),
            "twelve_data_key_configured": bool(TWELVE_DATA_KEY)}

@app.get("/symbols")
def symbols():
    return {"symbols": list(SYMBOLS), "intervals": list(INTERVALS)}

@app.get("/ohlc/{symbol}")
def ohlc(symbol: str, interval: str = Query("5m"), limit: int = Query(200, ge=1, le=1000)):
    symbol = symbol.upper().replace("/", "")
    if symbol not in SYMBOLS:
        raise HTTPException(404, "Supported symbols: XAUUSD, EURUSD, GBPUSD")
    if interval not in INTERVALS:
        raise HTTPException(400, "Supported intervals: 1m, 5m, 15m, 1h, 4h")
    cache_key = (symbol, interval, limit)
    now = time.time()
    cached = cache.get(cache_key)
    if cached and now - cached["at"] < CACHE_TTL:
        return {**cached["data"], "cached": True}

    errors = []
    if TWELVE_DATA_KEY:
        try:
            candles, source, instrument_note = _twelve_data(symbol, interval, limit)
            data = {"symbol": symbol, "interval": interval, "source": source,
                    "instrument_note": instrument_note, "count": len(candles),
                    "candles": candles, "cached": False}
            cache[cache_key] = {"at": now, "data": data}
            return data
        except Exception as exc:
            errors.append(f"Twelve Data: {exc}")

    try:
        candles, source, instrument_note = _yahoo_data(symbol, interval, limit)
        data = {"symbol": symbol, "interval": interval, "source": source,
                "instrument_note": instrument_note, "count": len(candles),
                "candles": candles, "cached": False,
                "warning": "Yahoo data is an unofficial fallback and may be delayed."}
        cache[cache_key] = {"at": now, "data": data}
        return data
    except Exception as exc:
        errors.append(f"Yahoo Finance: {exc}")
        raise HTTPException(502, "No upstream candle data available. " + " | ".join(errors))

@app.get("/price/{symbol}")
def price(symbol: str):
    result = ohlc(symbol, interval="1m", limit=2)
    if not result["candles"]:
        raise HTTPException(502, "No price available")
    last = result["candles"][-1]
    return {"symbol": result["symbol"], "price": last["close"], "time": last["time"],
            "source": result["source"], "instrument_note": result["instrument_note"]}
