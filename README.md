# Direct Market Signal Bot V4

Android/Kivy packaging layer for the direct-market-data signal engine.

## Design
- Direct OHLC/WebSocket market data; no screenshots or screen pixels.
- Signal-only; no order placement and no auto-clicking.
- Closed-candle analysis.
- EMA 5/13/21, RSI 14, MACD 12/26/9, Bollinger 20/2, ATR 14, ADX, stochastic context, rejection/engulfing, structure, support/resistance.
- UP/DOWN only when score reaches threshold; otherwise WAIT.
- Strength is a deterministic score, not a win probability.
- Credentials are entered locally on the phone and are not sent to chat.

## APK build
The included GitHub Actions workflow uses Buildozer to build a debug APK. Buildozer/p4a can package Python/Kivy Android apps and GitHub Actions can perform the build remotely. The build is not claimed tested until GitHub Actions actually succeeds and the resulting APK is installed/tested.

## Important
The Quotex client dependency is unofficial and its protocol can change. If the connection/data stream fails, the app shows WAIT/ERROR rather than fabricating signals.
