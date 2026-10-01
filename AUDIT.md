# AMH110 v4 — Build + Connection Compatibility Audit

## Current locked build stack
- GitHub Actions runner: Ubuntu 24.04 (pinned; avoids the 2026 ubuntu-latest migration).
- Buildozer: 1.6.0.
- Host Python: 3.12.
- p4a: master/develop-compatible commit `54cf321676712893786d4ccbbefbad3ff2e5930d`, pinned immediately before the p4a PyJNIus 1.7.0 recipe update.
- Target Python: **3.12.10** explicitly pinned for both `python3` and `hostpython3`; this prevents p4a's current default target Python 3.14.2 from selecting the incompatible PyJNIus path.
- Cython: 0.29.34.
- Java: 17.
- Kivy: 2.3.1.
- PyJNIus: 1.6.1.
- Android API: 35.
- Android min API: 24.
- Android NDK: 28c.
- Architecture: arm64-v8a only; `armeabi-v7a` is intentionally removed because it caused the previous PyJNIus 1.7.0 build failure.
- WebSockets: 14.2.0, matching the pinned PyQuotex source's `additional_headers` API.
- No numpy, curl_cffi or orjson.

## Connection blockers fixed in this audit
1. The app previously called `q.connect()` with no argument. The pinned PyQuotex revision requires `connect(is_demo: bool)`. The app now explicitly uses `q.connect(is_demo=True)` for the first/demo connection.
2. The pinned PyQuotex Login class has `base_url` / `https_base_url` as class attributes. The app now updates those attributes for each host before connecting, so host fallback actually changes the HTTP login endpoint.
3. The previous `websockets==12.0` pin conflicted with the pinned PyQuotex WebSocket client, which calls `websockets.connect(..., additional_headers=...)`. WebSockets 12's legacy asyncio client uses `extra_headers`; `additional_headers` is the newer API. The app now pins 14.2.0.
4. Newer p4a commits changed the bundled PyJNIus recipe to 1.7.0. This build pins the earlier p4a commit where the PyJNIus recipe is 1.6.1, then explicitly pins target/host Python 3.12.10. This removes the previously observed PyJNIus 1.7.0 / Python 3.14.2 path.
5. The workflow previously installed `libncurses5-dev`; the current GitHub Ubuntu runners use newer Ubuntu releases where `libncurses-dev` is the appropriate package. The workflow is pinned to Ubuntu 24.04 and uses `libncurses-dev`.
6. HTTPX is left unpinned in the app requirements so the p4a master HTTPX recipe can provide its current 0.28.x version; the PyQuotex requirement (`>=0.27,<1`) accepts that version.

## Real Quotex data path
1. DNS check.
2. HTTPS login through the pinned PyQuotex revision.
3. WebSocket authentication.
4. Live instrument list from Quotex.
5. Historical OHLC candles.
6. Realtime candle stream.
7. Direct OHLC analysis.
8. Final UP/DOWN only when the visible-chart cross-check agrees; otherwise WAIT.

## Screen/chart path
- Real Android WindowManager overlay.
- Real MediaProjection screen capture.
- Conservative red/green candle-like visual cross-check.
- Missing/unstable chart observation forces WAIT.

## Safety / trading behavior
- No buy/sell/order/click automation.
- No martingale.
- No 20-second period.
- Displayed percentage is analysis strength, not win probability.
- First connection is DEMO by design. Real-money use is not risk-free and no loss-free result can be guaranteed.

## Validation performed
- `python3 tests.py` passes.
- `python3 -m compileall -q .` passes.
- Dependency and API compatibility was cross-checked against current Buildozer/p4a/PyJNIus documentation and the exact pinned PyQuotex source.

## Remaining external dependency
The final APK still needs one actual GitHub Actions build and a real Quotex DEMO login test. Source/static audits cannot prove that Quotex will accept a particular account/network at runtime. PyQuotex is an unofficial library, and Cloudflare/network restrictions can still occur; those are server/network conditions rather than Python import/build errors.
