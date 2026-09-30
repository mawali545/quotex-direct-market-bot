__version__='1.0.0'
import asyncio, threading
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from engine import analyze

PERIODS=['5','10','15','30','60','120','300','600','900','1800','3600','7200','14400','86400']
PAIRS=['NZDCAD_otc','EURUSD_otc','GBPUSD_otc','USDJPY_otc','AUDUSD_otc','EURUSD','GBPUSD','USDJPY','AUDUSD','NZDUSD']
HOSTS=['qxbroker.com','quotex.com','qxbroker.io','quotex.io']
UA='Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 Chrome/154.0.0.0 Mobile Safari/537.36'

class AMH110(App):
    def build(self):
        self.stop_flag=True; self.loop=None; self.client=None; self.candles=[]
        root=BoxLayout(orientation='vertical',padding=dp(10),spacing=dp(8))
        title=Label(text='[b]AMH110[/b]\nAI MARKET SIGNAL',markup=True,font_size='26sp',size_hint_y=None,height=dp(70))
        root.add_widget(title)
        top=GridLayout(cols=2,spacing=dp(6),size_hint_y=None,height=dp(110))
        self.email=TextInput(hint_text='Quotex email',multiline=False,password=False)
        self.password=TextInput(hint_text='Quotex password',multiline=False,password=True)
        top.add_widget(self.email); top.add_widget(self.password)
        self.pair=Spinner(text=PAIRS[0],values=PAIRS)
        self.period=Spinner(text='60',values=PERIODS)
        top.add_widget(self.pair); top.add_widget(self.period)
        root.add_widget(top)
        self.status=Label(text='READY — SELECT PAIR & PERIOD',font_size='16sp',size_hint_y=None,height=dp(42))
        root.add_widget(self.status)
        self.signal=Label(text='WAIT',font_size='46sp',bold=True,size_hint_y=None,height=dp(90))
        root.add_widget(self.signal)
        self.strength=Label(text='Analysis strength: --%',font_size='19sp',size_hint_y=None,height=dp(45))
        root.add_widget(self.strength)
        self.details=Label(text='Waiting for live market data…',font_size='14sp',halign='left',valign='top')
        root.add_widget(self.details)
        buttons=BoxLayout(size_hint_y=None,height=dp(58),spacing=dp(8))
        self.connect_btn=Button(text='CONNECT & ANALYZE')
        self.connect_btn.bind(on_release=lambda *_: self.start())
        self.stop_btn=Button(text='STOP')
        self.stop_btn.bind(on_release=lambda *_: self.stop())
        buttons.add_widget(self.connect_btn); buttons.add_widget(self.stop_btn)
        root.add_widget(buttons)
        return root

    def set_status(self,s): Clock.schedule_once(lambda dt:setattr(self.status,'text',s),0)
    def render(self,r):
        def f(_):
            self.signal.text=r['signal']; self.strength.text=f"Analysis strength: {r['strength']}%"; self.details.text='\n'.join(r.get('factors',[])[:10]) or r.get('reason','WAIT')
        Clock.schedule_once(f,0)
    def start(self):
        if not self.email.text.strip() or not self.password.text:
            self.set_status('ENTER LOCAL QUOTEX LOGIN FIRST'); return
        self.stop_flag=False; self.connect_btn.disabled=True; self.set_status('ANALYZING MARKET…')
        threading.Thread(target=self.worker,daemon=True).start()
    def stop(self):
        self.stop_flag=True; self.connect_btn.disabled=False; self.set_status('STOPPED'); self.signal.text='WAIT'
    def worker(self):
        try:
            from pyquotex.stable_api import Quotex
            period=int(self.period.text); asset=self.pair.text
            for host in HOSTS:
                if self.stop_flag:return
                try:
                    self.set_status('CONNECTING: '+host)
                    q=Quotex(email=self.email.text.strip(),password=self.password.text,host=host,lang='en',user_agent=UA)
                    self.loop=asyncio.new_event_loop(); asyncio.set_event_loop(self.loop)
                    ok=self.loop.run_until_complete(q.connect())
                    if ok:
                        self.client=q; self.set_status('CONNECTED — ANALYZING '+asset)
                        data=self.loop.run_until_complete(q.get_historical_candles(asset, max(7200,period*120), period=period, max_workers=2))
                        self.candles=list(data or [])[-200:]
                        self.render(analyze(self.candles))
                        # Conservative polling fallback; avoids fake 5/10-second candles.
                        while not self.stop_flag:
                            asyncio.sleep(0)
                            new=self.loop.run_until_complete(q.get_historical_candles(asset, max(7200,period*120), period=period, max_workers=2))
                            if new:
                                self.candles=list(new)[-200:]; self.set_status('ANALYZING MARKET…'); self.render(analyze(self.candles))
                            import time; time.sleep(min(max(period,5),60))
                        try:self.loop.run_until_complete(q.close())
                        except Exception:pass
                        return
                except Exception as e:
                    self.set_status('RETRYING BROKER HOST…')
            self.set_status('CONNECTION FAILED — CHECK NETWORK / LOGIN')
        finally:
            self.connect_btn.disabled=False

if __name__=='__main__': AMH110().run()
