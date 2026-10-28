import os
import sys
import json
import time
import tkinter as tk
from tkinter import messagebox

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
STOP_FILE = os.path.join(BASE_DIR, ".stop_trigger")

VOICES = [
    ("Dalia (México - Femenina)", "es-MX-DaliaNeural"),
    ("Jorge (México - Masculina)", "es-MX-JorgeNeural"),
    ("Álvaro (España - Masculina)", "es-ES-AlvaroNeural"),
    ("Elvira (España - Femenina)", "es-ES-ElviraNeural"),
    ("Gonzalo (Colombia - Masculina)", "es-CO-GonzaloNeural"),
    ("Alex (Perú - Masculina)", "es-PE-AlexNeural"),
    ("Tomas (Argentina - Masculina)", "es-AR-TomasNeural")
]

def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"voice": "es-MX-DaliaNeural", "rate": "+10%", "enabled": True}

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error guardando config: {e}")

class FloatingVoiceWidget:
    def __init__(self):
        self.config = load_config()
        self.root = tk.Tk()
        self.root.title("Antigravity Voz")
        
        # Mantener siempre al frente
        self.root.attributes("-topmost", True)
        
        # Tamaño y posición visible en la pantalla (centro-derecha inferior)
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        default_x = max(100, screen_w - 360)
        default_y = max(100, screen_h - 160)
        
        x = self.config.get("widget_x", default_x)
        y = self.config.get("widget_y", default_y)
        
        self.root.geometry(f"395x52+{x}+{y}")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(False, False)

        # Forzar al frente
        self.root.lift()
        self.root.focus_force()

        self.setup_ui()
        self.update_state_from_config()
        self.poll_config_changes()

        # Guardar posición al mover
        self.root.bind("<Configure>", self.on_window_configure)

    def on_window_configure(self, event):
        if self.root.winfo_x() > 0 and self.root.winfo_y() > 0:
            self.config["widget_x"] = self.root.winfo_x()
            self.config["widget_y"] = self.root.winfo_y()
            save_config(self.config)

    def setup_ui(self):
        self.container = tk.Frame(self.root, bg="#181825", padx=6, pady=6)
        self.container.pack(fill="both", expand=True)

        # Botón Toggle ON/OFF
        self.btn_toggle = tk.Button(
            self.container,
            text="🎙️ Voz: ACTIVA",
            bg="#2e7d32",
            fg="#ffffff",
            activebackground="#388e3c",
            activeforeground="#ffffff",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
            padx=10,
            pady=4,
            command=self.toggle_mute
        )
        self.btn_toggle.pack(side="left", padx=4)

        # Botón Leer Plan
        self.btn_plan = tk.Button(
            self.container,
            text="📋 Plan",
            bg="#0284c7",
            fg="#ffffff",
            activebackground="#0369a1",
            activeforeground="#ffffff",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
            padx=8,
            pady=4,
            command=self.toggle_plan
        )
        self.btn_plan.pack(side="left", padx=4)

        # Botón Detener Audio
        self.btn_stop = tk.Button(
            self.container,
            text="⏹️ Parar",
            bg="#c62828",
            fg="#ffffff",
            activebackground="#d32f2f",
            activeforeground="#ffffff",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
            padx=8,
            pady=4,
            command=self.stop_audio
        )
        self.btn_stop.pack(side="left", padx=4)

        # Botón Menú de Voces
        self.btn_menu = tk.Button(
            self.container,
            text="⚙️ Voces",
            bg="#313244",
            fg="#cdd6f4",
            activebackground="#45475a",
            activeforeground="#ffffff",
            relief="flat",
            font=("Segoe UI", 9),
            cursor="hand2",
            padx=8,
            pady=4,
            command=self.show_voice_menu
        )
        self.btn_menu.pack(side="left", padx=4)

    def toggle_plan(self):
        def _call_plan():
            try:
                import urllib.request
                req = urllib.request.Request(
                    "http://127.0.0.1:49152/plan/speak",
                    data=b'{"action":"toggle"}',
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=2.0) as resp:
                    pass
            except Exception as e:
                print(f"Error llamando a toggle plan: {e}")
        import threading
        threading.Thread(target=_call_plan, daemon=True).start()

    def toggle_mute(self):
        self.config = load_config()
        self.config["enabled"] = not self.config.get("enabled", True)
        save_config(self.config)
        self.update_state_from_config()

    def stop_audio(self):
        try:
            with open(STOP_FILE, "w", encoding="utf-8") as f:
                f.write("stop")
        except Exception:
            pass

    def show_voice_menu(self):
        menu = tk.Menu(self.root, tearoff=0, bg="#1e1e2e", fg="#cdd6f4", activebackground="#313244", activeforeground="#ffffff")
        current_voice = self.config.get("voice", "es-MX-DaliaNeural")
        
        for name, v_id in VOICES:
            prefix = "✓ " if v_id == current_voice else "   "
            menu.add_command(
                label=f"{prefix}{name}",
                command=lambda vid=v_id: self.change_voice(vid)
            )

        menu.add_separator()
        menu.add_command(label="⏹️ Detener audio actual", command=self.stop_audio)

        x = self.root.winfo_rootx() + self.btn_menu.winfo_x()
        y = self.root.winfo_rooty() + self.btn_menu.winfo_y() + 32
        menu.post(x, y)

    def change_voice(self, voice_id):
        self.config = load_config()
        self.config["voice"] = voice_id
        save_config(self.config)

    def update_state_from_config(self):
        enabled = self.config.get("enabled", True)
        if enabled:
            self.btn_toggle.configure(text="🎙️ Voz: ACTIVA", bg="#2e7d32", fg="#ffffff")
        else:
            self.btn_toggle.configure(text="🔇 SILENCIADO", bg="#5c6370", fg="#ffdddd")

    def poll_config_changes(self):
        new_cfg = load_config()
        if new_cfg.get("enabled") != self.config.get("enabled"):
            self.config = new_cfg
            self.update_state_from_config()
        self.root.after(800, self.poll_config_changes)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = FloatingVoiceWidget()
    app.run()
