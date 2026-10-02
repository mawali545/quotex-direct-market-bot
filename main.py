__version__ = "3.0.0"

import asyncio
import socket
import threading
import time
from typing import Any

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView

from engine import analyze
from screen_reader import AndroidChartReader

PERIODS = ["5", "10", "15", "30", "60", "120", "300", "600", "900", "1800", "3600", "7200", "14400", "86400"]
DURATIONS = ["5", "10", "15", "30", "60"]
HOSTS = ["qxbroker.com", "quotex.com", "qxbroker.io", "quotex.io"]
UA = "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 Chrome/154.0.0.0 Mobile Safari/537.36"
BG = (.025, .032, .052, 1)
CARD = (.055, .072, .105, 1)
MUTED = (.55, .61, .72, 1)
TEXT = (.94, .96, 1, 1)
UP = (.25, .90, .55, 1)
DOWN = (1, .35, .45, 1)


class Card(BoxLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(*CARD)
            self.bg = RoundedRectangle(radius=[dp(16)])
        self.bind(pos=self.sync, size=self.sync)

    def sync(self, *_):
        self.bg.pos, self.bg.size = self.pos, self.size


class ChartWidget(Widget):
    candles = ListProperty([])

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self.redraw, size=self.redraw, candles=self.redraw)

    def redraw(self, *_):
        self.canvas.clear()
        if not self.candles:
            return
        cs = self.candles[-45:]
        lo = min(float(c["low"]) for c in cs)
        hi = max(float(c["high"]) for c in cs)
        span = max(hi - lo, 1e-12)
        px, py = dp(12), dp(12)
        step = max((self.width - 2 * px) / len(cs), dp(5))

        def yp(v):
            return self.y + py + (v - lo) / span * (self.height - 2 * py)

        with self.canvas:
            Color(.12, .16, .24, 1)
            for i in range(1, 4):
                y = self.y + py + (self.height - 2 * py) * i / 4
                Line(points=[self.x + px, y, self.right - px, y], width=.6)
            for i, c in enumerate(cs):
                o, h, l, cl = map(float, (c["open"], c["high"], c["low"], c["close"]))
                x = self.x + px + (i + .5) * step
                Color(*(UP if cl >= o else DOWN))
                Line(points=[x, yp(l), x, yp(h)], width=1)
                body = max(dp(2), abs(yp(cl) - yp(o)))
                Rectangle(pos=(x - step * .3, min(yp(o), yp(cl))), size=(step * .6, body))


