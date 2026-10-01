from dataclasses import dataclass
from math import sqrt
from typing import Any, List

@dataclass
class Candle:
    t:int; o:float; h:float; l:float; c:float

def normalize(x:Any)->Candle:
    if isinstance(x,dict):
        return Candle(int(float(x.get("time",x.get("timestamp",x.get("t",0))))),float(x.get("open",x.get("o"))),float(x.get("high",x.get("h"))),float(x.get("low",x.get("l"))),float(x.get("close",x.get("c"))))
    t,o,c,h,l=x[:5]
    return Candle(int(float(t)),float(o),float(h),float(l),float(c))

def ema(v,n):
    if not v:return 0.0
    k=2/(n+1);e=v[0]
    for x in v[1:]:e=x*k+e*(1-k)
    return e

def rsi(v,n=14):
    if len(v)<=n:return 50.0
    g=[];l=[]
    for i in range(1,len(v)):
        d=v[i]-v[i-1];g.append(max(d,0));l.append(max(-d,0))
    ag=sum(g[-n:])/n;al=sum(l[-n:])/n
    if al==0:return 100.0
    return 100-100/(1+ag/al)

def std(v):
    if not v:return 0.0
    m=sum(v)/len(v);return sqrt(sum((x-m)**2 for x in v)/len(v))

def stochastic(cs,n=14):
    if len(cs)<n:return 50.0,50.0
    ks=[]
    for i in range(n-1,len(cs)):
        hi=max(x.h for x in cs[i-n+1:i+1]);lo=min(x.l for x in cs[i-n+1:i+1])
        ks.append(50 if hi==lo else (cs[i].c-lo)/(hi-lo)*100)
    return ks[-1],sum(ks[-3:])/min(3,len(ks))

def adx(cs,n=14):
    if len(cs)<n+2:return 0.0,0.0
    tr=[];p=[];m=[]
    for i in range(1,len(cs)):
        a,b=cs[i-1],cs[i];tr.append(max(b.h-b.l,abs(b.h-a.c),abs(b.l-a.c)))
        u=b.h-a.h;d=a.l-b.l;p.append(u if u>d and u>0 else 0);m.append(d if d>u and d>0 else 0)
    t=sum(tr[-n:])/n
    if t<=0:return 0.0,0.0
    pdi=sum(p[-n:])/n/t*100;mdi=sum(m[-n:])/n/t*100;den=pdi+mdi
    return (0 if den==0 else abs(pdi-mdi)/den*100),pdi-mdi

def structure(cs):
    if len(cs)<8:return "NEUTRAL"
    hs=[x.h for x in cs[-8:]];ls=[x.l for x in cs[-8:]]
    if hs[-1]>max(hs[:-1]) and ls[-1]>min(ls[:-1]):return "HH/HL"
    if hs[-1]<max(hs[:-1]) and ls[-1]<min(ls[:-1]):return "LH/LL"
    return "MIXED"

def analyze(raw:List[Any]):
    cs=[normalize(x) for x in raw][-200:]
    if len(cs)<35:return {"signal":"WAIT","strength":0,"reason":"Need more live candles","factors":[]}
    cl=[x.c for x in cs];hi=[x.h for x in cs];lo=[x.l for x in cs];last=cs[-1];prev=cs[-2]
    e5,e13,e21=ema(cl,5),ema(cl,13),ema(cl,21);rv=rsi(cl)
    macd=ema(cl,12)-ema(cl,26);ms=[ema(cl[:i+1],12)-ema(cl[:i+1],26) for i in range(26,len(cl))];msig=ema(ms,9) if ms else macd
    mid=sum(cl[-20:])/20;sd=std(cl[-20:]);upper=mid+2*sd;lower=mid-2*sd
    trs=[max(hi[i]-lo[i],abs(hi[i]-cl[i-1]),abs(lo[i]-cl[i-1])) for i in range(1,len(cs))];atr=sum(trs[-14:])/14
    sk,sdv=stochastic(cs);adxv,diff=adx(cs);struct=structure(cs)
    body=abs(last.c-last.o);uw=last.h-max(last.o,last.c);lw=min(last.o,last.c)-last.l;ratio=body/max(last.h-last.l,1e-12)
    score=0;f=[]
    if e5>e13>e21:score+=2;f.append("EMA 5/13/21 bullish")
    elif e5<e13<e21:score-=2;f.append("EMA 5/13/21 bearish")
    else:f.append("EMA mixed")
    if 55<rv<75:score+=1;f.append(f"RSI {rv:.1f} bullish zone")
    elif 25<rv<45:score-=1;f.append(f"RSI {rv:.1f} bearish zone")
    else:f.append(f"RSI {rv:.1f}")
    if macd>msig:score+=1;f.append("MACD bullish")
    elif macd<msig:score-=1;f.append("MACD bearish")
    if last.c>mid:score+=1;f.append("Above Bollinger mid")
    elif last.c<mid:score-=1;f.append("Below Bollinger mid")
    if last.c>=upper:score-=1;f.append("Upper-band caution")
    elif last.c<=lower:score+=1;f.append("Lower-band rebound zone")
    if sk>sdv and sk<80:score+=1;f.append("Stochastic bullish")
    elif sk<sdv and sk>20:score-=1;f.append("Stochastic bearish")
    if adxv>=20:
        score += 1 if diff>0 else -1 if diff<0 else 0;f.append(f"ADX {adxv:.1f} trend strength")
    else:f.append(f"ADX {adxv:.1f} weak trend")
    if struct=="HH/HL":score+=1;f.append("HH/HL structure")
    elif struct=="LH/LL":score-=1;f.append("LH/LL structure")
    else:f.append("Mixed market structure")
    ph=max(hi[-21:-1]);pl=min(lo[-21:-1])
    if last.c>ph:score+=1;f.append("Breakout confirmation")
    elif last.h>ph and last.c<ph:score-=1;f.append("False-breakout rejection")
    elif last.c<pl:score-=1;f.append("Breakdown confirmation")
    elif last.l<pl and last.c>pl:score+=1;f.append("False-breakdown rejection")
    if last.c>last.o and lw>body*1.2:score+=1;f.append("Bullish rejection")
    elif last.c<last.o and uw>body*1.2:score-=1;f.append("Bearish rejection")
    f.append("Strong candle body" if ratio>.65 else "Weak/indecision candle")
    if last.c>last.o and prev.c<prev.o and last.o<=prev.c and last.c>=prev.o:score+=2;f.append("Bullish engulfing")
    elif last.c<last.o and prev.c>prev.o and last.o>=prev.c and last.c<=prev.o:score-=2;f.append("Bearish engulfing")
    mom=(cl[-1]-cl[-6])/max(abs(cl[-6]),1e-12)*100
    if mom>.03:score+=1;f.append(f"Momentum +{mom:.3f}%")
    elif mom<-.03:score-=1;f.append(f"Momentum {mom:.3f}%")
    else:f.append(f"Momentum {mom:+.3f}%")
    if atr<=max(abs(last.c)*.00001,1e-12):return {"signal":"WAIT","strength":35,"reason":"Very low volatility","factors":f}
    sig="UP" if score>=6 else "DOWN" if score<=-6 else "WAIT";strength=min(99,max(0,50+score*5))
    if sig=="WAIT":strength=min(strength,59)
    return {"signal":sig,"strength":strength,"reason":f"{len(f)} confirmations • score {score} • {struct}","factors":f,"rsi":round(rv,1),"macd":macd,"stochastic":round(sk,1),"adx":round(adxv,1),"atr":atr,"support":pl,"resistance":ph}
