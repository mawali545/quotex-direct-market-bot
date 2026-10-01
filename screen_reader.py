"""Real Android screen/chart reader.

Uses MediaProjection + ImageReader through PyJNIus. It does NOT invent candles.
It only reports a chart observation when enough repeated colored candle bodies are
found in a stable chart-like region. The reader is deliberately conservative:
no usable frame => WAIT.
"""
from __future__ import annotations

import math
import struct
import time
from typing import Any


class AndroidChartReader:
    REQUEST_CODE = 1101

    def __init__(self, on_observation):
        self.on_observation = on_observation
        self.running = False
        self.thread = None
        self.projection = None
        self.reader = None
        self.virtual_display = None
        self.width = 0
        self.height = 0
        self.density = 1

    @staticmethod
    def available() -> bool:
        try:
            import jnius  # noqa: F401
            from android import activity  # noqa: F401
            return True
        except Exception:
            return False

    def request_permission(self, activity_obj):
        from jnius import autoclass
        Context = autoclass("android.content.Context")
        MediaProjectionManager = autoclass("android.media.projection.MediaProjectionManager")
        mgr = activity_obj.getSystemService(Context.MEDIA_PROJECTION_SERVICE)
        intent = mgr.createScreenCaptureIntent()
        activity_obj.startActivityForResult(intent, self.REQUEST_CODE)

    def start(self, activity_obj, result_code, data_intent):
        self.stop()
        from jnius import autoclass
        DisplayMetrics = autoclass("android.util.DisplayMetrics")
        Context = autoclass("android.content.Context")
        MediaProjectionManager = autoclass("android.media.projection.MediaProjectionManager")
        PixelFormat = autoclass("android.graphics.PixelFormat")
        ImageReader = autoclass("android.media.ImageReader")
        DisplayManager = autoclass("android.hardware.display.DisplayManager")

        mgr = activity_obj.getSystemService(Context.MEDIA_PROJECTION_SERVICE)
        self.projection = mgr.getMediaProjection(result_code, data_intent)
        if self.projection is None:
            raise RuntimeError("SCREEN CAPTURE NOT GRANTED")

        metrics = DisplayMetrics()
        activity_obj.getWindowManager().getDefaultDisplay().getRealMetrics(metrics)
        self.width = int(metrics.widthPixels)
        self.height = int(metrics.heightPixels)
        self.density = int(metrics.densityDpi)
        self.reader = ImageReader.newInstance(
            self.width, self.height, PixelFormat.RGBA_8888, 2
        )
        flags = DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR
        self.virtual_display = self.projection.createVirtualDisplay(
            "AMH110ChartReader",
            self.width,
            self.height,
            self.density,
            flags,
            self.reader.getSurface(),
            None,
            None,
        )
        self.running = True
        import threading
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        for obj_name in ("virtual_display", "reader", "projection"):
            obj = getattr(self, obj_name, None)
            if obj is not None:
                try:
                    if obj_name == "virtual_display": obj.release()
                    elif obj_name == "reader": obj.close()
                    else: obj.stop()
                except Exception:
                    pass
            setattr(self, obj_name, None)

    def _read_rgba(self, image):
        planes = image.getPlanes()
        if not planes:
            return None
        plane = planes[0]
        buf = plane.getBuffer()
        pixel_stride = int(plane.getPixelStride())
        row_stride = int(plane.getRowStride())
        row_padding = max(0, row_stride - pixel_stride * self.width)
        raw_len = int(buf.remaining())
        data = bytearray(raw_len)
        buf.get(data)
        return data, pixel_stride, row_stride, row_padding

    def _pixel(self, data, ps, rs, x, y):
        idx = y * rs + x * ps
        if idx + 3 >= len(data):
            return 0, 0, 0, 0
        return data[idx], data[idx + 1], data[idx + 2], data[idx + 3]

    @staticmethod
    def _is_green(r, g, b):
        return g > 125 and g > r * 1.18 and g > b * 1.05 and (g - min(r, b)) > 30

    @staticmethod
    def _is_red(r, g, b):
        return r > 125 and r > g * 1.25 and r > b * 1.10 and (r - min(g, b)) > 35

    def _observe(self, data, ps, rs):
        # Quotex layouts vary by phone. Search the central 55% of the screen,
        # excluding the top header and bottom controls where possible.
        x0 = int(self.width * 0.05); x1 = int(self.width * 0.95)
        y0 = int(self.height * 0.16); y1 = int(self.height * 0.70)
        step_x = max(3, self.width // 180)
        step_y = max(3, self.height // 240)

        green = []
        red = []
        for y in range(y0, y1, step_y):
            for x in range(x0, x1, step_x):
                r, g, b, _ = self._pixel(data, ps, rs, x, y)
                if self._is_green(r, g, b): green.append((x, y))
                elif self._is_red(r, g, b): red.append((x, y))

        total = len(green) + len(red)
        if total < 40:
            return {"valid": False, "reason": "No stable colored candle bodies detected"}

        # Group detections into x-columns. A real candle body occupies multiple
        # nearby samples at roughly the same x coordinate.
        cols = {}
        for x, y in green + red:
            k = int(x / max(4, step_x * 2))
            cols.setdefault(k, {"green": 0, "red": 0, "ys": []})
            cols[k]["ys"].append(y)
        candidates = []
        for k, v in cols.items():
            if len(v["ys"]) < 3:
                continue
            # classify by local counts in a small x bucket
            cx = k * max(4, step_x * 2)
            gc = sum(1 for x, y in green if abs(x - cx) <= step_x * 2)
            rc = sum(1 for x, y in red if abs(x - cx) <= step_x * 2)
            if max(gc, rc) < 3:
                continue
            direction = "UP" if gc >= rc else "DOWN"
            candidates.append((cx, min(v["ys"]), max(v["ys"]), direction))

        candidates.sort(key=lambda z: z[0])
        if len(candidates) < 5:
            return {"valid": False, "reason": "Too few candle-like columns"}
        recent = candidates[-12:]
        up = sum(1 for c in recent if c[3] == "UP")
        down = len(recent) - up
        bias = "UP" if up > down else "DOWN" if down > up else "WAIT"
        agreement = int(round(max(up, down) / len(recent) * 100))
        return {
            "valid": True,
            "signal": bias,
            "agreement": agreement,
            "candle_columns": len(candidates),
            "recent_up": up,
            "recent_down": down,
            "region": [x0, y0, x1, y1],
        }

    def _loop(self):
        while self.running:
            image = None
            try:
                image = self.reader.acquireLatestImage() if self.reader else None
                if image is not None:
                    payload = self._read_rgba(image)
                    if payload:
                        data, ps, rs, _ = payload
                        obs = self._observe(data, ps, rs)
                        obs["ts"] = time.time()
                        self.on_observation(obs)
            except Exception as exc:
                self.on_observation({"valid": False, "reason": f"Chart reader error: {exc}"})
            finally:
                if image is not None:
                    try: image.close()
                    except Exception: pass
            time.sleep(0.8)
