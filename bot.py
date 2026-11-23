import json
import random
import time
import math
from pathlib import Path

import cv2
import ocr
import vision
from adb import Device


class Bot:
    def __init__(self, cfg):
        """Store the account configuration and connect to its Android device."""
        self.c = cfg
        self.dev = Device(cfg.DEVICE)
        state = self._load_wall_state()
        battle_count = state.get("battles_since_resource_ocr", 0)
        if not isinstance(battle_count, int) or isinstance(battle_count, bool) or battle_count < 0:
            self.log("Bộ đếm trận trong cache tường không hợp lệ, bắt đầu lại từ 0")
            battle_count = 0
        self._battles_since_resource_ocr = battle_count

    def log(self, msg):
        """Print a message prefixed with the configured account name."""
        print(f"[{self.c.NAME}] {msg}")

    def tap(self, pos, delay=1.0):
        """Tap near a screen position, then wait with a small randomized delay."""
        # lệch ngẫu nhiên vài pixel và thời gian chờ để giống người hơn
        x = pos[0] + random.randint(-3, 3)
        y = pos[1] + random.randint(-3, 3)
        self.dev.tap(x, y)
        time.sleep(delay + random.uniform(0, 0.5))

    # ---------- Đọc thông tin ----------
    def read_resources(self):
        """Read home gold and elixir several times and return their medians."""
        results = []
        max_resource = self.c.MAX_RESOURCE_OCR
        invalid_reads = 0

        for attempt in range(5):
            screen = self.dev.screenshot()
            gold = ocr.read_number(screen, self.c.HOME_GOLD)
            elixir = ocr.read_number(screen, self.c.HOME_ELIXIR)

            if (
                (gold is not None and gold > max_resource)
                or (elixir is not None and elixir > max_resource)
            ):
                invalid_reads += 1
                self.log(
                    f"OCR tài nguyên vượt {max_resource:,}, đọc lại "
                    f"({attempt + 1}/5): vàng={gold}, elixir={elixir}"
                )
                time.sleep(0.3)
                continue

            if gold is not None and elixir is not None:
                results.append((gold, elixir))

            time.sleep(0.3)

        if not results:
            if invalid_reads:
                raise RuntimeError(
                    f"OCR tài nguyên liên tục vượt MAX_RESOURCE_OCR={max_resource:,}"
                )
            return 0, 0

        gold_values = [x[0] for x in results]
        elixir_values = [x[1] for x in results]

        return sorted(gold_values)[len(gold_values) // 2], \
            sorted(elixir_values)[len(elixir_values) // 2]

    # ---------- Trạng thái trận ----------
    def in_battle(self):
        """Đã vào trận khi đọc được chiến lợi phẩm vàng."""
        screen = self.dev.screenshot()
        return ocr.read_number(screen, self.c.ENEMY_GOLD) is not None

    def wait_for_battle(self, timeout=45):
        """Poll for battle HUD detection until timeout; return whether it appeared."""
        for _ in range(timeout // 3):
            if self.in_battle():
                return True
            time.sleep(3)
        return False

    def good_target(self):
        """Save the current opponent screenshot and test its OCR loot threshold."""
        screen = self.dev.screenshot()
        cv2.imwrite("screenshots/debug_target.png", screen)
        gold = ocr.read_number(screen, self.c.ENEMY_GOLD)
        elixir = ocr.read_number(screen, self.c.ENEMY_ELIXIR)
        self.log(f"Đối thủ: vàng={gold} elixir={elixir}")
        if gold is None or elixir is None:
            return False
        return gold >= self.c.MIN_LOOT or elixir >= self.c.MIN_LOOT

    def end_battle(self):
        """Đầu hàng, xác nhận nếu có popup, rồi trở về làng."""
        self.tap(self.c.SURRENDER, 1.5)
        surrender_confirm = getattr(self.c, "SURRENDER_CONFIRM", None)
        if surrender_confirm is not None:
            self.tap(surrender_confirm, 3)
        self.tap(self.c.RETURN_HOME, 5)

    def goblins_left(self):
        """Đọc số Goblin còn lại; trả None nếu OCR không đọc được."""
        screen = self.dev.screenshot()
        return ocr.read_number(screen, self.c.GOBLIN_COUNT_REGION)

    def line_drop_points(self, start, end, count=None, safe_margin=None):
        """Nội suy điểm đều trên đoạn thẳng và né khoảng an toàn ở hai đầu."""
        safe_margin = safe_margin if safe_margin is not None else self.c.EDGE_SAFE_MARGIN
        spacing = getattr(
            self.c,
            "DROP_PASS_SPACING",
            50,
        )
        if spacing <= 0:
            raise ValueError("DROP_PASS_SPACING phải > 0")

        x1, y1 = start
        x2, y2 = end
        length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        if count is None:
            margin_ratio = min(safe_margin / length, 0.45) if length else 0
            usable_length = length * (1 - 2 * margin_ratio)
            count = max(2, int(usable_length / spacing) + 1)

        if length <= 0 or count <= 1:
            return [(int((x1 + x2) / 2), int((y1 + y2) / 2))]

        margin = min(safe_margin / length, 0.45)
        points = []
        for i in range(count):
            t = margin + i * (1 - 2 * margin) / (count - 1)
            x = int(round(x1 + (x2 - x1) * t))
            y = int(round(y1 + (y2 - y1) * t))
            points.append((x, y))
        return points

    def drop_all_goblins(self):
        """Thả xen kẽ 4 đường, lặp dọc đường và dừng theo OCR Goblin."""
        rage_points = self.c.RAGE_DROP_POINTS
        max_rage_drops = int(self.c.RAGE_MAX_DROPS)
        if max_rage_drops < 0 or max_rage_drops > 11:
            raise ValueError("RAGE_MAX_DROPS phải từ 0 đến 11")
        if not isinstance(rage_points, list):
            raise ValueError("RAGE_DROP_POINTS phải là danh sách tọa độ")
        if len(rage_points) > 11:
            raise ValueError("RAGE_DROP_POINTS tối đa 11 tọa độ")
        for point in rage_points:
            if (
                not isinstance(point, (tuple, list))
                or len(point) != 2
                or not all(isinstance(value, int) for value in point)
            ):
                raise ValueError("Mỗi điểm RAGE_DROP_POINTS phải là (x, y)")

        rage_drops = min(max_rage_drops, len(rage_points))
        if rage_drops:
            self.log(
                f"Config yêu cầu {max_rage_drops} Bình Cuồng, "
                f"có {len(rage_points)} điểm; sẽ thả {rage_drops}"
            )
        else:
            self.log("Chưa cấu hình điểm thả Bình Cuồng hoặc số bình bằng 0")

        drop_lines = list(self.c.DROP_LINES)
        hero_count = 0
        hero_slot_points = []
        hero_drop_points = []
        hero_ability_delay = float(self.c.HERO_ABILITY_DELAY_SECONDS)
        if hero_ability_delay < 0:
            raise ValueError("HERO_ABILITY_DELAY_SECONDS phải >= 0")
        if self.c.DROP_HEROES:
            hero_count = int(self.c.HERO_COUNT)
            if hero_count < 0 or hero_count > min(4, len(drop_lines)):
                raise ValueError("HERO_COUNT phải từ 0 đến 4 đường thả")
            hero_slot_points = self.c.HERO_SLOT_POINTS
            hero_drop_points = self.c.HERO_DROP_POINTS
            if not isinstance(hero_slot_points, list) or not isinstance(hero_drop_points, list):
                raise ValueError("HERO_SLOT_POINTS và HERO_DROP_POINTS phải là danh sách")
            if len(hero_slot_points) < hero_count or len(hero_drop_points) < hero_count:
                raise ValueError(
                    "Cần cấu hình đủ tọa độ ô chọn và điểm thả cho HERO_COUNT"
                )
            for point in hero_slot_points[:hero_count] + hero_drop_points[:hero_count]:
                if (
                    not isinstance(point, (tuple, list))
                    or len(point) != 2
                    or not all(isinstance(value, int) for value in point)
                ):
                    raise ValueError("Mỗi tọa độ tướng phải có dạng (x, y)")
            self.log(f"Đã bật thả {hero_count} tướng theo config")

        hero_deployed_at = {}
        hero_abilities_used = set()

        def activate_due_hero_abilities(wait_for_due=False):
            while True:
                now = time.monotonic()
                for hero_index, deployed_at in list(hero_deployed_at.items()):
                    if (
                        hero_index not in hero_abilities_used
                        and now - deployed_at >= hero_ability_delay
                    ):
                        self.dev.tap(*hero_slot_points[hero_index])
                        time.sleep(0.1)
                        self.dev.tap(*self.c.SLOT_GOBLIN)
                        time.sleep(0.1)
                        hero_abilities_used.add(hero_index)
                        self.log(f"Đã kích hoạt chiêu tướng {hero_index + 1}")

                if not wait_for_due or len(hero_abilities_used) == len(hero_deployed_at):
                    return

                next_due = min(
                    deployed_at + hero_ability_delay
                    for hero_index, deployed_at in hero_deployed_at.items()
                    if hero_index not in hero_abilities_used
                )
                time.sleep(min(max(0, next_due - time.monotonic()), 0.1))

        self.tap(self.c.SLOT_GOBLIN, 0.5)
        empty_reads = 0
        stop_deploying = False
        ocr_interval = getattr(self.c, "DROP_OCR_CHECK_INTERVAL", 25)
        ocr_interval = max(1, int(ocr_interval))
        max_taps = int(self.c.DROP_MAX_TAPS)
        if max_taps <= 0:
            raise ValueError("DROP_MAX_TAPS phải > 0")
        pass_counts = [0] * len(drop_lines)
        index = 0

        while index < max_taps and not stop_deploying:
            for segment_index, (start, end) in enumerate(drop_lines):
                if index >= max_taps:
                    break

                pass_index = pass_counts[segment_index]
                x1, y1 = start
                x2, y2 = end
                length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                spacing = getattr(
                    self.c,
                    "DROP_PASS_SPACING",
                    50,
                )
                if spacing <= 0:
                    raise ValueError("DROP_PASS_SPACING phải > 0")

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
                index += 1
                x = max(0, min(1279, x))
                y = max(0, min(719, y))
                self.dev.tap(x, y)
                time.sleep(random.uniform(0.035, 0.075))

                rage_point_index = pass_index * len(drop_lines) + segment_index
                if rage_point_index < rage_drops:
                    rage_x, rage_y = self.c.RAGE_SLOT
                    rage_drop_x, rage_drop_y = rage_points[rage_point_index]
                    self.dev.tap(rage_x, rage_y)
                    time.sleep(0.1)
                    self.dev.tap(rage_drop_x, rage_drop_y)
                    time.sleep(0.1)
                    self.dev.tap(*self.c.SLOT_GOBLIN)
                    time.sleep(0.1)

                if pass_index == 0 and segment_index < hero_count:
                    self.dev.tap(*hero_slot_points[segment_index])
                    time.sleep(0.1)
                    self.dev.tap(*hero_drop_points[segment_index])
                    time.sleep(0.1)
                    self.dev.tap(*self.c.SLOT_GOBLIN)
                    time.sleep(0.1)
                    hero_deployed_at[segment_index] = time.monotonic()

                activate_due_hero_abilities()

                if index % ocr_interval == 0:
                    left = self.goblins_left()
                    self.log(f"Đã tap {index}, goblin còn: {left}")
                    if left is not None and left <= 0:
                        empty_reads += 1
                        if empty_reads >= 2:
                            self.log("OCR báo hết Goblin, dừng thả")
                            stop_deploying = True
                            break
                    else:
                        empty_reads = 0

            if stop_deploying:
                break

        activate_due_hero_abilities(wait_for_due=True)

        if index >= max_taps and empty_reads < 2:
            self.log(f"Đạt giới hạn DROP_MAX_TAPS={max_taps}, dừng thả")

    # ---------- Farm ----------
    def farm_attack(self):
        """Search for loot, deploy Goblins, and finish one battle.

        Returns True when a battle was completed or explicitly ended, and False
        when the battle could not be entered or was lost during matchmaking.
        """
        self.log("Đi đánh")

        # 1. Mở menu Chiến đấu, bấm Tìm trận.
        #    Bấm thêm "Tấn công!" phòng khi game mở màn Quân đội.
        self.tap(self.c.ATTACK_BUTTON, 3)
        self.tap(self.c.FIND_MATCH, 3)
        self.tap(self.c.ARMY_ATTACK, 3)

        # 2. Chờ vào trận
        if not self.wait_for_battle():
            self.log("Không vào được trận, thoát")
            self.tap(self.c.SEARCH_CANCEL, 3)
            return False

        # 3. Tìm đối thủ đủ loot
        found = False
        for i in range(self.c.MAX_NEXT):
            if self.good_target():
                found = True
                break
            self.log(f"Bỏ qua, Next lần {i + 1}")
            self.tap(self.c.NEXT_BUTTON, 5)
            if not self.wait_for_battle(30):
                self.log("Mất trận sau khi Next, thoát")
                self.tap(self.c.SEARCH_CANCEL, 3)
                return False

        if not found:
            self.log("Không có mục tiêu đủ loot, kết thúc trận")
            self.end_battle()
            return True

        # 4. Thả hết goblin dọc viền
        self.log("Thả goblin")
        battle_wait = random.randint(
            self.c.MIN_BATTLE_SECONDS,
            self.c.MAX_BATTLE_SECONDS,
        )
        deploy_started = time.monotonic()
        self.drop_all_goblins()

        elapsed = time.monotonic() - deploy_started
        remaining = max(0, battle_wait - elapsed)
        self.log(f"Thời gian trận random: {battle_wait}s, đã thả: {elapsed:.1f}s, chờ thêm: {remaining:.1f}s")
        time.sleep(remaining)

        # 5. Kết thúc và về làng
        self.end_battle()
        self.log("Xong 1 trận")
        return True

    # ---------- Up tường ----------
    def wall_scan_points(self):
        """Tạo lưới quét qua lại bên trong bốn góc cụm tường đã cấu hình."""
        corners = self.c.WALL_POINTS
        center_x = sum(point[0] for point in corners) / len(corners)
        center_y = sum(point[1] for point in corners) / len(corners)
        ordered = sorted(
            corners,
            key=lambda point: math.atan2(point[1] - center_y, point[0] - center_x),
        )
        top_index = min(range(len(ordered)), key=lambda index: ordered[index][1])
        ordered = ordered[top_index:] + ordered[:top_index]

        top_left, top_right, bottom_right, bottom_left = ordered
        rows = self.c.WALL_SCAN_ROWS
        columns = self.c.WALL_SCAN_COLUMNS
        points = []

        for row in range(rows):
            row_ratio = row / (rows - 1) if rows > 1 else 0.5
            left_x = top_left[0] + (bottom_left[0] - top_left[0]) * row_ratio
            left_y = top_left[1] + (bottom_left[1] - top_left[1]) * row_ratio
            right_x = top_right[0] + (bottom_right[0] - top_right[0]) * row_ratio
            right_y = top_right[1] + (bottom_right[1] - top_right[1]) * row_ratio

            column_indices = range(columns) if row % 2 == 0 else range(columns - 1, -1, -1)
            for column in column_indices:
                column_ratio = column / (columns - 1) if columns > 1 else 0.5
                x = round(left_x + (right_x - left_x) * column_ratio)
                y = round(left_y + (right_y - left_y) * column_ratio)
                points.append((x, y))

        last_point = self._load_last_wall_point()
        if last_point in points:
            start_index = (points.index(last_point) + 1) % len(points)
            points = points[start_index:] + points[:start_index]
            self.log(f"Tiếp tục quét sau vị trí tường đã nâng {last_point}")

        return points

    def _load_wall_state(self):
        state_file = Path(self.c.WALL_STATE_FILE)
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError as error:
            self.log(f"Cache tường không hợp lệ ({error}), khởi tạo lại")
            return {}
        if not isinstance(state, dict):
            self.log("Cache tường sai định dạng, khởi tạo lại")
            return {}
        return state

    def _load_last_wall_point(self):
        state = self._load_wall_state()
        point = state.get("last_wall_point")
        if (
            isinstance(point, list)
            and len(point) == 2
            and all(isinstance(value, int) for value in point)
        ):
            return tuple(point)
        if point is not None:
            self.log("Cache vị trí tường sai định dạng, quét từ đầu")
        return None

    def _save_wall_state(self, **updates):
        state_file = Path(self.c.WALL_STATE_FILE)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        temporary_file = state_file.with_suffix(state_file.suffix + ".tmp")
        state = self._load_wall_state()
        state.update(updates)
        temporary_file.write_text(
            json.dumps(state),
            encoding="utf-8",
        )
        temporary_file.replace(state_file)

    def upgrade_walls(self, gold=None, elixir=None):
        """Inspect configured wall points and upgrade one valid, affordable wall."""
        self._last_wall_payment = None
        if gold is None or elixir is None:
            gold, elixir = self.read_resources()
        self.log(f"Up tường (vàng={gold}, elixir={elixir})")

        screen = self.dev.screenshot()
        cv2.imwrite("screenshots/debug_wall.png", screen)

        candidates = self.wall_scan_points()
        self.log(f"  quét {len(candidates)} điểm bên trong cụm tường")

        upgradeable_template = "screenshots/Tuong_can_nang_cap.png"
        max_template = "screenshots/Tuong_da_max.png"

        for x, y in candidates:
            self.dev.tap(x, y)
            time.sleep(1.2 + random.uniform(0, 0.5))

            screen = self.dev.screenshot()
            cv2.imwrite("screenshots/debug_wall.png", screen)

            state, score = vision.wall_menu_state(
                screen, upgradeable_template, max_template
            )
            self.log(f"  điểm ({x}, {y}): trạng thái tường={state}, tương quan={score:.3f}")

            if state is None:
                self.log("  không nhận diện được menu tường, bỏ điểm này")
                # Không dùng Android Back khi chưa xác nhận menu: Back có thể thoát giao diện game.
                continue

            if state == 0:
                self.tap(self.c.CONFIRM_CLOSE, 0.8)
                continue

            gp = ocr.read_number(screen, self.c.GOLD_PRICE_REGION)
            ep = ocr.read_number(screen, self.c.ELIXIR_PRICE_REGION)
            self.log(f"  giá vàng={gp}, giá elixir={ep}")

            options = []
            if gp and gp <= self.c.WALL_MAX_PRICE and gold >= gp:
                options.append(("gold", gold - gp, self.c.PAY_WITH_GOLD))
            if ep and ep <= self.c.WALL_MAX_PRICE and elixir >= ep:
                options.append(("elixir", elixir - ep, self.c.PAY_WITH_ELIXIR))

            if not options:
                self.log("  không đủ tài nguyên hoặc vượt ngưỡng")
                self.tap(self.c.CONFIRM_CLOSE, 0.8)
                continue

            # Ưu tiên vàng; chỉ dùng dầu nếu không có lựa chọn vàng hợp lệ.
            selected = next(option for option in options if option[0] == "gold") \
                if any(option[0] == "gold" for option in options) else options[0]
            currency, _, pay = selected
            self.tap(pay, 2)

            screen = self.dev.screenshot()
            cv2.imwrite("screenshots/debug_confirm.png", screen)
            price = ocr.read_number(screen, self.c.CONFIRM_PRICE_REGION)
            self.log(f"  popup xác nhận: giá={price}")

            if price and price <= self.c.WALL_MAX_PRICE:
                self.tap(self.c.CONFIRM, 2.5)
                self.log("  đã nâng 1 đoạn")
                self._last_wall_payment = (currency, price)
                self._save_wall_state(last_wall_point=[x, y])
                return True

            self.log("  giá popup không hợp lệ, đóng popup")
            self.tap(self.c.CONFIRM_CLOSE, 1)

        return False                                        
    # ---------- Vòng lặp ----------
    def cycle(self):
        """Run one farming cycle, then upgrade walls when resource thresholds allow."""
        if not self.farm_attack():
            time.sleep(5)
            return

        self._battles_since_resource_ocr += 1
        self._save_wall_state(
            battles_since_resource_ocr=self._battles_since_resource_ocr
        )
        interval = int(self.c.RESOURCE_OCR_EVERY_BATTLES)
        if interval <= 0:
            raise ValueError("RESOURCE_OCR_EVERY_BATTLES phải > 0")
        if self._battles_since_resource_ocr < interval:
            self.log(
                f"Bỏ qua OCR tài nguyên "
                f"({self._battles_since_resource_ocr}/{interval} trận)"
            )
            return

        gold, elixir = self.read_resources()
        self._battles_since_resource_ocr = 0
        self._save_wall_state(battles_since_resource_ocr=0)
        self.log(f"Tài nguyên sau trận: vàng={gold} elixir={elixir}")
        can_upgrade = (
            gold >= self.c.WALL_MIN_GOLD
            or elixir >= self.c.WALL_MIN_ELIXIR
        )
        if can_upgrade:
            self.upgrade_walls_until_broke(gold, elixir)

    def upgrade_walls_until_broke(self, gold=None, elixir=None):
        """Upgrade walls until resources are low, no wall is affordable, or limit is hit."""
        if gold is None or elixir is None:
            gold, elixir = self.read_resources()

        count = 0
        for _ in range(self.c.MAX_WALLS_PER_CYCLE):
            self.log(f"Tài nguyên: vàng={gold} elixir={elixir}")

            can_upgrade = (
                gold >= self.c.WALL_MIN_GOLD
                or elixir >= self.c.WALL_MIN_ELIXIR
            )
            if not can_upgrade:
                self.log("Hết tiền up tường, quay lại farm")
                break

            if not self.upgrade_walls(gold, elixir):
                self.log("Không còn đoạn nào nâng được, quay lại farm")
                break

            payment = self._last_wall_payment
            if payment is None:
                raise RuntimeError("Nâng tường thành công nhưng thiếu thông tin giá thanh toán")
            currency, price = payment
            if currency == "gold":
                gold = max(0, gold - price)
            else:
                elixir = max(0, elixir - price)

            count += 1
            time.sleep(2)

        self.log(f"Đã nâng {count} đoạn tường")

