import argparse
import importlib
import json
import os
import subprocess
import sys
import threading
import webbrowser
from collections import deque
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import cv2

from adb import Device
from drop_config import (
    ACCOUNTS_DIR,
    get_drop_config,
    load_drop_overrides,
    save_drop_overrides,
)


ROOT_DIR = Path(__file__).resolve().parent
WEB_DIR = ROOT_DIR / "web"
RUN_ACTIONS = {
    "loop": "Chạy chu trình nền",
    "onlyfarm": "Chỉ farm liên tục",
    "cycle": "Chạy một chu kỳ",
    "farm_attack": "Đánh một trận",
    "read_resources": "Đọc tài nguyên",
    "in_battle": "Kiểm tra đang trong trận",
    "wait_for_battle": "Chờ nhận diện trận",
    "good_target": "Kiểm tra mục tiêu hiện tại",
    "goblins_left": "Đọc số Goblin còn lại",
    "drop_all_goblins": "Thả Goblin (cần đang trong trận)",
    "end_battle": "Kết thúc trận (đầu hàng)",
    "upgrade_walls": "Nâng tường",
    "upgrade_walls_until_broke": "Nâng tường đến ngưỡng",
}


class BotRunner:
    def __init__(self, account):
        self.account = account
        self.process = None
        self.action = None
        self.output = deque(maxlen=300)
        self.lock = threading.Lock()

    def start(self, action):
        if action not in RUN_ACTIONS:
            raise ValueError("Action không được hỗ trợ")
        with self.lock:
            if self.process is not None and self.process.poll() is None:
                raise ValueError("Đang có một action chạy; hãy dừng trước khi chạy action khác")

            environment = os.environ.copy()
            environment["PYTHONIOENCODING"] = "utf-8:replace"
            self.process = subprocess.Popen(
                [
                    sys.executable,
                    "-u",
                    str(ROOT_DIR / "run_one.py"),
                    self.account,
                    action,
                ],
                cwd=ROOT_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=environment,
            )
            self.action = action
            self.output.clear()
            process = self.process
            threading.Thread(
                target=self._read_output,
                args=(process,),
                daemon=True,
            ).start()
        return self.status()

    def _read_output(self, process):
        if process.stdout is None:
            return
        for line in process.stdout:
            with self.lock:
                self.output.append(line.rstrip())

    def stop(self):
        with self.lock:
            process = self.process
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        return self.status()

    def status(self):
        with self.lock:
            process = self.process
            action = self.action
            logs = list(self.output)
        running = process is not None and process.poll() is None
        return {
            "running": running,
            "pid": process.pid if process is not None else None,
            "action": action,
            "label": RUN_ACTIONS.get(action),
            "exitCode": process.returncode if process is not None and not running else None,
            "logs": logs,
        }


def _jsonable_config(account, config_module):
    defaults = get_drop_config(config_module)
    overrides = load_drop_overrides(account, ACCOUNTS_DIR)
    effective = dict(defaults)
    effective.update(overrides)
    return {
        "account": account,
        "device": config_module.DEVICE,
        "defaults": defaults,
        "config": effective,
        "hasOverrides": bool(overrides),
        "actions": [{"value": key, "label": value} for key, value in RUN_ACTIONS.items()],
    }


def make_handler(account, config_module, runner):
    class RequestHandler(SimpleHTTPRequestHandler):
        def _send_json(self, payload, status=200):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_json(self):
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as error:
                raise ValueError("Content-Length không hợp lệ") from error
            if length <= 0 or length > 1024 * 1024:
                raise ValueError("Kích thước request phải từ 1 byte đến 1 MB")
            try:
                return json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise ValueError("Nội dung request không phải JSON hợp lệ") from error

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/api/config":
                try:
                    self._send_json(_jsonable_config(account, config_module))
                except (OSError, ValueError, json.JSONDecodeError) as error:
                    self._send_json({"error": str(error)}, status=500)
                return
            if path == "/api/screenshot":
                try:
                    image = Device(config_module.DEVICE).screenshot()
                    if image is None:
                        raise RuntimeError("ADB trả về ảnh màn hình rỗng")
                    success, encoded = cv2.imencode(".jpg", image)
                    if not success:
                        raise RuntimeError("Không thể mã hóa ảnh screenshot")
                except (cv2.error, OSError, RuntimeError, subprocess.SubprocessError) as error:
                    self._send_json({"error": f"Không chụp được màn hình ADB: {error}"}, status=502)
                    return
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(encoded.size))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(encoded.tobytes())
                return
            if path == "/api/runner":
                self._send_json(runner.status())
                return
            if path == "/api/actions":
                self._send_json(
                    [{"value": key, "label": label} for key, label in RUN_ACTIONS.items()]
                )
                return
            super().do_GET()

        def do_POST(self):
            path = urlparse(self.path).path
            try:
                if path == "/api/config":
                    config = self._read_json()
                    saved_path = save_drop_overrides(account, config, ACCOUNTS_DIR)
                    self._send_json({"saved": True, "path": saved_path.name})
                    return
                if path == "/api/reset":
                    override_path = ACCOUNTS_DIR / f"{account}.drop.json"
                    if override_path.exists():
                        override_path.unlink()
                    self._send_json({"reset": True})
                    return
                if path == "/api/runner/start":
                    data = self._read_json()
                    if not isinstance(data, dict):
                        raise ValueError("Request phải là một object JSON")
                    result = runner.start(data.get("action"))
                    self._send_json(result)
                    return
                if path == "/api/runner/stop":
                    self._send_json(runner.stop())
                    return
            except ValueError as error:
                self._send_json({"error": str(error)}, status=400)
                return
            except (OSError, subprocess.SubprocessError) as error:
                self._send_json({"error": str(error)}, status=500)
                return
            self._send_json({"error": "API không tồn tại"}, status=404)

        def log_message(self, format_string, *args):
            print(f"[web] {format_string % args}")

    return RequestHandler


def main():
    parser = argparse.ArgumentParser(
        description="Vue UI chọn tọa độ thả quân và chạy các action của bot"
    )
    parser.add_argument("account", help="Tên cấu hình trong accounts/ (ví dụ: acc1)")
    parser.add_argument("--port", type=int, default=8765, help="Cổng web (mặc định: 8765)")
    args = parser.parse_args()

    load_drop_overrides(args.account, ACCOUNTS_DIR)
    config_module = importlib.import_module(f"accounts.{args.account}")
    runner = BotRunner(args.account)
    handler = make_handler(args.account, config_module, runner)
    server = ThreadingHTTPServer(
        ("127.0.0.1", args.port),
        partial(handler, directory=str(WEB_DIR)),
    )
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Vue UI cho {args.account} đang chạy tại {url}")
    print("Nhấn Ctrl+C để dừng giao diện.")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐang dừng giao diện...")
    finally:
        runner.stop()
        server.server_close()


if __name__ == "__main__":
    main()
