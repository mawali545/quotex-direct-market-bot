__version__ = '0.4.0'
import asyncio, threading, os, time
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty
from engine import normalize, analyze

KV='''
BoxLayout:
    orientation: 'vertical'
    padding: dp(14)
    spacing: dp(10)
    Label:
        text: 'DIRECT MARKET SIGNAL BOT'
        font_size: '22sp'
        size_hint_y: None
        height: dp(42)
    Label:
        text: 'Live OHLC/WebSocket • Signal only • No auto trade'
        size_hint_y: None
        height: dp(28)
    TextInput:
        id: email
        hint_text: 'Quotex email'
        multiline: False
        password: False
        size_hint_y: None
        height: dp(46)
    TextInput:
        id: password
        hint_text: 'Quotex password (stays on phone)'
        multiline: False
        password: True
        size_hint_y: None
        height: dp(46)
    TextInput:
        id: asset
        text: 'EURUSD_otc'
        hint_text: 'Asset'
        multiline: False
        size_hint_y: None
        height: dp(46)
    Spinner:
        id: period
        text: '60'
        values: ['5','10','15','30','60','120','300','600','900','1800','3600']
        size_hint_y: None
        height: dp(46)
    BoxLayout:
        size_hint_y: None
        height: dp(48)
        spacing: dp(8)
        Button:
            text: 'CONNECT'
            on_release: app.connect()
        Button:
            text: 'STOP'
            on_release: app.stop_bot()
    Label:
        text: app.status
        text_size: self.width, None
        halign: 'center'
        valign: 'middle'
    Label:
        text: app.signal_text
        font_size: '30sp'
        text_size: self.width, None
        halign: 'center'
        valign: 'middle'
    Label:
        text: app.detail_text
        text_size: self.width, self.height
        valign: 'top'
        halign: 'left'
'''

class BotApp(App):
    status=StringProperty('DISCONNECTED')
    signal_text=StringProperty('WAIT')
    detail_text=StringProperty('Enter credentials locally, then CONNECT.')
    def __init__(self,**kw):
        super().__init__(**kw); self.stop_event=threading.Event(); self.thread=None
    def build(self): return Builder.load_string(KV)
    def connect(self):
        if self.thread and self.thread.is_alive(): return
        email=self.root.ids.email.text.strip(); password=self.root.ids.password.text; asset=self.root.ids.asset.text.strip() or 'EURUSD_otc'
        try: period=int(self.root.ids.period.text)
        except: period=60
        if not email or not password:
            self.status='LOGIN REQUIRED'; return
        self.stop_event.clear(); self.status='CONNECTING...'; self.thread=threading.Thread(target=self.worker,args=(email,password,asset,period),daemon=True); self.thread.start()
    def stop_bot(self): self.stop_event.set(); self.status='STOPPING...'; self.signal_text='WAIT'
    def ui(self,status=None,signal=None,detail=None):
        def f(_):
            if status is not None:self.status=status
            if signal is not None:self.signal_text=signal
            if detail is not None:self.detail_text=detail
        Clock.schedule_once(f,0)
    def worker(self,email,password,asset,period):
        try:
            from pyquotex.stable_api import Quotex
            asyncio.run(self.async_worker(Quotex,email,password,asset,period))
        except Exception as e:
            self.ui('ERROR', 'WAIT', repr(e))
    async def async_worker(self,Quotex,email,password,asset,period):
        client=Quotex(email=email,password=password,lang='en',host=os.getenv('QUOTEX_HOST','qxbroker.com'),period_default=period)
        ok,msg=await client.connect()
        if not ok: self.ui('CONNECTION FAILED','WAIT',str(msg)); return
        self.ui('CONNECTED','WAIT','Receiving closed candles...')
        candles=normalize(await client.get_historical_candles(asset,amount_of_seconds=7200,period=period,max_workers=2))
        try:
            await client.start_candles_stream(asset,period)
            last_ts=candles[-1].t if candles else 0
            event_name=f'candle_generated_{asset}_{period}'
            while not self.stop_event.is_set() and await client.check_connect():
                try: msg=await client.api.event_registry.wait_event(event_name,timeout=period+10)
                except TimeoutError: msg=client.api.candle_generated_check[str(asset)].get(period)
                if not msg: continue
                c=normalize([msg])
                if not c or c[0].t<=last_ts: continue
                candles=sorted({x.t:x for x in (candles+c)}.values(),key=lambda x:x.t)[-500:]; last_ts=c[0].t
                s=analyze(candles)
                if s:
                    self.ui('LIVE',s.signal,f'Strength {s.strength}/100 | score {s.score:+d}\nClose: {s.close}\n'+' • '.join(s.reasons))
                else:self.ui('LIVE','WAIT','Need more closed-candle history.')
        except Exception as e:self.ui('LIVE ERROR','WAIT',repr(e))
        finally:
            try: await client.stop_candles_stream(asset)
            except Exception: pass
            await client.close()
            self.ui('DISCONNECTED','WAIT','Bot stopped.')

if __name__=='__main__': BotApp().run()
