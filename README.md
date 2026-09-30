# AMH110 V3

Direct-OHLC Android market-signal project.

- UP / DOWN / WAIT only
- No automatic trading or clicking
- Native periods only; no fake 20-second candles
- Direct market/OHLC analysis
- EMA, RSI, MACD, Bollinger Bands, ATR, rejection and engulfing checks
- Analysis strength is an agreement score, not a guaranteed win probability

## V3 build fix
V2 failed during python-for-android's pure-Python install stage because the Android build environment created a Python 3.14 venv with an incompatible/mixed pip state.

V3 pins python-for-android to commit `9a7694e` on the `develop` branch, which is the p4a fix specifically associated with the September 2026 pip-venv corruption/self-upgrade problem.

The GitHub Actions workflow still uses host Python 3.12 and removes `.buildozer` and `bin` before every build.
