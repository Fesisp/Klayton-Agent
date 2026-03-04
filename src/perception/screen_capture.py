import mss
import numpy as np
import cv2
from src.utils.window_handler import WindowHandler

class ScreenCapture:
    def __init__(self, config=None):
        self.cfg = config or {}
        window_title = self.cfg.get('screen', {}).get('window_title', 'PokeOne')
        self.win_handler = WindowHandler(window_title=window_title)
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[1] if len(self.sct.monitors) > 1 else self.sct.monitors[0]

    def capture(self):
        rect = self.win_handler.get_window_rect()
        if rect:
            wx, wy, ww, wh = rect
            monitor = {
                "top": int(wy),
                "left": int(wx),
                "width": int(ww),
                "height": int(wh),
            }
            screenshot = self.sct.grab(monitor)
        else:
            screenshot = self.sct.grab(self.monitor)
        img = np.array(screenshot)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def capture_roi(self, roi_pct):
        """
        Captura uma região específica usando porcentagens (0.0 a 1.0).
        roi_pct = {"top": 0.1, "left": 0.2, "width": 0.1, "height": 0.05}
        """
        rect = self.win_handler.get_window_rect()
        if not rect:
            return None

        wx, wy, ww, wh = rect

        monitor = {
            "top": int(wy + (roi_pct["top"] * wh)),
            "left": int(wx + (roi_pct["left"] * ww)),
            "width": int(roi_pct["width"] * ww),
            "height": int(roi_pct["height"] * wh)
        }

        img = np.array(self.sct.grab(monitor))
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)