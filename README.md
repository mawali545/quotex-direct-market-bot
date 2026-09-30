# AMH110

Video-reference inspired Quotex market-signal Android bot.

- Direct OHLC market analysis; no screenshot/pixel analysis.
- UP / DOWN / WAIT signal.
- Multi-factor engine: EMA 5/13/21, RSI 14, MACD, Bollinger Bands, ATR, rejection/engulfing, recent highs/lows, support/resistance and market structure proxies.
- Analysis strength is an agreement score, not a guaranteed win probability.
- Weak/conflicting setups return WAIT.
- No automatic buy/sell/clicking or martingale.
- Native broker periods only; no fake 20-second candles.
- Credentials are entered locally on the phone and are not sent to this project author.

Build target: Buildozer 1.6.0, Java 17, p4a 957a3e5, PyQuotex pinned to 70fca1575b9c3e8f45aaaa08a54baf67adbdac68.

Live broker connection cannot be honestly guaranteed without testing a real account at build/runtime; PyQuotex is unofficial and broker protocols can change.
