import cv2
from adb import Device

screen = Device("emulator-5554").screenshot()
title = "Click de lay toa do - nhan Q de thoat"

def on_click(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"({x}, {y})")

cv2.imshow(title, screen)
cv2.setMouseCallback(title, on_click)
while cv2.waitKey(50) != ord("q"):
    pass
cv2.destroyAllWindows()