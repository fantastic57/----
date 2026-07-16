#!/usr/bin/env python3
"""本地服务器 - 高德地图看房标记工具"""
import http.server
import json
import os
import urllib.parse

PORT = 8080
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")
HTML_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "map.html")

DEFAULT_WEIGHTS = {
    "school_quality": 3,
    "metro_lines": 3,
    "metro_line3_walk_min": 3,
    "metro_nearest_walk_min": 3,
    "school_cycling_min": 3,
    "work_bus_min": 3,
    "work_car_min": 3,
    "parking": 3,
    "environment": 3,
    "amenities_level": 3,
}

DEFAULT_HOUSE_WEIGHTS = {
    "built_year": 3,
    "price_tier": 3,
    "area_sqm": 3,
    "internal_area_sqm": 3,
    "floor_num": 3,
    "has_elevator": 3,
    "stairwell": 3,
    "households_per_floor": 3,
    "room_layout": 3,
    "layout_type": 3,
    "daylight": 3,
    "north_south_transparent": 3,
    "noise": 3,
    "privacy": 3,
    "decoration": 3,
    "seller_mood": 3,
}


def read_data():
    """读取 data.json
    新格式: {weights: {...}, markers: [...], others: [...]}
    旧格式（兼容）: [...]
    """
    if not os.path.exists(DATA_FILE):
        return _empty_data()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, list):
            return {
                "weights": DEFAULT_WEIGHTS.copy(),
                "house_weights": DEFAULT_HOUSE_WEIGHTS.copy(),
                "markers": raw,
                "others": [],
            }
        if isinstance(raw, dict):
            return {
                "weights": raw.get("weights") or DEFAULT_WEIGHTS.copy(),
                "house_weights": raw.get("house_weights") or DEFAULT_HOUSE_WEIGHTS.copy(),
                "markers": raw.get("markers") or [],
                "others": raw.get("others") or [],
            }
        return _empty_data()
    except (json.JSONDecodeError, IOError):
        return _empty_data()


def _empty_data():
    return {
        "weights": DEFAULT_WEIGHTS.copy(),
        "house_weights": DEFAULT_HOUSE_WEIGHTS.copy(),
        "markers": [],
        "others": [],
    }


def write_data(data):
    """写入 data.json"""
    try:
        # 兼容旧代码只发 marker array 的情况
        if isinstance(data, list):
            data = {"weights": DEFAULT_WEIGHTS.copy(), "house_weights": DEFAULT_HOUSE_WEIGHTS.copy(), "markers": data, "others": []}
        # 保证结构完整
        if not isinstance(data, dict):
            raise ValueError("Data must be dict or list")
        data.setdefault("weights", DEFAULT_WEIGHTS.copy())
        data.setdefault("house_weights", DEFAULT_HOUSE_WEIGHTS.copy())
        data.setdefault("markers", [])
        data.setdefault("others", [])
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"写入失败: {e}")
        return False


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        # 读取完整数据（weights + markers + others）
        if parsed.path == "/api/data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(read_data(), ensure_ascii=False).encode("utf-8"))
            return

        # 仅 weights（用于不重新加载 markers 的场景）
        if parsed.path == "/api/weights":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(read_data()["weights"], ensure_ascii=False).encode("utf-8"))
            return

        # 仅 house_weights
        if parsed.path == "/api/house_weights":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(read_data()["house_weights"], ensure_ascii=False).encode("utf-8"))
            return

        # 仅 markers 数组（向后兼容）
        if parsed.path == "/api/markers":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(read_data()["markers"], ensure_ascii=False).encode("utf-8"))
            return

        # 默认：返回 map.html
        if parsed.path == "/" or parsed.path == "/map.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            with open(HTML_FILE, "rb") as f:
                self.wfile.write(f.read())
            return

        # 其他静态文件
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        # 保存完整数据（建议用 /api/data）
        if parsed.path in ("/api/data", "/api/markers"):
            try:
                data = json.loads(body.decode("utf-8"))
                ok = write_data(data)
                if not ok:
                    self._error_response(500, "写入失败")
                    return
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True}, ensure_ascii=False).encode("utf-8"))
                return
            except (json.JSONDecodeError, ValueError) as e:
                self._error_response(400, str(e))
                return

        # 保存仅 weights
        if parsed.path == "/api/weights":
            try:
                weights = json.loads(body.decode("utf-8"))
                if not isinstance(weights, dict):
                    raise ValueError("weights must be a dict")
                current = read_data()
                current["weights"] = weights
                ok = write_data(current)
                if not ok:
                    self._error_response(500, "写入失败")
                    return
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True}, ensure_ascii=False).encode("utf-8"))
                return
            except (json.JSONDecodeError, ValueError) as e:
                self._error_response(400, str(e))
                return

        # 保存仅 house_weights
        if parsed.path == "/api/house_weights":
            try:
                weights = json.loads(body.decode("utf-8"))
                if not isinstance(weights, dict):
                    raise ValueError("house_weights must be a dict")
                current = read_data()
                current["house_weights"] = weights
                ok = write_data(current)
                if not ok:
                    self._error_response(500, "写入失败")
                    return
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True}, ensure_ascii=False).encode("utf-8"))
                return
            except (json.JSONDecodeError, ValueError) as e:
                self._error_response(400, str(e))
                return

        self._error_response(404, "Not Found")

    def _error_response(self, code, msg):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": False, "error": msg}, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"服务器已启动: http://localhost:{PORT}")
    print("按 Ctrl+C 停止")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        server.server_close()
