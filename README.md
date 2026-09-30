# Direct Market Signal Bot V6 — Audited

Signal-only Android/Kivy app. Direct OHLC/WebSocket analysis; no screenshot analysis and no automatic trade execution.

### Signal engine
EMA 5/13/21, RSI 14, MACD, Bollinger Bands, ATR, ADX, stochastic, candle patterns, market structure and support/resistance. Weak/conflicting conditions return WAIT. Strength is an internal agreement score, not a win probability.

### Timeframes
Only broker-supported periods are included: 5, 10, 15, 30, 60, 120, 300, 600, 900, 1800, 3600, 7200, 14400, 86400 seconds. 20 seconds is removed.

### Build compatibility
- Buildozer 1.6.0
- GitHub runner Ubuntu 24.04
- Host Python 3.11
- Java 17
- python-for-android release 2024.01.21 commit `957a3e5`
- PyQuotex pinned to `70fca1575b9c3e8f45aaaa08a54baf67adbdac68`
- PyQuotex dependency path uses httpx + websockets; curl_cffi is not used
- No NumPy, Pillow, pyjnius, or Android Python package is manually added to app requirements

### Connection
The app tries several known Quotex hosts and fails safely to WAIT/ERROR. PyQuotex is unofficial and broker protocol changes can break connectivity. A live broker login cannot be claimed as tested without using real credentials against the live service; credentials should never be sent in chat.
