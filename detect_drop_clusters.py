import cv2
import numpy as np

im = cv2.imread(r"screenshots/goc_tha_linh.png")
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
mask = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([179, 255, 75]))
num, labels, stats, centers = cv2.connectedComponentsWithStats(mask)

for i in range(1, num):
    x, y, w, h, area = stats[i]
    if area > 20 and y < 600:
        cx, cy = int(centers[i][0]), int(centers[i][1])
        print(area, (cx, cy), (x, y, w, h))
