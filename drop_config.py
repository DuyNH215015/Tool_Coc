import json
import os
import re
import tempfile
from pathlib import Path


DROP_CONFIG_KEYS = (
    "SLOT_GOBLIN",
    "DROP_LINES",
    "RAGE_SLOT",
    "RAGE_MAX_DROPS",
    "RAGE_DROP_POINTS",
    "DROP_HEROES",
    "HERO_COUNT",
    "HERO_SLOT_POINTS",
    "HERO_DROP_POINTS",
)

ACCOUNTS_DIR = Path(__file__).resolve().parent / "accounts"


def _account_path(account, accounts_dir=ACCOUNTS_DIR):
    if not isinstance(account, str) or not re.fullmatch(r"[A-Za-z0-9_]+", account):
        raise ValueError("Tên tài khoản chỉ được chứa chữ, số và dấu gạch dưới")
    return Path(accounts_dir) / f"{account}.drop.json"


def _is_point(point):
    return (
        isinstance(point, (tuple, list))
        and len(point) == 2
        and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and 0 <= value <= 65535
            for value in point
        )
    )


def validate_drop_config(config):
    if not isinstance(config, dict):
        raise ValueError("Cấu hình phải là một object JSON")
    if set(config) != set(DROP_CONFIG_KEYS):
        missing = sorted(set(DROP_CONFIG_KEYS) - set(config))
        extra = sorted(set(config) - set(DROP_CONFIG_KEYS))
        raise ValueError(f"Trường cấu hình không hợp lệ (thiếu={missing}, thừa={extra})")

    if not _is_point(config["SLOT_GOBLIN"]) or not _is_point(config["RAGE_SLOT"]):
        raise ValueError("SLOT_GOBLIN và RAGE_SLOT phải là tọa độ [x, y]")

    lines = config["DROP_LINES"]
    if (
        not isinstance(lines, list)
        or len(lines) != 4
        or any(
            not isinstance(line, (tuple, list))
            or len(line) != 2
            or not all(_is_point(point) for point in line)
            for line in lines
        )
    ):
        raise ValueError("DROP_LINES phải có đúng 4 đoạn, mỗi đoạn gồm 2 tọa độ")

    rage_points = config["RAGE_DROP_POINTS"]
    if (
        not isinstance(rage_points, list)
        or len(rage_points) > 11
        or any(not _is_point(point) for point in rage_points)
    ):
        raise ValueError("RAGE_DROP_POINTS phải có tối đa 11 tọa độ [x, y]")
    rage_count = config["RAGE_MAX_DROPS"]
    if (
        not isinstance(rage_count, int)
        or isinstance(rage_count, bool)
        or not 0 <= rage_count <= 11
    ):
        raise ValueError("RAGE_MAX_DROPS phải từ 0 đến 11")

    if not isinstance(config["DROP_HEROES"], bool):
        raise ValueError("DROP_HEROES phải là true hoặc false")
    hero_count = config["HERO_COUNT"]
    if (
        not isinstance(hero_count, int)
        or isinstance(hero_count, bool)
        or not 0 <= hero_count <= 4
    ):
        raise ValueError("HERO_COUNT phải từ 0 đến 4")
    for key in ("HERO_SLOT_POINTS", "HERO_DROP_POINTS"):
        points = config[key]
        if (
            not isinstance(points, list)
            or len(points) > 4
            or any(not _is_point(point) for point in points)
        ):
            raise ValueError(f"{key} phải có tối đa 4 tọa độ [x, y]")
    if config["DROP_HEROES"] and (
        len(config["HERO_SLOT_POINTS"]) < hero_count
        or len(config["HERO_DROP_POINTS"]) < hero_count
    ):
        raise ValueError("Cần đủ tọa độ ô chọn và điểm thả cho số tướng đã bật")

    return {
        key: json.loads(json.dumps(config[key]))
        for key in DROP_CONFIG_KEYS
    }


def get_drop_config(config):
    def to_json_value(value):
        if isinstance(value, (tuple, list)):
            return [to_json_value(item) for item in value]
        return value

    return {key: to_json_value(getattr(config, key)) for key in DROP_CONFIG_KEYS}


def load_drop_overrides(account, accounts_dir=ACCOUNTS_DIR):
    path = _account_path(account, accounts_dir)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        overrides = json.load(file)
    return validate_drop_config(overrides)


def save_drop_overrides(account, config, accounts_dir=ACCOUNTS_DIR):
    validated = validate_drop_config(config)
    path = _account_path(account, accounts_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)
            json.dump(validated, file, ensure_ascii=False, indent=2)
            file.write("\n")
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    return path


def apply_drop_overrides(config, account, accounts_dir=ACCOUNTS_DIR):
    overrides = load_drop_overrides(account, accounts_dir)
    for key, value in overrides.items():
        setattr(config, key, value)
    return bool(overrides)
