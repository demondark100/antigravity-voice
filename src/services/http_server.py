import time
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from utils.config import log, HTTP_PORT
from plan_manager import get_plan_info

def create_handler_class(player):
    class VoiceRequestHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args): pass

        def _send_cors(self, status=200, content_type="application/json"):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Private-Network", "true")
            self.end_headers()

        def do_OPTIONS(self):
            self._send_cors(204)

        def do_GET(self):
            if self.path.startswith("/plan/status"):
                path, title = get_plan_info(player.brain_dirs)
                self._send_cors(200)
                self.wfile.write(json.dumps({
                    "has_plan": bool(path), "plan_file": path or "", "plan_title": title,
                    "is_reading_plan": player.is_reading_plan, "is_playing": player.is_playing,
                    "is_paused": player.is_paused, "is_synthesizing": player.is_synthesizing
                }).encode("utf-8"))
            elif self.path.startswith("/status"):
                self._send_cors(200)
                self.wfile.write(json.dumps({
                    "is_playing": player.is_playing, "is_paused": player.is_paused,
                    "is_synthesizing": player.is_synthesizing, "turn_id": player.current_turn_id,
                    "sig": player.current_sig, "enabled": player.config.get("enabled", True)
                }).encode("utf-8"))
            elif self.path.startswith("/replay"):
                player.replay_last()
                self._send_cors(200)
                self.wfile.write(b'{"ok":true,"state":"playing"}')
            elif self.path.startswith("/stop"):
                if player.is_playing and not player.is_paused:
                    player.pause_playback()
                    st = "paused"
                else:
                    player.stop_playback()
                    st = "idle"
                self._send_cors(200)
                self.wfile.write(json.dumps({"ok": True, "state": st}).encode("utf-8"))
            else:
                self._send_cors(404)
                self.wfile.write(b'{"error":"not_found"}')

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length).decode("utf-8", errors="ignore") if length > 0 else "{}"
            try: data = json.loads(raw) if raw else {}
            except Exception: data = {}

            if self.path.startswith("/plan/speak"):
                st = player.toggle_plan_speech(data.get("plan_path"), bool(data.get("restart")), data.get("conv_id"))
                _, title = get_plan_info(player.brain_dirs, data.get("conv_id"))
                self._send_cors(200)
                self.wfile.write(json.dumps({"ok": True, "state": st, "plan_file": player.current_plan_path, "plan_title": title, "is_reading_plan": player.is_reading_plan}).encode("utf-8"))
            elif self.path.startswith("/plan/stop"):
                if player.is_reading_plan and player.is_playing and not player.is_paused:
                    player.pause_playback()
                    st = "paused"
                else:
                    player.stop_playback()
                    st = "idle"
                self._send_cors(200)
                self.wfile.write(json.dumps({"ok": True, "state": st}).encode("utf-8"))
            elif self.path.startswith("/speak"):
                st = player.toggle_or_speak((data.get("text") or "").strip(), bool(data.get("restart")), (data.get("turn_id") or "").strip())
                self._send_cors(200)
                self.wfile.write(json.dumps({"ok": True, "state": st, "turn_id": player.current_turn_id, "sig": player.current_sig}).encode("utf-8"))
            elif self.path.startswith("/replay"):
                player.replay_last()
                self._send_cors(200)
                self.wfile.write(b'{"ok":true,"state":"playing"}')
            elif self.path.startswith("/stop"):
                if player.is_playing and not player.is_paused:
                    player.pause_playback()
                    st = "paused"
                else:
                    player.stop_playback()
                    st = "idle"
                self._send_cors(200)
                self.wfile.write(json.dumps({"ok": True, "state": st}).encode("utf-8"))
            else:
                self._send_cors(404)
                self.wfile.write(b'{"error":"not_found"}')
    return VoiceRequestHandler

def start_local_http_server(player):
    handler_cls = create_handler_class(player)
    def _run():
        ThreadingHTTPServer.allow_reuse_address = True
        server = None
        for _ in range(10):
            try:
                server = ThreadingHTTPServer(("127.0.0.1", HTTP_PORT), handler_cls)
                break
            except OSError: time.sleep(0.5)
        if server:
            log(f"[🌐] Servidor local activo en http://127.0.0.1:{HTTP_PORT}")
            server.serve_forever()
    threading.Thread(target=_run, daemon=True).start()
