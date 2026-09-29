from engine import Candle, analyze, combine_signals
cs=[]
price=100.0
for i in range(80):
    o=price; c=price+0.05; h=c+0.02; l=o-0.01
    cs.append(Candle(i*60,o,h,l,c)); price=c
s=analyze(cs)
assert s is not None
assert combine_signals(s,'UP',70)[0] in ('UP','WAIT')
assert combine_signals(s,'DOWN',70)[0] == 'WAIT' if s.signal != 'DOWN' else True
print('OK: direct engine + dual-source cross-check')
