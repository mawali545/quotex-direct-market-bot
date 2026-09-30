from dataclasses import dataclass
from math import sqrt
from typing import Any, Dict, List

@dataclass
class Candle:
    t: int
    o: float
    h: float
    l: float
    c: float


def normalize(x: Any) -> Candle:
    if isinstance(x, dict):
        t = x.get('time', x.get('timestamp', x.get('t')))
        o = x.get('open', x.get('o'))
        h = x.get('high', x.get('h'))
        l = x.get('low', x.get('l'))
        c = x.get('close', x.get('c'))
        return Candle(int(float(t)), float(o), float(h), float(l), float(c))
    t, o, c, h, l = x[:5]
    return Candle(int(float(t)), float(o), float(h), float(l), float(c))


def ema(vals, n):
    if not vals: return 0.0
    k = 2/(n+1); e = vals[0]
    for v in vals[1:]: e = v*k + e*(1-k)
    return e


def rsi(vals, n=14):
    if len(vals) <= n: return 50.0
    gains=[]; losses=[]
    for i in range(1,len(vals)):
        d=vals[i]-vals[i-1]; gains.append(max(d,0)); losses.append(max(-d,0))
    ag=sum(gains[-n:])/n; al=sum(losses[-n:])/n
    if al == 0: return 100.0
    return 100 - 100/(1+ag/al)


def std(vals):
    if not vals: return 0.0
    m=sum(vals)/len(vals)
    return sqrt(sum((v-m)**2 for v in vals)/len(vals))


def analyze(raw: List[Any]) -> Dict[str, Any]:
    cs=[normalize(x) for x in raw][-200:]
    if len(cs)<35:
        return {'signal':'WAIT','strength':0,'reason':'Need more candles','factors':[]}
    closes=[x.c for x in cs]; highs=[x.h for x in cs]; lows=[x.l for x in cs]
    e5,e13,e21=ema(closes,5),ema(closes,13),ema(closes,21)
    rv=rsi(closes,14); m12,m26=ema(closes,12),ema(closes,26); macd=m12-m26
    sig=ema([ema(closes[:i+1],12)-ema(closes[:i+1],26) for i in range(26,len(closes))],9) if len(closes)>=35 else macd
    mid=sum(closes[-20:])/20; sd=std(closes[-20:]); upper=mid+2*sd; lower=mid-2*sd
    tr=[]
    for i in range(1,len(cs)):
        tr.append(max(highs[i]-lows[i],abs(highs[i]-closes[i-1]),abs(lows[i]-closes[i-1])))
    atr=sum(tr[-14:])/14
    recent_high=max(highs[-20:]); recent_low=min(lows[-20:])
    last=cs[-1]; body=abs(last.c-last.o); rng=max(last.h-last.l,1e-12)
    upper_w=last.h-max(last.o,last.c); lower_w=min(last.o,last.c)-last.l
    score=0; factors=[]
    if e5>e13>e21: score+=2; factors.append('EMA bullish alignment')
    elif e5<e13<e21: score-=2; factors.append('EMA bearish alignment')
    if rv>55 and rv<75: score+=1; factors.append('RSI bullish')
    elif rv<45 and rv>25: score-=1; factors.append('RSI bearish')
    if macd>sig: score+=1; factors.append('MACD bullish')
    elif macd<sig: score-=1; factors.append('MACD bearish')
    if last.c>mid: score+=1; factors.append('Above Bollinger mid')
    elif last.c<mid: score-=1; factors.append('Below Bollinger mid')
    if last.c>=upper: score-=1; factors.append('Upper-band caution')
    elif last.c<=lower: score+=1; factors.append('Lower-band rebound zone')
    if last.c>recent_high*0.999: score+=1; factors.append('Recent-high pressure')
    if last.c<recent_low*1.001: score-=1; factors.append('Recent-low pressure')
    if last.c>last.o and lower_w>body*1.2: score+=1; factors.append('Bullish rejection')
    if last.c<last.o and upper_w>body*1.2: score-=1; factors.append('Bearish rejection')
    if len(cs)>=2:
        prev=cs[-2]
        if last.c>last.o and prev.c<prev.o and last.o<=prev.c and last.c>=prev.o:
            score+=2; factors.append('Bullish engulfing')
        if last.c<last.o and prev.c>prev.o and last.o>=prev.c and last.c<=prev.o:
            score-=2; factors.append('Bearish engulfing')
    if atr <= max(abs(last.c)*0.00005, 1e-12):
        return {'signal':'WAIT','strength':35,'reason':'Very low volatility','factors':factors}
    signal='UP' if score>=5 else 'DOWN' if score<=-5 else 'WAIT'
    strength=min(99, max(0, 50+score*7))
    if signal=='WAIT': strength=min(strength,59)
    return {'signal':signal,'strength':strength,'reason':f'{len([f for f in factors if f])} confirmations; score {score}',
            'factors':factors,'rsi':round(rv,1),'ema5':e5,'ema13':e13,'ema21':e21,'macd':macd,'atr':atr,
            'support':recent_low,'resistance':recent_high}
