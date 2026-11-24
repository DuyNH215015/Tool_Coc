import importlib
import sys
import time
import traceback
from bot import Bot
from drop_config import apply_drop_overrides

name = sys.argv[1]                       # tên acc, vd: acc1
action = sys.argv[2] if len(sys.argv) > 2 else "loop"

cfg = importlib.import_module(f"accounts.{name}")
apply_drop_overrides(cfg, name)
bot = Bot(cfg)

if action == "loop":
    while True:
        try:
            bot.cycle()
        except Exception as e:
            bot.log(f"Lỗi: {e}")
            traceback.print_exc()
        time.sleep(5)

elif action == "onlyfarm":
    completed_battles = 0
    check_resources = True

    while True:
        try:
            if check_resources:
                gold, elixir = bot.read_resources()
                bot.log(f"Only farm: vàng={gold}, elixir={elixir}")

                if gold >= 28_000_000 and elixir >= 28_000_000:
                    bot.log("Đã đủ cả vàng và elixir 28 triệu, dừng onlyfarm")
                    break

                check_resources = False

            if bot.farm_attack():
                completed_battles += 1
                if completed_battles >= 6:
                    completed_battles = 0
                    check_resources = True
            time.sleep(2)
        except Exception as e:
            bot.log(f"Lỗi: {e}")
            traceback.print_exc()
            time.sleep(5)

else:
    result = getattr(bot, action)()      # chạy đúng 1 hàm để test
    if result is not None:
        bot.log(f"Kết quả {action}: {result}")