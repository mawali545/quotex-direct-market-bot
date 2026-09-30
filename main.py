__version__ = '0.5.9'
import asyncio, threading, os, time
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty
from engine import normalize, analyze, combine_signals, analyze_screen_frame_rgb
from screen_assist import ScreenAssist

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
    Spinner:
        id: asset
        text: 'EURUSD_otc'
        values: ['EURUSD_otc','GBPUSD_otc','USDJPY_otc','AUDUSD_otc','USDCAD_otc','USDCHF_otc','EURGBP_otc','EURJPY_otc','GBPJPY_otc','NZDUSD_otc','EURUSD','GBPUSD','USDJPY','AUDUSD','USDCAD','USDCHF','EURGBP','EURJPY','GBPJPY','NZDUSD']
        size_hint_y: None
        height: dp(46)
    Spinner:
        id: period
        text: '60'
        values: ['5','10','15','30','60','120','300','600','900','1800','3600','7200','14400','86400']
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
        text: app.screen_text
        text_size: self.width, None
        halign: 'center'
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
    screen_text=StringProperty('Screen chart assist: OFF')
    def __init__(self,**kw):
        super().__init__(**kw); self.stop_event=threading.Event(); self.thread=None; self.screen=ScreenAssist(); self.screen_enabled=False
    def build(self): return Builder.load_string(KV)
    def connect(self):
        if self.thread and self.thread.is_alive(): return
        email=self.root.ids.email.text.strip(); password=self.root.ids.password.text; asset=self.root.ids.asset.text.strip() or 'EURUSD_otc'
        try: period=int(self.root.ids.period.text)
        except: period=60
        if not email or not password:
            self.status='LOGIN REQUIRED'; return
        self.stop_event.clear(); self.status='CONNECTING...'; self.thread=threading.Thread(target=self.worker,args=(email,password,asset,period),daemon=True); self.thread.start()
    def stop_bot(self):
        self.stop_event.set(); self.status='STOPPING...'; self.signal_text='WAIT'
    def toggle_screen(self, active):
        self.screen_enabled = False
        self.screen_text = 'Screen chart assist: OFF (direct market mode)'

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
        native_period = period
        # Android/mobile networks can reset a TLS connection to one Quotex
        # hostname while another supported hostname is reachable. Try the
        # configured host first, then the documented alternate hosts.
        configured = os.getenv('QUOTEX_HOST', '').strip()
        hosts = [configured] if configured else []
        for h in ('qxbroker.com', 'quotex.com', 'qxbroker.io', 'quotex.io', 'qxbroker.sqldb.tc'):
            if h not in hosts:
                hosts.append(h)

        # A normal browser UA is supported by the current PyQuotex API and is
        # preferable to its old placeholder UA on mobile networks.
        user_agent = (
            'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/154.0.0.0 Mobile Safari/537.36'
        )

        client = None
        ok = False
        msg = 'Connection failed.'
        tried = []
        for host in hosts:
            if self.stop_event.is_set():
                return
            for attempt in range(1, 3):
                if self.stop_event.is_set():
                    return
                self.ui('CONNECTING...', 'WAIT', f'Connecting to {host} (try {attempt}/2)...')
                current = None
                ok = False
                try:
                    current = Quotex(
                        email=email, password=password, lang='en',
                        host=host, user_agent=user_agent,
                        period_default=native_period
                    )
                    ok, msg = await current.connect()
                    if ok:
                        client = current
                        break
                    tried.append(f'{host} try {attempt}: {msg}')
                except Exception as ex:
                    tried.append(f'{host} try {attempt}: {type(ex).__name__}: {ex}')
                    msg = str(ex)
                finally:
                    if current is not None and not ok:
                        try:
                            await current.close()
                        except Exception:
                            pass
                if attempt < 2:
                    await asyncio.sleep(1.5)
            if client is not None:
                break

        if not ok or client is None:
            detail = ' | '.join(tried[-6:]) if tried else str(msg)
            self.ui('CONNECTION FAILED', 'WAIT', detail)
            return

        self.ui('CONNECTED', 'WAIT', f'Receiving {period}s closed candles via {client.host}...')
        raw=normalize(await client.get_historical_candles(asset,amount_of_seconds=7200,period=native_period,max_workers=2))
        candles = raw
        try:
            await client.start_candles_stream(asset,native_period)
            last_ts=candles[-1].t if candles else 0
            event_name=f'candle_generated_{asset}_{native_period}'
            while not self.stop_event.is_set() and await client.check_connect():
                try: msg=await client.api.event_registry.wait_event(event_name,timeout=native_period+10)
                except TimeoutError: msg=client.api.candle_generated_check[str(asset)].get(native_period)
                if not msg: continue
                c=normalize([msg])
                if not c: continue
                if c[0].t<=last_ts: continue
                candles=sorted({x.t:x for x in (candles+c)}.values(),key=lambda x:x.t)[-500:]
                last_ts=c[0].t
                s=analyze(candles)
                if s:
                    ss='WAIT'; sc=0; sd='Screen assist off.'
                    # Screen assist is disabled in this Android build to keep the
                    # APK free of pyjnius/Pillow/NumPy dependency issues.
                    final_sig,final_strength,cross=combine_signals(s,ss,sc)
                    self.ui('LIVE',final_sig,f'Strength {final_strength}/100 | direct {s.signal} | screen {ss}\nClose: {s.close}\n{cross}\n{sd}\n'+' • '.join(s.reasons))
                else:self.ui('LIVE','WAIT','Need more closed-candle history.')
        except Exception as e:self.ui('LIVE ERROR','WAIT',repr(e))
        finally:
            try: await client.stop_candles_stream(asset,native_period)
            except Exception: pass
            await client.close()
            self.ui('DISCONNECTED','WAIT','Bot stopped.')

if __name__=='__main__': BotApp().run()
