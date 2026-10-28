import os
import sys
import time
import json
import ctypes
from typing import Dict, Any

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
LOG_FILE = os.path.join(BASE_DIR, "voice_reader.log")
CACHE_DIR = os.path.join(BASE_DIR, ".audio_cache")
STOP_FILE = os.path.join(BASE_DIR, ".stop_trigger")
REPLAY_FILE = os.path.join(BASE_DIR, ".replay_trigger")
LAST_SPEECH_FILE = os.path.join(BASE_DIR, ".last_speech.txt")
HTTP_PORT = 49152
os.makedirs(CACHE_DIR, exist_ok=True)

DEFAULT_CONFIG: Dict[str, Any] = {
    "voice": "es-MX-DaliaNeural",
    "rate": "+10%",
    "volume": "+0%",
    "announce_code_blocks": True,
    "max_characters": 0,
    "enabled": True,
    "hotkeys_enabled": True
}

_APP_MUTEX = None

def check_single_instance():
    global _APP_MUTEX
    try:
        kernel32 = ctypes.windll.kernel32
        ERROR_ALREADY_EXISTS = 183
        _APP_MUTEX = kernel32.CreateMutexW(None, False, "AntigravityVoiceReader_Mutex_Unique")
        if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
            log("[!] Otra instancia activa ya está corriendo (Mutex ocupado). Saliendo.")
            sys.exit(0)
    except Exception as e:
        log(f"[!] Error comprobando mutex: {e}")

def log(msg: str = ""):
    try:
        print(msg, flush=True)
    except Exception:
        pass
    try:
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 512 * 1024:
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write(f"--- Log rotado {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    except Exception:
        pass

def load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                return {**DEFAULT_CONFIG, **cfg}
        except Exception as e:
            log(f"[!] Error leyendo config.json ({e}), usando predeterminados.")
    return DEFAULT_CONFIG.copy()

def save_config(config: Dict[str, Any]):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        log(f"[!] Error guardando config.json: {e}")
