import os
import sys
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

class SetupWizard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Instalador - Antigravity Voice")
        self.root.geometry("460x360")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(False, False)
        self.base_dir = get_base_dir()
        self.install_dir = os.path.expandvars(r"%LOCALAPPDATA%\AntigravityVoice")
        self.gemini_dir = os.path.expanduser(r"~\.gemini\config\sidecars\voice-reader")
        self.setup_ui()

    def setup_ui(self):
        pad = {"padx": 20, "pady": 6}
        lbl_title = tk.Label(self.root, text="🎙️ Antigravity Voice Assistant", font=("Segoe UI", 14, "bold"), fg="#ffffff", bg="#1e1e2e")
        lbl_title.pack(padx=20, pady=(16, 4))

        lbl_sub = tk.Label(self.root, text="Asistente de Voz Neuronal y Lector de Planes", font=("Segoe UI", 9), fg="#94a3b8", bg="#1e1e2e")
        lbl_sub.pack(padx=20, pady=(0, 12))

        self.txt_status = tk.Text(self.root, height=7, bg="#11111b", fg="#cdd6f4", font=("Consolas", 9), relief="flat", padx=8, pady=8)
        self.txt_status.pack(fill="x", padx=20, pady=4)
        self.log("[*] Listo para instalar en: " + self.install_dir)

        self.progress = ttk.Progressbar(self.root, mode="determinate")
        self.progress.pack(fill="x", padx=20, pady=12)

        self.btn_install = tk.Button(self.root, text="Instalar Ahora", font=("Segoe UI", 10, "bold"), bg="#0284c7", fg="#ffffff", activebackground="#0369a1", activeforeground="#ffffff", relief="flat", cursor="hand2", padx=16, pady=8, command=self.start_install)
        self.btn_install.pack(pady=8)

    def log(self, msg):
        self.txt_status.insert(tk.END, msg + "\n")
        self.txt_status.see(tk.END)

    def start_install(self):
        self.btn_install.config(state="disabled", text="Instalando...")
        threading.Thread(target=self._run_install, daemon=True).start()

    def _run_install(self):
        try:
            self.progress["value"] = 10
            self.log("[1/4] Creando directorios...")
            os.makedirs(os.path.join(self.install_dir, "bin"), exist_ok=True)
            os.makedirs(os.path.join(self.install_dir, ".audio_cache"), exist_ok=True)
            os.makedirs(self.gemini_dir, exist_ok=True)

            self.progress["value"] = 35
            self.log("[2/4] Desplegando binarios standalone...")
            bin_source = os.path.join(self.base_dir, "bin") if os.path.exists(os.path.join(self.base_dir, "bin")) else self.base_dir
            for f in os.listdir(bin_source):
                if f.endswith(".exe") or f.endswith(".json") or f.endswith(".py"):
                    shutil.copy2(os.path.join(bin_source, f), os.path.join(self.install_dir, "bin" if f.endswith(".exe") else self.install_dir))

            self.progress["value"] = 65
            self.log("[3/4] Registrando tarea en Windows (Inicio automático)...")
            ps_script = os.path.join(self.base_dir, "installer", "setup_task.ps1")
            if not os.path.exists(ps_script):
                ps_script = os.path.join(self.base_dir, "setup_task.ps1")
            if os.path.exists(ps_script):
                subprocess.call(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_script, "-InstallDir", self.install_dir])

            self.progress["value"] = 85
            self.log("[4/4] Creando accesos directos...")
            vbs_script = os.path.join(self.base_dir, "installer", "create_shortcuts.vbs")
            if not os.path.exists(vbs_script):
                vbs_script = os.path.join(self.base_dir, "create_shortcuts.vbs")
            if os.path.exists(vbs_script):
                subprocess.call(["cscript", "//nologo", vbs_script])

            self.progress["value"] = 100
            self.log("\n[OK] ¡Instalación completada con éxito!")
            self.btn_install.config(state="normal", text="¡Listo! Cerrar", bg="#16a34a", command=self.root.destroy)

            widget_exe = os.path.join(self.install_dir, "bin", "AntigravityVoiceWidget.exe")
            if os.path.exists(widget_exe):
                subprocess.Popen([widget_exe])
        except Exception as e:
            self.log(f"[!] Error: {e}")
            self.btn_install.config(state="normal", text="Reintentar", bg="#dc2626")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    SetupWizard().run()
