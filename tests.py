import ast
import pathlib
import re
from engine import analyze

ROOT = pathlib.Path(__file__).parent
for p in ROOT.glob("*.py"):
    ast.parse(p.read_text(encoding="utf-8"))

main = (ROOT / "main.py").read_text(encoding="utf-8")
reader = (ROOT / "screen_reader.py").read_text(encoding="utf-8")
spec = (ROOT / "buildozer.spec").read_text(encoding="utf-8")
workflow = (ROOT / ".github/workflows/android.yml").read_text(encoding="utf-8")

# Safety / product invariants
period_text = main.split("PERIODS =", 1)[1].split("]", 1)[0]
assert '"20"' not in period_text
assert not any(x in main for x in [".buy(", ".sell(", "open_pending", "instruments_follow"])
assert "ok, reason =" in main and "if not ok:" in main
assert "get_historical_candles" in main
assert "get_realtime_candles" in main
assert "start_candles_stream" in main
assert "qxbroker.com" in main and "quotex.com" in main
assert "random" not in main.lower()
assert "SYSTEM_ALERT_WINDOW" in spec
assert "MediaProjectionManager" in reader
assert "createVirtualDisplay" in reader
assert "No stable colored candle bodies detected" in reader

# Dependency / Android compatibility target: stable p4a master + Python 3.12.
assert "python3==3.12.14" in spec and "hostpython3==3.12.14" in spec
assert "kivy==2.3.1" in spec
assert "pyjnius" in spec and "pyjnius==" not in spec
assert "websockets==14.2.0" in spec
assert "q.connect(is_demo=True)" in main
assert "Login.https_base_url" in main
assert "android.api = 35" in spec
assert "android.ndk = 25b" in spec
assert "android.archs = arm64-v8a" in spec
assert "armeabi-v7a" not in spec
assert "p4a.branch = master" in spec
assert 'runs-on: ubuntu-24.04' in workflow
assert 'python-version: "3.12"' in workflow
assert "libncurses-dev" in workflow and "libncurses5-dev" not in workflow
assert 'java-version: "17"' in workflow
assert "cython==0.29.34" in workflow
assert "numpy" not in spec and "curl_cffi" not in spec and "orjson" not in spec
assert "beautifulsoup4" in spec and "typing_extensions" in spec and "certifi" in spec
assert "charset-normalizer==3.4.3" in spec

# Analysis engine smoke test.
raw = []
price = 100.0
for i in range(160):
    o = price
    c = price + (0.04 if i % 3 else -0.01)
    raw.append({
        "time": i,
        "open": o,
        "high": max(o, c) + 0.08,
        "low": min(o, c) - 0.08,
        "close": c,
    })
    price = c
r = analyze(raw)
assert r["signal"] in {"UP", "DOWN", "WAIT"}
assert 0 <= r["strength"] <= 99
assert {"rsi", "macd", "stochastic", "adx", "atr", "support", "resistance"}.issubset(r)

print("AMH110 FINAL STATIC AUDIT PASS")
