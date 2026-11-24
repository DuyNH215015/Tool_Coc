# 4 đoạn thẳng thả quân (tọa độ ảnh 1280x720).
# Chỉnh đường tại file này để bot không phụ thuộc tọa độ trong acc1.py.
DROP_LINES = [
    ((135, 352), (523, 28)),    # 1: trái -> trên
    ((706, 13), (1080, 290)),   # 2: trên -> phải
    ((1109, 350), (906, 531)), # 3: phải -> dưới
    ((130, 352), (307, 460)),  # 4: trái -> dưới
]

DROP_MAX_TAPS = 20  # giới hạn tap tuyệt đối, kể cả khi OCR đọc sai số quân

RAGE_SLOT = (650, 650)          # tọa độ chọn ô Bình Cuồng
RAGE_MAX_DROPS = 5             # số bình muốn thả, tối đa 11
RAGE_DROP_POINTS = [(360, 272),(323, 400) ,(638, 92) ,(977, 420) ,(445, 468) ]            # tối đa 11 điểm, xếp theo từng lượt qua DROP_LINES

DROP_HEROES = True
HERO_COUNT = 3
HERO_SLOT_POINTS = [(346, 647),(447, 647),(547, 650)]            # tọa độ chọn từng tướng trên thanh quân
HERO_DROP_POINTS = [(135, 352),(135, 352),(135, 352)]            # tọa độ thả từng tướng trên chiến trường
HERO_ABILITY_DELAY_SECONDS = 7  # sau bao nhiêu giây từ lúc thả thì bấm lại ô tướng
