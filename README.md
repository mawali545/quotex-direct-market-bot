# Quotex Direct Market Signal Bot V5.4

Dual-source signal assistant:
- Direct live Quotex/WebSocket OHLC analysis is the primary source.
- Optional Android MediaProjection screen-chart assist reads the visible Quotex chart.
- The screen source can only confirm the direct signal; conflict or weak screen evidence becomes WAIT.
- Signal only: no automatic clicks or trades.
- Native broker-supported periods only; 20 seconds is not included.
- Indicators include EMA 5/13/21, RSI 14, MACD, Bollinger Bands, ATR, ADX, stochastic, support/resistance, market structure and candle patterns.

Screen capture requires the Android user to grant the system screen-capture permission. This project has not been live-tested against a Quotex account in this environment.


### V5.6 connection resilience
- Uses the current PyQuotex browser-style User-Agent.
- If a mobile TLS connection is reset on one supported Quotex host, the app tries the other documented hosts automatically.
- The UI reports which host is being attempted and shows the recent connection errors if all attempts fail.
- No credentials are stored in the project; they are entered locally in the app.
