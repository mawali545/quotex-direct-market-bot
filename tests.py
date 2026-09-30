import ast, pathlib
from engine import analyze
root=pathlib.Path(__file__).parent
for p in root.glob('*.py'): ast.parse(p.read_text())
import re
period_text=pathlib.Path(root/'main.py').read_text().split('PERIODS=')[1].split(']')[0]
periods=re.findall(r"'([^']+)'", period_text)
assert '20' not in periods
assert not any(x in pathlib.Path(root/'main.py').read_text() for x in ['.buy(','.sell(','open_pending'])
raw=[]
price=100.0
for i in range(120):
    o=price; c=price+(0.04 if i%3 else -0.01); h=max(o,c)+0.08; l=min(o,c)-0.08; raw.append([i,o,c,h,l]); price=c
r=analyze(raw); assert r['signal'] in {'UP','DOWN','WAIT'} and 0<=r['strength']<=99
print('AMH110 AUDIT PASS')
