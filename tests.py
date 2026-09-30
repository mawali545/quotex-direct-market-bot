import ast
from pathlib import Path
from engine import Candle, normalize, analyze

ROOT = Path(__file__).parent
for path in ROOT.glob("*.py"):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

cs = normalize([{"time":100,"open":1,"close":2,"high":3,"low":0}])
assert len(cs) == 1 and cs[0].c == 2

spec = (ROOT/"buildozer.spec").read_text(encoding="utf-8")
main = (ROOT/"main.py").read_text(encoding="utf-8")
assert "values: ['5','10','15','30','60','120','300','600','900','1800','3600','7200','14400','86400']" in main
assert "'20'" not in main and '"20"' not in main
assert ".buy(" not in main and ".sell(" not in main and "open_pending" not in main

series=[]
p=100.0
for i in range(120):
    o=p; c=p+(0.15 if i%3 else 0.05); h=max(o,c)+0.08; l=min(o,c)-0.05
    series.append(Candle(i,o,h,l,c)); p=c
s=analyze(series)
assert s is not None and s.signal in ("UP","DOWN","WAIT")
assert 0 <= s.strength <= 100

for rel in ["main.py","engine.py","tests.py","buildozer.spec","README.md",".github/workflows/android.yml"]:
    assert (ROOT/rel).exists(), rel

print("OK: syntax, native periods, no auto-trade, normalization, indicators, files")
