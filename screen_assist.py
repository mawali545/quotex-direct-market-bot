"""Android screen-chart assist bridge.

The Java helper captures the visible display after the user grants Android's
MediaProjection permission. This module keeps capture optional so the direct
market-data path continues to work if screen capture is unavailable.
"""
import os
try:
    from jnius import autoclass
except Exception:
    autoclass=None

class ScreenAssist:
    def __init__(self):
        self.active=False
        self.path=os.path.join(os.getcwd(),'screen_assist.jpg')
        self.helper=None
    def available(self):
        return autoclass is not None
    def start(self):
        if not self.available(): return False
        try:
            Helper=autoclass('org.directmarketsignal.ScreenCapture')
            self.helper=Helper
            Helper.requestPermission()
            self.active=True
            return True
        except Exception:
            return False
    def latest_path(self):
        return self.path if os.path.exists(self.path) else None
    def stop(self):
        try:
            if self.helper: self.helper.stop()
        except Exception: pass
        self.active=False
