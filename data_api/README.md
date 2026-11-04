# ICT Baba Data API

A small FastAPI service for the ICT Baba scanner.

## Supported markets and intervals
- XAUUSD, EURUSD, GBPUSD
- 1m, 5m, 15m, 1h, 4h
- `/ohlc/{symbol}?interval=5m&limit=200`
- `/price/{symbol}`, `/symbols`, `/health`, `/docs`

## Data sources and important accuracy note
1. If `TWELVE_DATA_API_KEY` is configured, the service requests XAU/USD, EUR/USD or GBP/USD from Twelve Data.
2. If Twelve Data is not configured or fails, it falls back to Yahoo Finance.
3. Yahoo's `GC=F` is COMEX gold futures, **not spot XAUUSD**. The API explicitly labels this distinction. Yahoo Finance is an unofficial fallback and may be delayed or rate-limited.
4. Yahoo does not supply native 4-hour candles here; the fallback aggregates four 1-hour bars.

Do not use this API for live order execution until the feed, timestamp, spread and broker price have been independently checked.

## Run locally
```bash
cd data_api
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Set the Twelve Data key as an environment variable; never commit API keys:
```bash
export TWELVE_DATA_API_KEY="YOUR_KEY"
```

## Deploy on Render
Use the root `render.yaml` blueprint. Add `TWELVE_DATA_API_KEY` as a secret environment variable in the Render dashboard. Free web services may sleep when idle and provider free-tier limits apply.
