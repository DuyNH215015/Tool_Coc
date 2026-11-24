from pathlib import Path
import time

import cv2


class LauncherRecovery:
    def __init__(self):
        template_path = (
            Path(__file__).resolve().parent
            / "screenshots"
            / "man_hinh_chinh.png"
        )
        reference = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
        if reference is None:
            raise FileNotFoundError(f"Không đọc được ảnh mẫu: {template_path}")

        x, y, width, height = 616, 148, 50, 50
        self.icon_template = reference[y:y + height, x:x + width]
        if self.icon_template.shape[:2] != (height, width):
            raise ValueError(f"Ảnh mẫu không đúng kích thước: {template_path}")

    def _find_game_icon(self, screen):
        if (
            screen is None
            or screen.shape[0] < self.icon_template.shape[0]
            or screen.shape[1] < self.icon_template.shape[1]
        ):
            return None

        result = cv2.matchTemplate(
            screen,
            self.icon_template,
            cv2.TM_CCOEFF_NORMED,
        )
        _, confidence, _, location = cv2.minMaxLoc(result)
        if confidence < 0.88:
            return None

        height, width = self.icon_template.shape[:2]
        return location[0] + width // 2, location[1] + height // 2

    def reopen_if_needed(self, device, screen, log):
        icon_center = self._find_game_icon(screen)
        if icon_center is None:
            return False

        log("Phát hiện màn hình chính emulator, đang mở lại Clash of Clans")
        device.tap(*icon_center)

        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            time.sleep(3)
            if self._find_game_icon(device.screenshot()) is None:
                log("Đã mở game, chờ 30 giây để game tải")
                time.sleep(30)
                return True

        raise TimeoutError("Không thể mở Clash of Clans từ màn hình chính emulator")
