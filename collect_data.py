import os
import time
import cv2
import numpy as np
from adb import Device

dev = Device("emulator-5554")
os.makedirs("dataset/images", exist_ok=True)

prev = None
count = len(os.listdir("dataset/images"))

while True:
    img = dev.screenshot()
    small = cv2.resize(img, (64, 36))
    if prev is None or np.mean(cv2.absdiff(small, prev)) > 8:
        cv2.imwrite(f"dataset/images/{count:05d}.png", img)
        count += 1
        prev = small
        print("Đã lưu", count)
    time.sleep(2)