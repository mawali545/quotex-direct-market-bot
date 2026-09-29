from engine import Candle, analyze, macd

def synthetic(n=120):
    out=[]; p=100.0
    for i in range(n):
        o=p; c=p+0.05+(0.02 if i%7 else -0.01); h=max(o,c)+0.03; l=min(o,c)-0.03
        out.append(Candle(i,o,h,l,c)); p=c
    return out

cs=synthetic()
assert analyze(cs) is not None
m,ms,h=macd([c.c for c in cs])
assert m is not None and ms is not None and h is not None
print('V4 engine tests passed')
