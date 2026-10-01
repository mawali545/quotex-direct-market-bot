# AMH110 v3 — Video-Reference Signal Assistant

This build targets the saved AMH110 video concept: a premium dark trading screen plus a compact floating assistant.

### Real-data rules
- Quotex live OHLC is the primary source.
- The app loads the real Quotex instrument list after connection.
- Historical and realtime candles are read from the pinned PyQuotex revision.
- A screen/chart cross-check uses Android MediaProjection.
- UP/DOWN is shown only when the direct analysis and visible-chart cross-check agree.
- Otherwise the app stays WAIT.
- No fake/random signals.
- No auto-trading or click automation.
- No 20-second timeframe.

### Android permissions during demo
1. Connect with your Quotex account.
2. Tap **OVERLAY + CHART READER**.
3. Allow **Display over other apps**.
4. Allow Android's **screen capture** prompt.
5. Open Quotex and keep the AMH110 floating panel visible.
6. Use a DEMO account first.

### Build target
- Python 3.12
- python-for-android master
- Android API 35
- NDK 28c
- arm64-v8a only
- Java 17
- PyJnius 1.6.1
- PyQuotex pinned to commit `70fca1575b9c3e8f45aaaa08a54baf67adbdac68`

The percentage shown is analysis strength, not a claim of win probability. No software can guarantee no losses in real-money trading.
