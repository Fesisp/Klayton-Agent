import mss
import numpy as np
import cv2

class ScreenCapture:
    def __init__(self, config=None):
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[1] # Default to primary monitor

    def capture(self):
        screenshot = self.sct.grab(self.monitor)
        img = np.array(screenshot)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)