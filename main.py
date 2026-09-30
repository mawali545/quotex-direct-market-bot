__version__ = "0.6.0"

import asyncio
import threading
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty
from engine import normalize, analyze

KV = '''
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
        text: app.detail_text
        text_size: self.width, self.height
        valign: 'top'
        halign: 'left'
'''

HOSTS = ("qxbroker.com", "quotex.com", "qxbroker.io", "quotex.io", "quotex.sqldb.tc")
USER_AGENT = ("Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/154.0.0.0 Mobile Safari/537.36")

class BotApp(App):
    status = StringProperty("DISCONNECTED")
    signal_text = StringProperty("WAIT")
    detail_text = StringProperty("Enter credentials locally, then CONNECT.")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stop_event = threading.Event()
        self.thread = None

    def build(self):
        return Builder.load_string(KV)

    def connect(self):
        if self.thread and self.thread.is_alive():
            return
        email = self.root.ids.email.text.strip()
        password = self.root.ids.password.text
        asset = self.root.ids.asset.text.strip() or "EURUSD_otc"
        try:
            period = int(self.root.ids.period.text)
        except (TypeError, ValueError):
            period = 60
        if not email or not password:
            self.status = "LOGIN REQUIRED"
            return
        self.stop_event.clear()
        self.status = "CONNECTING..."
        self.signal_text = "WAIT"
        self.detail_text = "Trying Quotex connection..."
        self.thread = threading.Thread(target=self.worker,
                                       args=(email, password, asset, period),
                                       daemon=True)
        self.thread.start()

    def stop_bot(self):
        self.stop_event.set()
        self.status = "STOPPING..."
        self.signal_text = "WAIT"

    def ui(self, status=None, signal=None, detail=None):
        def apply(_):
            if status is not None: self.status = status
            if signal is not None: self.signal_text = signal
            if detail is not None: self.detail_text = detail
        Clock.schedule_once(apply, 0)

    def worker(self, email, password, asset, period):
        try:
            from pyquotex.stable_api import Quotex
            asyncio.run(self.async_worker(Quotex, email, password, asset, period))
        except Exception as exc:
            self.ui("ERROR", "WAIT", f"{type(exc).__name__}: {exc}")

    async def async_worker(self, Quotex, email, password, asset, period):
        client = None
        connected_host = None
        last_error = "Unknown connection error."
        try:
            for host in HOSTS:
                if self.stop_event.is_set():
                    return
                candidate = None
                try:
                    self.ui("CONNECTING...", "WAIT", f"Trying {host}...")
                    candidate = Quotex(email=email, password=password, host=host,
                                      lang="en", user_agent=USER_AGENT,
                                      period_default=period)
                    ok, reason = await candidate.connect()
                    if ok:
                        client = candidate
                        connected_host = host
                        break
                    last_error = str(reason)
                    await candidate.close()
                except Exception as exc:
                    last_error = f"{type(exc).__name__}: {exc}"
                    if candidate is not None:
                        try:
                            await candidate.close()
                        except Exception:
                            pass

            if client is None:
                self.ui("CONNECTION FAILED", "WAIT",
                        "All broker hosts failed.\n" + last_error)
                return

            self.ui("CONNECTED", "WAIT",
                    f"Host: {connected_host}\nLoading closed-candle history...")
            raw = await client.get_historical_candles(
                asset, amount_of_seconds=max(7200, period * 120),
                period=period, max_workers=2)
            candles = normalize(raw)
            await client.start_candles_stream(asset, period)
            last_ts = candles[-1].t if candles else 0
            event_name = f"candle_generated_{asset}_{period}"

            while not self.stop_event.is_set() and await client.check_connect():
                try:
                    msg = await client.api.event_registry.wait_event(
                        event_name, timeout=period + 10)
                except TimeoutError:
                    try:
                        msg = client.api.candle_generated_check[str(asset)].get(period)
                    except Exception:
                        msg = None
                if not msg:
                    continue
                new = normalize([msg])
                if not new:
                    continue
                candle = new[-1]
                if candle.t <= last_ts:
                    continue
                merged = {c.t: c for c in candles + new}
                candles = sorted(merged.values(), key=lambda c: c.t)[-500:]
                last_ts = candle.t
                signal = analyze(candles)
                if signal is None:
                    self.ui("LIVE", "WAIT", "Need more closed-candle history.")
                else:
                    details = (f"Host: {connected_host}\nPeriod: {period}s | Close: {signal.close}\n"
                               f"Strength: {signal.strength}/100 | score: {signal.score:+d}\n" +
                               " • ".join(signal.reasons))
                    self.ui("LIVE", signal.signal, details)
        except Exception as exc:
            self.ui("LIVE ERROR", "WAIT", f"{type(exc).__name__}: {exc}")
        finally:
            if client is not None:
                try: await client.stop_candles_stream(asset, period)
                except Exception: pass
                try: await client.close()
                except Exception: pass
            if not self.stop_event.is_set():
                self.ui("DISCONNECTED", "WAIT", "Connection ended.")

if __name__ == "__main__":
    BotApp().run()
