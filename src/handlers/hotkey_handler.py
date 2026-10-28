from typing import Dict, Any
from utils.config import log, save_config

try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

def setup_global_hotkeys(player, config: Dict[str, Any]):
    if not PYNPUT_AVAILABLE or not config.get("hotkeys_enabled", True):
        return

    current_keys = set()

    def on_press(key):
        current_keys.add(key)
        is_ctrl = any(k in current_keys for k in [keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r])
        is_alt = any(k in current_keys for k in [keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr])

        try:
            if is_ctrl and is_alt and hasattr(key, 'char') and key.char:
                ch = key.char.lower()
                if ch == 's':
                    player.stop_playback()
                elif ch == 'r':
                    player.replay_last()
                elif ch == 'p':
                    player.toggle_plan_speech()
                elif ch == 'm':
                    config["enabled"] = not config.get("enabled", True)
                    state = "ACTIVADA" if config["enabled"] else "SILENCIADA"
                    log(f"\n[🔔] Voz {state} por atajo.")
                    save_config(config)
        except Exception:
            pass

    def on_release(key):
        current_keys.discard(key)

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.daemon = True
    listener.start()
