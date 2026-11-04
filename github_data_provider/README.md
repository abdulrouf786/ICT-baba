# ICT Baba GitHub Data Provider

This provider runs entirely through GitHub Actions and stores the latest OHLC snapshot in this repository. It does not require Render, a VPS, or another hosting platform.

## Output
Raw JSON file:
https://raw.githubusercontent.com/abdulrouf786/ICT-baba/main/data/market_data.json

Supported symbols: XAUUSD, EURUSD, GBPUSD
Supported timeframes: 1m, 5m, 15m, 1h, 4h

## Refresh schedule
GitHub Actions is scheduled every 5 minutes and can also be started manually from the Actions tab. GitHub may delay scheduled runs; this is not a guaranteed live tick feed.

## Data source
- Default: Yahoo Finance chart feed.
- Optional: set repository Actions secret `TWELVE_DATA_API_KEY` to prefer Twelve Data. If it fails, the script falls back to Yahoo.
- GitHub stores and distributes the snapshot; it does not create market prices. Source and caveats are included in the JSON response.
- Confirm XAUUSD against your broker. If Yahoo's XAUUSD=X is unavailable, the corresponding symbol will show an error rather than silently substituting a different instrument.

## Enable
The repository must allow GitHub Actions and the workflow must be enabled. The workflow requires Actions permission to write repository contents.
