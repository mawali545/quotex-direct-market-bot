from dataclasses import dataclass
from math import sqrt
from typing import Any, Dict, List
@dataclass
class Candle:
    t:int; o:float; h:float; l:float; c:float
def normalize(x:Any)->Candle:
    if isinstance(x,dict):
        return Candle(int(float(x.get('time',x.get('timestamp',x.get('t'))))),float(x.get('open',x.get('o'))),float(x.get('high',x.get('h'))),float(x.get('low',x.get('l'))),float(x.get('close',x.get('c'))))
    t,o,c,h,l=x[:5]; return Candle(int(float(t)),float(o),float(h),float(l),float(c))
def ema(vals,n):
    if not vals:return 0.0
    k=2/(n+1); e=vals[0]
    for v in vals[1:]: e=v*k+e*(1-k)
    return e
def rsi(vals,n=14):
    if len(vals)<=n:return 50.0
    g=[];l=[]
    for i in range(1,len(vals)):
        d=vals[i]-vals[i-1];g.append(max(d,0));l.append(max(-d,0))
    ag=sum(g[-n:])/n;al=sum(l[-n:])/n
    if al==0:return 100.0
    return 100-100/(1+ag/al)
def std(vals):
    if not vals:return 0.0
    m=sum(vals)/len(vals);return sqrt(sum((v-m)**2 for v in vals)/len(vals))
def analyze(raw:List[Any])->Dict[str,Any]:
    cs=[normalize(x) for x in raw][-200:]
    if len(cs)<35:return {'signal':'WAIT','strength':0,'reason':'Need more candles','factors':[]}
    closes=[x.c for x in cs];highs=[x.h for x in cs];lows=[x.l for x in cs]
    e5,e13,e21=ema(closes,5),ema(closes,13),ema(closes,21);rv=rsi(closes,14)
    m12,m26=ema(closes,12),ema(closes,26);macd=m12-m26
    ms=[ema(closes[:i+1],12)-ema(closes[:i+1],26) for i in range(26,len(closes))]
    sig=ema(ms,9) if ms else macd
    mid=sum(closes[-20:])/20;sd=std(closes[-20:]);upper=mid+2*sd;lower=mid-2*sd
    tr=[max(highs[i]-lows[i],abs(highs[i]-closes[i-1]),abs(lows[i]-closes[i-1])) for i in range(1,len(cs))]
    atr=sum(tr[-14:])/14;rh=max(highs[-20:]);rl=min(lows[-20:]);last=cs[-1]
    body=abs(last.c-last.o);uw=last.h-max(last.o,last.c);lw=min(last.o,last.c)-last.l
    score=0;f=[]
    if e5>e13>e21:score+=2;f.append('EMA bullish alignment')
    elif e5<e13<e21:score-=2;f.append('EMA bearish alignment')
    if 55<rv<75:score+=1;f.append('RSI bullish')
    elif 25<rv<45:score-=1;f.append('RSI bearish')
    if macd>sig:score+=1;f.append('MACD bullish')
    elif macd<sig:score-=1;f.append('MACD bearish')
    if last.c>mid:score+=1;f.append('Above Bollinger mid')
    elif last.c<mid:score-=1;f.append('Below Bollinger mid')
    if last.c>=upper:score-=1;f.append('Upper-band caution')
    elif last.c<=lower:score+=1;f.append('Lower-band rebound zone')
    if last.c>rh*.999:score+=1;f.append('Recent-high pressure')
    if last.c<rl*1.001:score-=1;f.append('Recent-low pressure')
    if last.c>last.o and lw>body*1.2:score+=1;f.append('Bullish rejection')
    if last.c<last.o and uw>body*1.2:score-=1;f.append('Bearish rejection')
    if len(cs)>=2:
        p=cs[-2]
        if last.c>last.o and p.c<p.o and last.o<=p.c and last.c>=p.o:score+=2;f.append('Bullish engulfing')
        if last.c<last.o and p.c>p.o and last.o>=p.c and last.c<=p.o:score-=2;f.append('Bearish engulfing')
    if atr<=max(abs(last.c)*.00005,1e-12):return {'signal':'WAIT','strength':35,'reason':'Very low volatility','factors':f}
    s='UP' if score>=5 else 'DOWN' if score<=-5 else 'WAIT';strength=min(99,max(0,50+score*7))
    if s=='WAIT':strength=min(strength,59)
    return {'signal':s,'strength':strength,'reason':f'{len(f)} confirmations; score {score}','factors':f,'rsi':round(rv,1),'ema5':e5,'ema13':e13,'ema21':e21,'macd':macd,'atr':atr,'support':rl,'resistance':rh}
