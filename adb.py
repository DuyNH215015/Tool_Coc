import subprocess
import numpy as np
import cv2
import random
import time

ADB_PATH = r"F:\LDPlayer\LDPlayer14\adb.exe"

class Device:
    def __init__(self, serial):
        self.serial = serial

    def _adb(self, *args, capture=False):
        cmd = [ADB_PATH, "-s", self.serial, *args]
        return subprocess.run(cmd, capture_output=capture, check=True).stdout

    def screenshot(self):
        data = self._adb("exec-out", "screencap", "-p", capture=True)
        return cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)

    def tap(self, x, y):
        self._adb("shell", "input", "tap", str(x), str(y))

    def swipe(self, x1, y1, x2, y2, duration=300):
        self._adb("shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration))

    def back(self):
        self._adb("shell", "input", "keyevent", "4")

    def tap_continuous(self, count=200, points=None):
        if points is None:
            points = [
                (180, 260, 50, 60),   # góc trái-trên
                (1100, 260, 50, 60),  # góc phải-trên
                (640, 500, 160, 40),  # góc dưới giữa
            ]

        for i in range(count):
            cx, cy, rx, ry = points[i % len(points)]
            x = cx + random.randint(-rx, rx)
            y = cy + random.randint(-ry, ry)
            self.tap(x, y)
            time.sleep(random.uniform(0.035, 0.075))