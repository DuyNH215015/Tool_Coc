import cv2
import easyocr

_reader = easyocr.Reader(["en"], gpu=False)

def read_text(screen, region, allow="0123456789"):
    """Đọc chuỗi ký tự trong vùng (x, y, w, h)."""
    x, y, w, h = region
    crop = screen[y:y+h, x:x+w]
    crop = cv2.resize(crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    parts = _reader.readtext(crop, allowlist=allow, detail=0)
    return "".join(parts).replace(" ", "")

def read_number(screen, region):
    """Đọc số nguyên trong vùng, ví dụ '25 747 786' -> 25747786."""
    txt = read_text(screen, region, "0123456789")
    return int(txt) if txt.isdigit() else None