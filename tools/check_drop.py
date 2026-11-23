import importlib
import random
import sys
from pathlib import Path

import cv2

from bot import Bot


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Cách dùng: python -m tools.check_drop acc1")

    cfg = importlib.import_module(f"accounts.{sys.argv[1]}")
    image_path = Path("screenshots/khu_vuc_attack.png")
    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(f"Không đọc được ảnh: {image_path}")
    if image.shape[1] != 1280 or image.shape[0] != 720:
        raise ValueError(f"Ảnh phải là 1280x720, hiện tại: {image.shape[1]}x{image.shape[0]}")

    bot = Bot.__new__(Bot)
    bot.c = cfg

    for start, end in cfg.DROP_LINES:
        cv2.line(image, start, end, (255, 255, 255), 1, cv2.LINE_AA)

    preview_taps = 40
    pass_counts = [0] * len(cfg.DROP_LINES)
    previous_points = [None] * len(cfg.DROP_LINES)
    spacing = getattr(cfg, "DROP_PASS_SPACING", 50)
    if spacing <= 0:
        raise AssertionError("DROP_PASS_SPACING phải > 0")

    for _ in range(preview_taps):
        for segment_index, (start, end) in enumerate(cfg.DROP_LINES):
            x1, y1 = start
            x2, y2 = end
            length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
            pass_index = pass_counts[segment_index]

            if length <= 0:
                x, y = x1, y1
            else:
                max_distance = int(length // spacing) * spacing
                distance = pass_index * spacing
                cycle_length = 2 * max_distance
                if cycle_length > 0:
                    cycle_position = distance % cycle_length
                    distance = cycle_position if cycle_position <= max_distance \
                        else cycle_length - cycle_position
                t = distance / length
                x = int(round(x1 + (x2 - x1) * t))
                y = int(round(y1 + (y2 - y1) * t))

            pass_counts[segment_index] += 1
            previous = previous_points[segment_index]
            if previous is not None:
                gap = ((x - previous[0]) ** 2 + (y - previous[1]) ** 2) ** 0.5
                if abs(gap - spacing) > 1.5:
                    raise AssertionError(
                        f"Đường {segment_index + 1}: khoảng cách thực tế {gap:.1f}px, "
                        f"không bằng config {spacing}px"
                    )
            previous_points[segment_index] = (x, y)
            cv2.circle(image, (x, y), 2, (0, 0, 255), -1, cv2.LINE_AA)

    output_path = Path("screenshots/drop_preview.png")
    if not cv2.imwrite(str(output_path), image):
        raise OSError(f"Không lưu được ảnh: {output_path}")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
