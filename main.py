import os
import sys
import cv2
from adb import Device

name = sys.argv[1] if len(sys.argv) > 1 else "a"
os.makedirs("screenshots", exist_ok=True)

img = Device("emulator-5554").screenshot()
path = f"screenshots/{name}.png"
cv2.imwrite(path, img)
print("Kích thước:", img.shape, "| đã lưu", os.path.abspath(path))