class OverlayController:
    """Real Android WindowManager overlay. No fake UI fallback is presented as overlay."""

    def __init__(self, app):
        self.app = app
        self.activity = None
        self.window = None
        self.text = None
        self.ready = False

    def _ui(self, fn):
        if self.activity is None:
            return
        try:
            from jnius import PythonJavaClass, java_method

            class Run(PythonJavaClass):
                __javainterfaces__ = ["java/lang/Runnable"]

                def __init__(self, callback):
                    super().__init__()
                    self.callback = callback

                @java_method("()V")
                def run(self):
                    self.callback()

            self.activity.runOnUiThread(Run(fn))
        except Exception:
            try:
                fn()
            except Exception:
                pass

    def has_permission(self):
        try:
            from jnius import autoclass
            Settings = autoclass("android.provider.Settings")
            return bool(Settings.canDrawOverlays(self.activity))
        except Exception:
            return False

    def request_permission(self):
        from jnius import autoclass
            
        Settings = autoclass("android.provider.Settings")
        Intent = autoclass("android.content.Intent")
        Uri = autoclass("android.net.Uri")
        intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:" + self.activity.getPackageName()))
        self.activity.startActivity(intent)

    def show(self):
        if self.activity is None:
            return False
        if not self.has_permission():
            self.app.status_text("OVERLAY PERMISSION REQUIRED")
            self.request_permission()
            return False
        try:
            from jnius import autoclass
            Context = autoclass("android.content.Context")
            WindowManager = autoclass("android.view.WindowManager")
            Gravity = autoclass("android.view.Gravity")
            PixelFormat = autoclass("android.graphics.PixelFormat")
            TextView = autoclass("android.widget.TextView")
            GradientDrawable = autoclass("android.graphics.drawable.GradientDrawable")

            wm = self.activity.getSystemService(Context.WINDOW_SERVICE)
            tv = TextView(self.activity)
            tv.setTextColor(0xFFF2F5FF)
            tv.setTextSize(11)
            tv.setPadding(4, 4, 4, 4)
            tv.setGravity(Gravity.CENTER)
            tv.setText("AMH")
            bg = GradientDrawable()
            bg.setColor(0xEE14508A)
            bg.setCornerRadius(200.0)
            bg.setStroke(3, 0xFF65B8FF)
            tv.setBackground(bg)

            size = int(self.app.dp_to_px(58))
            if self.app.android_api >= 26:
                wtype = WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
            else:
                wtype = WindowManager.LayoutParams.TYPE_PHONE
            flags = (
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                | WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
            )
            params = WindowManager.LayoutParams(size, size, wtype, flags, PixelFormat.TRANSLUCENT)
            params.gravity = Gravity.RIGHT | Gravity.CENTER_VERTICAL
            params.x = int(self.app.dp_to_px(8))
            params.y = int(self.app.dp_to_px(0))
            wm.addView(tv, params)
            self.window, self.text, self.ready = wm, tv, True
            return True
        except Exception as exc:
            self.app.status_text("OVERLAY ERROR  •  " + str(exc)[:100])
            return False

    def update(self, signal, direct, screen, strength, status):
        if not self.ready or self.text is None:
            return
        msg = f"AMH110  •  {signal}\\nDIRECT: {direct}   CHART: {screen}\\nSTRENGTH: {strength}%\\n{status}"
        self._ui(lambda: self.text.setText(msg))

    def hide(self):
        if self.window is not None and self.text is not None:
            try:
                self.window.removeView(self.text)
            except Exception:
                pass
        self.window = self.text = None
        self.ready = False


