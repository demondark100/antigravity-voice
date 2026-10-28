import os
import sys

# Asegurar importación de subpaquetes locales
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

from utils.config import check_single_instance, load_config, log
from services.audio_player import AudioPlayer
from services.http_server import start_local_http_server
from services.transcript_watcher import AntigravityConversationWatcher
from handlers.cdp_injector import start_cdp_button_injector
from handlers.hotkey_handler import setup_global_hotkeys

def main():
    check_single_instance()
    config = load_config()
    player = AudioPlayer(config)
    start_local_http_server(player)
    start_cdp_button_injector()
    setup_global_hotkeys(player, config)
    watcher = AntigravityConversationWatcher(player)

    try:
        watcher.run_loop()
    except KeyboardInterrupt:
        log("\n[👋] Antigravity Voice Assistant detenido correctamente.")
        player.stop_playback()
        sys.exit(0)
    except Exception as e:
        import traceback
        log(f"[💥 CRASH] Error fatal: {e}\n{traceback.format_exc()}")
        time_sleep = __import__("time").sleep(2)

if __name__ == "__main__":
    main()
