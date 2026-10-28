import os
import time
import pygame
from utils.config import log, CACHE_DIR, STOP_FILE
from services.tts_synthesizer import TTSSynthesizer

def run_playback_worker(player, text: str, my_id: int):
    cache = os.path.join(CACHE_DIR, f"speech_{int(time.time()*1000)}_{my_id}.mp3")
    try:
        ok = TTSSynthesizer.synthesize_to_file(
            text, player.config.get("voice", "es-MX-DaliaNeural"),
            player.config.get("rate", "+10%"), player.config.get("volume", "+0%"),
            cache, lambda: player.stop_requested or player.play_id != my_id
        )
        if not ok: return
        with player.lock:
            player.is_synthesizing = False
            if player.stop_requested or player.play_id != my_id: return
        pygame.mixer.music.load(cache)
        pygame.mixer.music.play()
        while (pygame.mixer.music.get_busy() or player.is_paused) and not player.stop_requested and player.play_id == my_id:
            if os.path.exists(STOP_FILE):
                try: os.remove(STOP_FILE)
                except Exception: pass
                player.stop_playback()
                break
            time.sleep(0.08)
    except Exception as e:
        log(f"[!] Error reproducción: {e}")
    finally:
        with player.lock:
            if player.play_id == my_id:
                player.is_playing = player.is_paused = player.is_synthesizing = player.is_reading_plan = False
                player.current_plan_path = player.current_turn_id = ""
                try:
                    if pygame.mixer.get_init(): pygame.mixer.music.unload()
                except Exception: pass
        try:
            if os.path.exists(cache): os.remove(cache)
        except Exception: pass
