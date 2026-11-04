# ICT Baba

GitHub-hosted ICT market scanner and indicator rules. No TradingView account, webhook, or separate hosting website is required for the Python Telegram scanner.

## Markets
- XAUUSD: Gold feed configured in `background_scanner.py`. This is broker/spot Gold data and is not the same as PAXG.
- BTCUSDT, ETHUSDT, PAXGUSDT: Binance public OHLC endpoints; no Binance API key is needed for public candle data.
- EUR/USD and GBP/USD are not included.

## Timeframes
1m, 5m, 15m, 1h, 4h.

## ICT logic
- Confirmed swing highs/lows and BSL/SSL liquidity sweeps
- MSS / BOS-style structure breaks
- Three-candle FVG
- FVG retest confirmation
- Entry, stop loss, take profit (default indicator retest target is 1:2 RR)
- Existing scanner modules also detect order blocks, mitigation/breaker blocks, IFVG and approximate OTE
- Duplicate alert protection and TP/SL outcome tracking

## GitHub setup
1. In repository **Settings → Secrets and variables → Actions**, add:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
2. Open **Actions → ICT Baba Background Scanner** and use **Run workflow** for a manual scan.
3. The scheduled workflow checks approximately every 5 minutes. GitHub may delay scheduled jobs; it is not a guaranteed real-time feed.

## Files
- `background_scanner.py`: Python scanner and Telegram integration, including the Python implementation of the indicator's sweep + MSS + FVG retest rules.
- `indicators/ICT_Baba_Indicator.pine`: optional Pine Script source stored in GitHub. It is not required by the Python scanner and is not executed by GitHub Actions.
- `.github/workflows/ict-background-scanner.yml`: scheduled GitHub Actions job.

## Important
PAXG/USDT is a gold-backed token market, not broker XAUUSD. Public Binance market data does not require an API key, but availability and rate limits can change. Alerts are educational rule-based setups, not guaranteed trades or financial advice.
