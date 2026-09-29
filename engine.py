from __future__ import annotations
from dataclasses import dataclass
from math import sqrt
from statistics import pstdev
from typing import Any

@dataclass(frozen=True)
class Candle:
    t: int; o: float; h: float; l: float; c: float

@dataclass(frozen=True)
class Signal:
    signal: str; strength: int; score: int; reasons: tuple[str, ...]
    close: float; rsi: float|None; atr: float|None
    ema5: float|None; ema13: float|None; ema21: float|None
    macd: float|None; macd_signal: float|None
    bb_upper: float|None; bb_mid: float|None; bb_lower: float|None
    support: float|None; resistance: float|None

def num(v: Any) -> float|None:
    try: return float(v)
    except (TypeError, ValueError): return None

def normalize(raw: Any) -> list[Candle]:
    if isinstance(raw, dict): raw = raw.get('candles', raw.get('data', raw.get('result', raw)))
    if not isinstance(raw, (list, tuple)): return []
    out=[]
    for x in raw:
        if isinstance(x, dict):
            t=x.get('time',x.get('timestamp',x.get('from',x.get('t')))); o=x.get('open',x.get('o')); h=x.get('high',x.get('max',x.get('h'))); l=x.get('low',x.get('min',x.get('l'))); c=x.get('close',x.get('c'))
        elif isinstance(x,(list,tuple)) and len(x)>=5: t,o,h,l,c=x[:5]
        else: continue
        vals=tuple(map(num,(t,o,h,l,c)))
        if all(v is not None for v in vals):
            tt,oo,hh,ll,cc=vals
            if hh>=max(oo,cc) and ll<=min(oo,cc) and hh>=ll: out.append(Candle(int(tt),oo,hh,ll,cc))
    return [c for _,c in sorted({c.t:c for c in out}.items())]


def ema(v:list[float], n:int)->float|None:
    if len(v)<n:return None
    e=sum(v[:n])/n; k=2/(n+1)
    for x in v[n:]: e=x*k+e*(1-k)
    return e

def ema_series(v:list[float], n:int)->list[float]:
    if len(v)<n:return []
    e=sum(v[:n])/n; k=2/(n+1); out=[e]
    for x in v[n:]: e=x*k+e*(1-k); out.append(e)
    return out

def rsi(v:list[float],n:int=14)->float|None:
    if len(v)<n+1:return None
    gains=[]; losses=[]
    for a,b in zip(v[-n-1:-1],v[-n:]):
        d=b-a; gains.append(max(d,0)); losses.append(max(-d,0))
    ag,al=sum(gains)/n,sum(losses)/n
    if al==0:return 100.0
    return 100-(100/(1+ag/al))

def macd(v:list[float],fast:int=12,slow:int=26,sig:int=9):
    if len(v)<slow+sig:return None,None,None
    ef=ema_series(v,fast); es=ema_series(v,slow)
    # Both series are indexed by the original price timeline; align at slow EMA start.
    fast_aligned=ef[(slow-fast):]
    line=[a-b for a,b in zip(fast_aligned,es)]
    ss=ema_series(line,sig)
    if not line or not ss:return None,None,None
    return line[-1],ss[-1],line[-1]-ss[-1]

def atr(cs:list[Candle],n:int=14)->float|None:
    if len(cs)<n+1:return None
    tr=[]
    for i in range(1,len(cs)):
        p=cs[i-1].c;x=cs[i];tr.append(max(x.h-x.l,abs(x.h-p),abs(x.l-p)))
    return sum(tr[-n:])/n

def bb(v:list[float],n:int=20,k:float=2):
    if len(v)<n:return None,None,None
    s=v[-n:];m=sum(s)/n;sd=pstdev(s);return m+k*sd,m,m-k*sd

def adx(cs:list[Candle],n:int=14)->float|None:
    if len(cs)<n*2+1:return None
    trs=[];plus=[];minus=[]
    for i in range(1,len(cs)):
        cur,prev=cs[i],cs[i-1];trs.append(max(cur.h-cur.l,abs(cur.h-prev.c),abs(cur.l-prev.c)))
        up=cur.h-prev.h;down=prev.l-cur.l;plus.append(up if up>down and up>0 else 0.0);minus.append(down if down>up and down>0 else 0.0)
    av=sum(trs[-n:])/n
    if av==0:return 0.0
    pdi=100*(sum(plus[-n:])/n)/av;mdi=100*(sum(minus[-n:])/n)/av
    return 0.0 if pdi+mdi==0 else 100*abs(pdi-mdi)/(pdi+mdi)

def stochastic(cs:list[Candle],n:int=14)->float|None:
    if len(cs)<n:return None
    s=cs[-n:];hi=max(x.h for x in s);lo=min(x.l for x in s)
    return 50.0 if hi==lo else 100*(s[-1].c-lo)/(hi-lo)

def candle_shape(c:Candle):
    rng=max(c.h-c.l,1e-12);body=abs(c.c-c.o)
    return body/rng,(c.h-max(c.o,c.c))/rng,(min(c.o,c.c)-c.l)/rng

