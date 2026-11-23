import cv2
import numpy as np


def find(screen, template_path, threshold=0.85):
    """Trả về (x, y) tâm của ảnh mẫu, hoặc None nếu không thấy."""
    tpl = cv2.imread(template_path)
    if tpl is None:
        return None
    if tpl.shape[0] > screen.shape[0] or tpl.shape[1] > screen.shape[1]:
        return None

    res = cv2.matchTemplate(screen, tpl, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    if max_val < threshold:
        return None

    h, w = tpl.shape[:2]
    return (max_loc[0] + w // 2, max_loc[1] + h // 2)


def wall_candidates(screen, limit=60):
    """Tìm các ứng viên nằm trên cạnh tường bằng Hough lines."""
    gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=35,
                            minLineLength=35, maxLineGap=10)
    if lines is None:
        return []

    h, w = screen.shape[:2]
    found = []
    for line in lines.reshape(-1, 4):
        x1, y1, x2, y2 = map(int, line)
        dx, dy = x2 - x1, y2 - y1
        length = float(np.hypot(dx, dy))
        angle = abs(np.degrees(np.arctan2(dy, dx)))
        if not ((20 <= angle <= 55) or (125 <= angle <= 160)):
            continue

        steps = max(1, int(length // 24))
        for step in range(steps + 1):
            ratio = step / steps
            x = int(round(x1 + dx * ratio))
            y = int(round(y1 + dy * ratio))
            if int(w * 0.10) <= x <= int(w * 0.90) and int(h * 0.18) <= y <= int(h * 0.78):
                found.append((length, (x, y)))

    found.sort(reverse=True)
    candidates = []
    for _, point in found:
        if all((point[0] - cx) ** 2 + (point[1] - cy) ** 2 >= 26 ** 2
               for cx, cy in candidates):
            candidates.append(point)
            if len(candidates) >= limit:
                break
    return candidates


def wall_menu_state(screen, upgradeable_template, max_template):
    """So khớp vùng nút nâng cấp: 1=cần nâng; 0=đã tối đa; None=không phải tường."""
    if screen.shape[:2] != (720, 1280):
        screen = cv2.resize(screen, (1280, 720))

    regions = (
        (350, 465, 580, 255),
        (795, 495, 145, 145),
        (650, 495, 180, 145),
    )

    scores = []
    for x, y, w, h in regions:
        crop = screen[y:y+h, x:x+w]

        def region_similarity(template_path):
            template = cv2.imread(template_path)
            if template is None:
                return -1.0
            template = cv2.resize(template, (1280, 720))
            return float(cv2.matchTemplate(
                crop,
                template[y:y+h, x:x+w],
                cv2.TM_CCOEFF_NORMED
            ).max())

        scores.append((region_similarity(upgradeable_template),
                       region_similarity(max_template)))

    menu_up, menu_max = scores[0]
    button_up, button_max = scores[1]
    elixir_up, elixir_max = scores[2]

    if button_up >= 0.88 and button_up >= button_max + 0.10:
        return 1, button_up
    if button_max >= 0.88 and button_max >= button_up + 0.10:
        return 0, button_max
    if menu_up >= 0.76 and menu_up >= menu_max + 0.10:
        return 1, menu_up
    if elixir_up >= 0.88 and elixir_up >= elixir_max + 0.10:
        return 1, elixir_up
    return None, max(button_up, button_max, menu_up, menu_max, elixir_up, elixir_max)