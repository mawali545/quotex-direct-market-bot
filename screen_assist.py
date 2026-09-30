"""Screen assist disabled in the direct-market Android build.

The bot now uses direct Quotex market data only, avoiding pyjnius/Pillow/NumPy
Android build dependencies.
"""
class ScreenAssist:
    def __init__(self):
        self.active=False
    def available(self):
        return False
    def start(self):
        return False
    def latest_path(self):
        return None
    def stop(self):
        self.active=False