def analyze(cs:list[Candle],min_score:int=5)->Signal|None:
    # `cs` must contain closed candles only. Never remove the latest candle here.
    if len(cs)<60:return None
    closed=cs;v=[c.c for c in closed];last,prev=closed[-1],closed[-2]
    e5,e13,e21=ema(v,5),ema(v,13),ema(v,21);r=rsi(v);m,ms,_=macd(v);a=atr(closed);bu,bm,bl=bb(v);ax=adx(closed);st=stochastic(closed)
    body,upper,lower=candle_shape(last);score=0;reasons=[]
    if e5 and e13 and e21:
        if e5>e13>e21:score+=2;reasons.append('EMA trend UP')
        elif e5<e13<e21:score-=2;reasons.append('EMA trend DOWN')
        else:reasons.append('EMA mixed')
    if r is not None:
        if 52<=r<=68:score+=1;reasons.append(f'RSI bullish {r:.0f}')
        elif 32<=r<=48:score-=1;reasons.append(f'RSI bearish {r:.0f}')
        elif r>=75:reasons.append(f'RSI overbought {r:.0f}')
        elif r<=25:reasons.append(f'RSI oversold {r:.0f}')
    if m is not None and ms is not None:
        if m>ms and m>0:score+=2;reasons.append('MACD bullish')
        elif m<ms and m<0:score-=2;reasons.append('MACD bearish')
        else:reasons.append('MACD mixed')
    if bm is not None:
        if last.c>bm:score+=1;reasons.append('above BB mid')
        elif last.c<bm:score-=1;reasons.append('below BB mid')
    if ax is not None:reasons.append(f'ADX {"trend" if ax>=25 else "weak"} {ax:.0f}')
    if st is not None:
        if st>85:reasons.append('stoch high')
        elif st<15:reasons.append('stoch low')
    bull=last.c>last.o;bear=last.c<last.o;pbull=prev.c>prev.o;pbear=prev.c<prev.o
    if bull and lower>upper*1.3 and body>0.20:score+=1;reasons.append('bullish rejection')
    if bear and upper>lower*1.3 and body>0.20:score-=1;reasons.append('bearish rejection')
    if bull and pbear and last.o<=prev.c and last.c>=prev.o:score+=2;reasons.append('bullish engulfing')
    if bear and pbull and last.o>=prev.c and last.c<=prev.o:score-=2;reasons.append('bearish engulfing')
    recent=closed[-12:];highs=[x.h for x in recent];lows=[x.l for x in recent];resistance=max(highs[:-1]);support=min(lows[:-1])
    if highs[-1]>max(highs[:-1]):score+=1;reasons.append('higher high')
    if lows[-1]<min(lows[:-1]):score-=1;reasons.append('lower low')
    if a:
        if abs(last.c-resistance)<=max(a*0.35,last.c*1e-5) and last.c<resistance:score-=1;reasons.append('near resistance')
        if abs(last.c-support)<=max(a*0.35,last.c*1e-5) and last.c>support:score+=1;reasons.append('near support')
        if a/last.c<0.00003:reasons.append('very low volatility')
    if body<0.08:reasons.append('small candle')
    sig='UP' if score>=min_score else 'DOWN' if score<=-min_score else 'WAIT'
    return Signal(sig,min(100,int(abs(score)/10*100)),score,tuple(reasons[-8:]),last.c,r,a,e5,e13,e21,m,ms,bu,bm,bl,support,resistance)


def combine_signals(direct: Signal|None, screen_signal: str|None, screen_confidence: int = 0) -> tuple[str, int, str]:
    """Cross-check direct market signal with an optional screen-chart signal.
    The direct market engine remains primary. Screen data is only allowed to
    confirm it; disagreement or weak screen evidence produces WAIT.
    """
    if direct is None:
        return 'WAIT', 0, 'Direct market data not ready.'
    ss=(screen_signal or 'WAIT').upper()
    if ss not in ('UP','DOWN','WAIT'):
        ss='WAIT'
    if ss == 'WAIT' or screen_confidence < 55:
        return direct.signal, direct.strength, 'Direct market primary; screen chart not reliable enough to confirm.'
    if direct.signal == ss and direct.signal != 'WAIT':
        strength=min(100, max(direct.strength, screen_confidence) + 10)
        return direct.signal, strength, 'Direct market + screen chart agree.'
    if direct.signal != 'WAIT' and direct.signal != ss:
        return 'WAIT', min(direct.strength, screen_confidence), 'Direct market and screen chart conflict.'
    return 'WAIT', 0, 'Insufficient agreement.'

def analyze_screen_frame_rgb(rgb, width: int, height: int) -> tuple[str, int, str]:
    """Lightweight chart-color assist. It never replaces OHLC analysis.
    It looks for repeated green/red candle-like vertical regions in the
    supplied RGB frame. Unknown/ambiguous frames return WAIT.
    """
    try:
        import numpy as np
        a=np.asarray(rgb)
        if a.ndim != 3 or a.shape[0] < 40 or a.shape[1] < 40:
            return 'WAIT', 0, 'Screen frame too small.'
        # Ignore UI edges and sample the central chart area.
        y0,y1=int(height*.15),int(height*.82)
        x0,x1=int(width*.05),int(width*.95)
        q=a[y0:y1,x0:x1,:3].astype('int16')
        r,g,b=q[:,:,0],q[:,:,1],q[:,:,2]
        green=((g-r)>28)&((g-b)>8)&(g>75)
        red=((r-g)>28)&((r-b)>8)&(r>75)
        # Count per-column candle-like pixels, then compare recent/right side
        # versus the left side. This is deliberately conservative.
        gs=green.sum(axis=0); rs=red.sum(axis=0)
        mid=max(1,len(gs)//2)
        gl=float(gs[mid:].sum()); gr=float(rs[mid:].sum())
        total=gl+gr
        if total < 80:
            return 'WAIT', 0, 'No reliable candle colors detected.'
        if gl/total >= .62:
            conf=min(85,int(55+35*(gl/total-.62)/.38))
            return 'UP',conf,'Screen chart shows stronger recent bullish candle color.'
        if gr/total >= .62:
            conf=min(85,int(55+35*(gr/total-.62)/.38))
            return 'DOWN',conf,'Screen chart shows stronger recent bearish candle color.'
        return 'WAIT', 40, 'Screen chart colors are mixed.'
    except Exception as e:
        return 'WAIT',0,f'Screen assist unavailable: {e}'
