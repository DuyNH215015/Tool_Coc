from pathlib import Path

# ---------- Nút thanh toán và xác nhận ----------
PAY_WITH_GOLD = (708, 570)
PAY_WITH_ELIXIR = (848, 570)
CONFIRM = (897, 620)                          # nút xác nhận nâng tường
CONFIRM_PRICE_REGION = (800, 620, 160, 36)
CONFIRM_CLOSE = (1131, 55)                    # nút X đóng popup

# ---------- Ngưỡng nâng tường ----------
WALL_MIN_GOLD = 10_000_000
WALL_MIN_ELIXIR = 10_000_000
WALL_MAX_PRICE = 20_000_000
MAX_WALLS_PER_CYCLE = 10 # số tường tối đa được nâng trong mỗi chu kỳ
RESOURCE_OCR_EVERY_BATTLES = 10 # đánh bao nhiêu trận thì đọc lại số tài nguyên, tránh OCR sai do số thay đổi
WALL_STATE_FILE = str(Path(__file__).with_name("wall_state.json"))

# ---------- Khu vực và mật độ quét ----------
WALL_POINTS = [(255, 252), (512, 55), (644, 155), (382, 354)]
WALL_SCAN_ROWS = 24
WALL_SCAN_COLUMNS = 24

# ---------- Vùng OCR giá ----------
GOLD_PRICE_REGION = (645, 505, 130, 28)
ELIXIR_PRICE_REGION = (785, 505, 130, 28)
