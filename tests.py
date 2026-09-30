import ast,pathlib,re
from engine import analyze
root=pathlib.Path(__file__).parent
for p in root.glob('*.py'):ast.parse(p.read_text())
txt=(root/'main.py').read_text()
periods=re.findall(r"'([^']+)'",txt.split('PERIODS=',1)[1].split(']',1)[0])
assert '20' not in periods
assert not any(x in txt for x in ['.buy(','.sell(','open_pending'])
raw=[];price=100
for i in range(120):
 o=price;c=price+(0.04 if i%3 else -0.01);raw.append([i,o,c,max(o,c)+.08,min(o,c)-.08]);price=c
r=analyze(raw);assert r['signal'] in {'UP','DOWN','WAIT'} and 0<=r['strength']<=99
print('AMH110 V3 AUDIT PASS')
