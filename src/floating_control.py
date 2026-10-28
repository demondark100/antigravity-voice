import os
import sys
import threading
import urllib.request
import tkinter as tk

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

from utils.config import load_config, save_config, STOP_FILE
from utils.voice_list import VOICES

class FloatingVoiceWidget:
    def __init__(self):
        self.config = load_config()
        self.root = tk.Tk()
        self.root.title("Antigravity Voz")
        self.root.attributes("-topmost", True)
        screen_w, screen_h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        x, y = self.config.get("widget_x", max(100, screen_w - 420)), self.config.get("widget_y", max(100, screen_h - 160))
        self.root.geometry(f"395x52+{x}+{y}")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(False, False)
        self.setup_ui()
        self.update_state_from_config()
        self.poll_config_changes()
        self.root.bind("<Configure>", lambda e: self._on_configure())

    def _on_configure(self):
        if self.root.winfo_x() > 0 and self.root.winfo_y() > 0:
            self.config["widget_x"], self.config["widget_y"] = self.root.winfo_x(), self.root.winfo_y()
            save_config(self.config)

    def setup_ui(self):
        box = tk.Frame(self.root, bg="#181825", padx=6, pady=6)
        box.pack(fill="both", expand=True)

        self.btn_toggle = tk.Button(box, text="🎙️ Voz: ACTIVA", bg="#2e7d32", fg="#fff", relief="flat", font=("Segoe UI", 9, "bold"), cursor="hand2", padx=8, pady=4, command=self.toggle_mute)
        self.btn_toggle.pack(side="left", padx=3)

        self.btn_plan = tk.Button(box, text="📋 Plan", bg="#0284c7", fg="#fff", relief="flat", font=("Segoe UI", 9, "bold"), cursor="hand2", padx=8, pady=4, command=self.toggle_plan)
        self.btn_plan.pack(side="left", padx=3)

        self.btn_stop = tk.Button(box, text="⏹️ Parar", bg="#c62828", fg="#fff", relief="flat", font=("Segoe UI", 9, "bold"), cursor="hand2", padx=8, pady=4, command=self.stop_audio)
        self.btn_stop.pack(side="left", padx=3)

        self.btn_menu = tk.Button(box, text="⚙️ Voces", bg="#313244", fg="#cdd6f4", relief="flat", font=("Segoe UI", 9), cursor="hand2", padx=8, pady=4, command=self.show_voice_menu)
        self.btn_menu.pack(side="left", padx=3)

    def toggle_mute(self):
        self.config = load_config()
        self.config["enabled"] = not self.config.get("enabled", True)
        save_config(self.config)
        self.update_state_from_config()

    def toggle_plan(self):
        def _call():
            try:
                req = urllib.request.Request("http://127.0.0.1:49152/plan/speak", data=b'{"action":"toggle"}', headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=2.0): pass
            except Exception: pass
        threading.Thread(target=_call, daemon=True).start()

    def stop_audio(self):
        try:
            with open(STOP_FILE, "w", encoding="utf-8") as f: f.write("stop")
        except Exception: pass

    def show_voice_menu(self):
        menu = tk.Menu(self.root, tearoff=0, bg="#1e1e2e", fg="#cdd6f4", activebackground="#313244")
        cur = self.config.get("voice", "es-MX-DaliaNeural")
        for name, vid in VOICES:
            pfx = "✓ " if vid == cur else "   "
            menu.add_command(label=f"{pfx}{name}", command=lambda v=vid: self.change_voice(v))
        menu.post(self.root.winfo_rootx() + self.btn_menu.winfo_x(), self.root.winfo_rooty() + self.btn_menu.winfo_y() + 32)

    def change_voice(self, vid):
        self.config = load_config()
        self.config["voice"] = vid
        save_config(self.config)

    def update_state_from_config(self):
        if self.config.get("enabled", True):
            self.btn_toggle.configure(text="🎙️ Voz: ACTIVA", bg="#2e7d32", fg="#fff")
        else:
            self.btn_toggle.configure(text="🔇 SILENCIADO", bg="#5c6370", fg="#ffdddd")

    def poll_config_changes(self):
        cfg = load_config()
        if cfg.get("enabled") != self.config.get("enabled"):
            self.config = cfg
            self.update_state_from_config()
        self.root.after(800, self.poll_config_changes)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    FloatingVoiceWidget().run()