class AMH110(App):
    def build(self):
        self.stop_flag = True
        self.loop = None
        self.client = None
        self.candles = []
        self.current_asset = ""
        self.available_pairs = ["CONNECT FIRST"]
        self.screen_obs = {"valid": False, "signal": "WAIT", "agreement": 0}
        self.android_api = 35
        self.overlay = OverlayController(self)
        self.reader = None
        self.capture_requested = False

        # One-screen mobile layout: no scrolling on the main face.
        root = FloatLayout()
        with root.canvas.before:
            Color(*BG)
            self.bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda *_: setattr(self.bg, "pos", root.pos),
                  size=lambda *_: setattr(self.bg, "size", root.size))

        content = BoxLayout(
            orientation="vertical",
            padding=(dp(7), dp(6), dp(7), dp(5)),
            spacing=dp(4),
            size_hint=(1, 1),
        )
        root.add_widget(content)

        header = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(5))
        header.add_widget(Label(text="[b]AMH110[/b]", markup=True, font_size="19sp",
                                size_hint_x=.34, color=TEXT))
        header.add_widget(Label(text="QUOTEX LIVE  •  DIRECT + CHART",
                                font_size="8sp", size_hint_x=.66, color=MUTED))
        content.add_widget(header)

        auth = Card(orientation="vertical", padding=dp(6), spacing=dp(4),
                    size_hint_y=None, height=dp(86))
        g = GridLayout(cols=2, spacing=dp(5), size_hint_y=None, height=dp(34))
        self.email = TextInput(hint_text="Quotex ID / Email", multiline=False, font_size="12sp")
        self.password = TextInput(hint_text="Password", multiline=False, password=True, font_size="12sp")
        g.add_widget(self.email); g.add_widget(self.password); auth.add_widget(g)
        self.connect_btn = Button(text="CONNECT • LIVE", size_hint_y=None, height=dp(37),
                                  font_size="14sp", background_normal="",
                                  background_color=(.10, .36, .62, 1), bold=True)
        self.connect_btn.bind(on_release=lambda *_: self.start())
        auth.add_widget(self.connect_btn)
        content.add_widget(auth)

        settings = Card(orientation="vertical", padding=dp(5), size_hint_y=None, height=dp(58))
        g = GridLayout(cols=3, spacing=dp(5))
        self.pair = Spinner(text=self.available_pairs[0], values=self.available_pairs,
                            font_size="9sp", shorten=True)
        self.period = Spinner(text="CANDLE 10s",
                              values=["CANDLE " + x + "s" for x in PERIODS],
                              font_size="9sp")
        self.duration = Spinner(text="TRADE 10s",
                                values=["TRADE " + x + "s" for x in DURATIONS],
                                font_size="9sp")
        g.add_widget(self.pair); g.add_widget(self.period); g.add_widget(self.duration)
        settings.add_widget(g)
        content.add_widget(settings)

        tools = Card(orientation="horizontal", padding=dp(4), spacing=dp(5),
                     size_hint_y=None, height=dp(40))
        self.overlay_btn = Button(text="● OVERLAY", font_size="10sp",
                                  background_normal="", background_color=(.14, .22, .35, 1), bold=True)
        self.overlay_btn.bind(on_release=lambda *_: self.enable_overlay())
        self.demo_btn = Button(text="WAIT IF UNCERTAIN", font_size="10sp",
                               background_normal="", background_color=(.18, .18, .24, 1), bold=True)
        tools.add_widget(self.overlay_btn); tools.add_widget(self.demo_btn)
        content.add_widget(tools)

        st = Card(orientation="vertical", padding=dp(5), spacing=dp(1),
                  size_hint_y=None, height=dp(48))
        self.status = Label(text="READY • CONNECT THEN ENABLE OVERLAY",
                            font_size="9sp", color=TEXT)
        self.payout = Label(text="PAYOUT  —", font_size="8sp", color=MUTED)
        st.add_widget(self.status); st.add_widget(self.payout)
        content.add_widget(st)

        ch = Card(orientation="vertical", padding=dp(4), size_hint_y=None, height=dp(105))
        ch.add_widget(Label(text="LIVE QUOTEX OHLC • PRIMARY SOURCE",
                            font_size="9sp", color=MUTED, size_hint_y=None, height=dp(17)))
        self.chart = ChartWidget()
        ch.add_widget(self.chart)
        content.add_widget(ch)

        sig = Card(orientation="vertical", padding=dp(5), spacing=dp(0),
                   size_hint_y=None, height=dp(104))
        self.phase = Label(text="WAITING FOR VERIFIED DATA", font_size="8sp",
                           color=MUTED, size_hint_y=None, height=dp(16))
        self.signal = Label(text="WAIT", font_size="34sp", bold=True, color=TEXT,
                            size_hint_y=None, height=dp(43))
        self.strength = Label(text="ANALYSIS STRENGTH  —%", font_size="9sp",
                              color=MUTED, size_hint_y=None, height=dp(18))
        self.reason = Label(text="No live OHLC + chart confirmation = no signal.",
                            font_size="8sp", color=MUTED)
        for x in (self.phase, self.signal, self.strength, self.reason):
            sig.add_widget(x)
        content.add_widget(sig)

        content.add_widget(Label(text="SIGNALS ONLY • NO AUTO-TRADING • DEMO FIRST",
                                 font_size="7sp", color=MUTED, size_hint_y=None, height=dp(14)))

        # OTP is an overlay card, not part of the vertical layout.
        otp = Card(orientation="vertical", padding=dp(8), spacing=dp(5),
                   size_hint=(.88, None), height=dp(128),
                   pos_hint={"center_x": .5, "center_y": .56},
                   opacity=0)
        self.otp_card = otp
        self.otp_msg = Label(text="QUOTEX AUTHENTICATION CODE",
                             font_size="10sp", color=TEXT,
                             size_hint_y=None, height=dp(24))
        self.otp_input = TextInput(hint_text="Enter authentication code",
                                   multiline=False, input_filter="int",
                                   font_size="15sp", size_hint_y=None, height=dp(38))
        self.otp_btn = Button(text="VERIFY CODE", font_size="13sp",
                              size_hint_y=None, height=dp(38),
                              background_normal="", background_color=(.10, .36, .62, 1))
        self.otp_btn.bind(on_release=self._submit_otp)
        otp.add_widget(self.otp_msg); otp.add_widget(self.otp_input); otp.add_widget(self.otp_btn)
        root.add_widget(otp)

        try:
            from android import activity
            activity.bind(on_activity_result=self._on_activity_result)
        except Exception:
            pass
        return root

    @property
    def android_api(self):
        try:
            from jnius import autoclass
            Build = autoclass("android.os.Build")
            return int(Build.VERSION.SDK_INT)
        except Exception:
            return 35

    @android_api.setter
    def android_api(self, value):
        self._android_api = value

    def dp_to_px(self, value):
        try:
            from kivy.core.window import Window
            return value * (Window.dpi / 160.0)
        except Exception:
            return value * 3

    def status_text(self, text):
        Clock.schedule_once(lambda dt: setattr(self.status, "text", text), 0)

    def phase_text(self, text):
        Clock.schedule_once(lambda dt: setattr(self.phase, "text", text), 0)

    def render(self, result):
        def f(_):
            direct = result.get("signal", "WAIT")
            screen = self.screen_obs.get("signal", "WAIT") if self.screen_obs.get("valid") else "WAIT"
            if direct in {"UP", "DOWN"} and screen == direct:
                final = direct
                strength = min(int(result.get("strength", 0)), int(self.screen_obs.get("agreement", 0)))
                reason = "DIRECT OHLC + visible chart agree"
            else:
                final = "WAIT"
                strength = min(int(result.get("strength", 0)), 59)
                reason = "WAIT: direct OHLC and visible chart are not both confirmed"
            self.signal.text = final
            self.strength.text = f"ANALYSIS STRENGTH  {strength}%"
            self.reason.text = reason
            self.chart.candles = result.get("candles", self.candles[-45:])
            self.overlay.update(final, direct, screen, strength, reason)
        Clock.schedule_once(f, 0)

    def enable_overlay(self):
        try:
            from jnius import autoclass
            self.overlay.activity = autoclass("org.kivy.android.PythonActivity").mActivity
            if not self.overlay.has_permission():
                self.overlay.request_permission()
                self.status_text("ANDROID SETTINGS OPENED  •  ALLOW DISPLAY OVER OTHER APPS")
                return
            if self.overlay.show():
                self.status_text("OVERLAY ACTIVE  •  NOW OPEN QUOTEX")
            if AndroidChartReader.available() and not self.capture_requested:
                self.capture_requested = True
                self.reader = AndroidChartReader(self.on_screen_observation)
                self.reader.request_permission(self.overlay.activity)
                self.status_text("SCREEN CAPTURE REQUESTED  •  ALLOW TO READ QUOTEX CHART")
        except Exception as exc:
            self.status_text("ANDROID FEATURE ERROR  •  " + str(exc)[:110])

    def _on_activity_result(self, request_code, result_code, data):
        if request_code != AndroidChartReader.REQUEST_CODE:
            return
        if result_code == -1 and data is not None and self.reader is not None:
            try:
                self.reader.start(self.overlay.activity, result_code, data)
                self.status_text("CHART READER LIVE  •  OPEN QUOTEX")
            except Exception as exc:
                self.status_text("CHART READER ERROR  •  " + str(exc)[:110])
        else:
            self.status_text("SCREEN CAPTURE DENIED  •  SIGNALS REMAIN WAIT")

    def on_screen_observation(self, obs):
        if not obs.get("valid"):
            self.screen_obs = {"valid": False, "signal": "WAIT", "agreement": 0}
            return
        self.screen_obs = obs
        Clock.schedule_once(lambda dt: self.render(self.last_result) if hasattr(self, "last_result") else None, 0)

    def _show_otp(self, prompt):
        self.otp_msg.text = "QUOTEX AUTH CODE  •  " + str(prompt)[:70]
        self.otp_input.text = ""
        self.otp_card.height = dp(118)
        self.otp_card.opacity = 1
        self.otp_input.focus = True

    def _hide_otp(self):
        self.otp_card.height = 0
        self.otp_card.opacity = 0

    def _submit_otp(self, *_):
        code = self.otp_input.text.strip()
        if code:
            self.otp_result["code"] = code
            self.otp_done.set()
            self._hide_otp()
            self.status_text("AUTH CODE RECEIVED  •  CONTINUING LOGIN")

    def request_otp(self, prompt):
        self.otp_done = threading.Event()
        self.otp_result = {"code": ""}
        Clock.schedule_once(lambda dt: self._show_otp(prompt), 0)
        self.status_text("QUOTEX AUTH CODE REQUIRED  •  CHECK YOUR EMAIL")
        if not self.otp_done.wait(180):
            Clock.schedule_once(lambda dt: self._hide_otp(), 0)
            self.status_text("AUTH CODE TIMEOUT  •  CONNECT AGAIN")
            return "0"
        return self.otp_result["code"] or "0"

    def start(self):
        if not self.email.text.strip() or not self.password.text:
            self.status_text("LOGIN REQUIRED  •  ENTER ID + PASSWORD")
            return
        if self.pair.text == "CONNECT FIRST":
            self.status_text("CONNECTING  •  LIVE PAIRS WILL LOAD AFTER LOGIN")
        self.stop_flag = False
        self.connect_btn.disabled = True
        self.phase_text("CONNECTING  •  VERIFYING QUOTEX DATA")
        threading.Thread(target=self.worker, daemon=True).start()

    def worker(self):
        try:
            from pyquotex.stable_api import Quotex
            from pyquotex.network.login import Login
            requested_asset = self.pair.text if self.pair.text not in {"CONNECT FIRST", "AUTO"} else ""
            period = int(self.period.text.split()[-1].rstrip("s"))
            trade_duration = int(self.duration.text.split()[-1].rstrip("s"))

            for host in HOSTS:
                if self.stop_flag:
                    return
                self.loop = None
                self.client = None
                try:
                    self.status_text("DNS / SSL CHECK  •  " + host)
                    socket.gethostbyname(host)
                    self.status_text("LOGIN / WEBSOCKET  •  " + host)
                    # The pinned PyQuotex revision keeps Login URLs as class attributes.
                    # Set them per selected host so the fallback hosts are real fallbacks.
                    Login.base_url = host
                    Login.https_base_url = f"https://{host}"
                    q = Quotex(
                        email=self.email.text.strip(),
                        password=self.password.text,
                        host=host,
                        lang="en",
                        user_agent=UA,
                        asset_default=requested_asset or "EURUSD",
                        period_default=period,
                        on_otp_callback=self.request_otp,
                    )
                    self.loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(self.loop)
                    q.set_account_mode("PRACTICE")
                    ok, reason = self.loop.run_until_complete(q.connect())
                    if not ok:
                        raise RuntimeError(reason or "LOGIN FAILED")
                    self.client = q
                    self.status_text("CONNECTED  •  LOADING REAL QUOTEX INSTRUMENTS")

                    instruments = self.loop.run_until_complete(q.get_instruments(timeout=15))
                    pairs = []
                    for item in instruments or []:
                        if isinstance(item, (list, tuple)) and len(item) > 2:
                            asset = str(item[1])
                            display = str(item[2]).replace("\\n", " ").strip()
                            if asset:
                                pairs.append(asset)
                    pairs = sorted(set(pairs))
                    if not pairs:
                        raise RuntimeError("NO LIVE QUOTEX INSTRUMENTS RECEIVED")
                    asset = requested_asset if requested_asset in pairs else self.pick_asset(pairs)
                    self.available_pairs = pairs
                    Clock.schedule_once(lambda dt, ps=pairs, a=asset: self._set_pairs(ps, a), 0)
                    self.current_asset = asset

                    try:
                        payout = q.get_payout_by_asset(asset)
                        payout_text = payout.get("1M") if isinstance(payout, dict) else payout
                        Clock.schedule_once(lambda dt, p=payout_text: setattr(self.payout, "text", f"PAYOUT  {p}%" if p is not None else "PAYOUT  —"), 0)
                    except Exception:
                        pass

                    history = self.loop.run_until_complete(
                        q.get_historical_candles(asset, amount_of_seconds=max(1800, period * 100), period=period, timeout=15, max_workers=2)
                    )
                    if not history or len(history) < 35:
                        raise RuntimeError("LIVE OHLC INSUFFICIENT / TIMEOUT")
                    self.candles = list(history)[-240:]
                    self.status_text(f"LIVE OHLC  •  {asset}  •  {period}s")
                    self.phase_text("ANALYZING MARKET  •  DIRECT + CHART CROSS-CHECK")

                    self.loop.run_until_complete(q.start_candles_stream(asset, period))
                    last_render = 0.0
                    while not self.stop_flag:
                        if not self.loop.run_until_complete(q.check_connect()):
                            raise ConnectionError("WEBSOCKET DISCONNECTED")
                        rt = self.loop.run_until_complete(q.get_realtime_candles(asset))
                        merged = self.merge_realtime(self.candles, rt, period)
                        if len(merged) >= 35:
                            self.candles = merged[-240:]
                            result = analyze(self.candles)
                            result["candles"] = self.candles[-45:]
                            self.last_result = result
                            self.render(result)
                            if time.time() - last_render > 4:
                                self.status_text(f"LIVE VERIFIED  •  {asset}  •  {len(self.candles)} candles")
                                last_render = time.time()
                        time.sleep(0.6)
                    try:
                        self.loop.run_until_complete(q.stop_candles_stream(asset))
                    except Exception:
                        pass
                    try:
                        self.loop.run_until_complete(q.close())
                    except Exception:
                        pass
                    return
                except Exception as exc:
                    self.status_text(self.classify(exc) + "  •  " + str(exc)[:105])
                    try:
                        if self.client and self.loop:
                            self.loop.run_until_complete(self.client.close())
                    except Exception:
                        pass
                    time.sleep(1.2)
            self.phase_text("WAIT  •  LIVE DATA NOT VERIFIED")
            self.signal_text_safe("WAIT")
        except Exception as exc:
            self.status_text(self.classify(exc) + "  •  " + str(exc)[:110])
        finally:
            Clock.schedule_once(lambda dt: setattr(self.connect_btn, "disabled", False), 0)

    @staticmethod
    def pick_asset(pairs):
        preferred = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "EURUSD_otc", "GBPUSD_otc"]
        for p in preferred:
            if p in pairs:
                return p
        return pairs[0]

    @staticmethod
    def merge_realtime(history, realtime, period):
        out = {int(float(c.get("time", 0))): c for c in history if isinstance(c, dict) and "time" in c}
        if isinstance(realtime, dict):
            vals = list(realtime.values())
        else:
            vals = realtime if isinstance(realtime, list) else []
        for item in vals:
            if isinstance(item, dict):
                try:
                    ts = int(float(item.get("time", item.get("timestamp", item.get("t")))))
                    o = float(item.get("open", item.get("o")))
                    h = float(item.get("high", item.get("h")))
                    l = float(item.get("low", item.get("l")))
                    c = float(item.get("close", item.get("c")))
                    out[ts] = {"time": ts, "open": o, "high": h, "low": l, "close": c}
                except Exception:
                    continue
        return [out[k] for k in sorted(out)]

    def _set_pairs(self, pairs, selected):
        self.pair.values = pairs
        self.pair.text = selected

    def signal_text_safe(self, text):
        Clock.schedule_once(lambda dt: setattr(self.signal, "text", text), 0)

    @staticmethod
    def classify(exc):
        s = f"{type(exc).__name__}: {exc}".lower()
        if "ssl" in s or "certificate" in s or "tls" in s:
            return "SSL/TLS ERROR"
        if "timeout" in s or "timed out" in s:
            return "NETWORK TIMEOUT"
        if "reset" in s or "connection" in s or "websocket" in s:
            return "NETWORK/WEBSOCKET ERROR"
        if "login" in s or "password" in s or "credential" in s:
            return "LOGIN FAILED"
        if "module" in s or "import" in s:
            return "APP DEPENDENCY ERROR"
        if "instrument" in s or "asset" in s:
            return "QUOTEX ASSET DATA ERROR"
        return "CONNECTION ERROR"

    def stop(self):
        self.stop_flag = True
        try:
            if self.reader:
                self.reader.stop()
        except Exception:
            pass
        try:
            self.overlay.hide()
        except Exception:
            pass
        self.connect_btn.disabled = False
        self.status_text("STOPPED  •  WAIT")
        self.signal_text_safe("WAIT")

    def on_stop(self):
        self.stop()


if __name__ == "__main__":
    AMH110().run()
