
import cv2

IMAGE_PATH = "screenshots/debug_confirm.png"

img = cv2.imread(IMAGE_PATH)

if img is None:
    raise FileNotFoundError(IMAGE_PATH)

print("Kéo chuột để chọn vùng OCR, nhấn ENTER để xác nhận.")
print("Nhấn ESC để thoát.")

region = cv2.selectROI(
    "Select OCR Region",
    img,
    fromCenter=False,
    showCrosshair=True
)

x, y, w, h = map(int, region)

print(f"REGION = ({x}, {y}, {w}, {h})")

cv2.destroyAllWindows()

# Lưu ảnh crop để kiểm tra
crop = img[y:y+h, x:x+w]
cv2.imwrite("screenshots/selected_region.png", crop)
