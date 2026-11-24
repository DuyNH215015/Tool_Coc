from accounts.attack import (
    DROP_HEROES,
    DROP_LINES,
    DROP_MAX_TAPS,
    HERO_ABILITY_DELAY_SECONDS,
    HERO_COUNT,
    HERO_DROP_POINTS,
    HERO_SLOT_POINTS,
    RAGE_DROP_POINTS,
    RAGE_MAX_DROPS,
    RAGE_SLOT,
)
from accounts.button_common import (
    ARMY_ATTACK,
    ATTACK_BUTTON,
    ENEMY_ELIXIR,
    ENEMY_GOLD,
    FIND_MATCH,
    HOME_ELIXIR,
    HOME_GOLD,
    MAX_RESOURCE_OCR,
    NEXT_BUTTON,
    SEARCH_CANCEL,
)
from accounts.wall import (
    CONFIRM,
    CONFIRM_CLOSE,
    CONFIRM_PRICE_REGION,
    ELIXIR_PRICE_REGION,
    GOLD_PRICE_REGION,
    MAX_WALLS_PER_CYCLE,
    PAY_WITH_ELIXIR,
    PAY_WITH_GOLD,
    RESOURCE_OCR_EVERY_BATTLES,
    WALL_MAX_PRICE,
    WALL_MIN_ELIXIR,
    WALL_MIN_GOLD,
    WALL_POINTS,
    WALL_SCAN_COLUMNS,
    WALL_SCAN_ROWS,
    WALL_STATE_FILE,
)

SLOT_GOBLIN = (137, 620)                  # tâm ô Goblin đầu tiên
GOBLIN_COUNT_REGION = (125, 578, 55, 32)  # số trên ô Goblin, ví dụ x117

EDGE_SAFE_MARGIN = 150                    # né hai đầu mút mỗi đường (px)
DROP_JITTER = 0                           # không lệch khỏi 4 đường thẳng khi thả quân
DROP_PASS_SPACING = 100                   # khoảng cách thật giữa hai quân liên tiếp trên cùng đường (px)
DROP_OCR_CHECK_INTERVAL = 5               # cứ 5 tap mới đọc OCR để dừng khi hết Goblin
MIN_BATTLE_SECONDS = 60                   # thời gian trận tối thiểu tính từ lúc bắt đầu thả
MAX_BATTLE_SECONDS = 65                   # thời gian trận tối đa

SURRENDER = (90, 535)                     # Đầu hàng / Kết thúc trận chiến
SURRENDER_CONFIRM = (780, 430)            # nút xác nhận đầu hàng
RETURN_HOME = (640, 618)                  # Về làng ở màn kết quả

MIN_LOOT = 600000
MAX_NEXT = 15

__all__ = [name for name in globals() if name.isupper()]
