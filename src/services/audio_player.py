import os
import re
import threading
from typing import Dict, Any, Optional
import pygame
from utils.config import log, load_config, LAST_SPEECH_FILE
from utils.text_cleaner import TextCleaner
from services.plan_narrator import PlanNarrator
from services.playback_worker import run_playback_worker

class AudioPlayer:
    def __init__(self, config: Dict[str, Any]):
        self.config, self.lock = config, threading.Lock()
        self.is_playing = self.is_paused = self.is_synthesizing = self.stop_requested = self.is_reading_plan = False
        self.current_plan_path = self.current_sig = self.current_turn_id = self.last_text = ""
        self.play_id = 0
        self.brain_dirs = [
            os.path.expanduser(r"~\.gemini\antigravity-ide\brain"),
            os.path.expanduser(r"~\.gemini\antigravity\brain"),
            os.path.expanduser(r"~\.gemini\antigravity-cli\brain")
        ]
        pygame.mixer.init()

    @staticmethod
    def get_text_sig(text: str) -> str:
        return re.sub(r"[^a-z0-9áéíóúñü]+", "", (text or "").lower())[:60]

    def _matches_current(self, cleaned: str) -> bool:
        if not cleaned or not self.current_sig: return not cleaned
        sig = self.get_text_sig(cleaned)
        p_len = min(35, len(sig), len(self.current_sig))
        return p_len > 0 and sig[:p_len] == self.current_sig[:p_len]

    def pause_playback(self) -> bool:
        with self.lock:
            if self.is_playing and not self.is_paused:
                if pygame.mixer.get_init(): pygame.mixer.music.pause()
                self.is_paused, self.is_playing = True, False
                log("\n[⏸️] Lectura en pausa.")
                return True
        return False

    def resume_playback(self) -> bool:
        with self.lock:
            if self.is_paused:
                if pygame.mixer.get_init(): pygame.mixer.music.unpause()
                self.is_paused, self.is_playing = False, True
                log("\n[▶️] Continuando lectura...")
                return True
        return False

    def stop_playback(self, quiet: bool = False):
        with self.lock:
            self.stop_requested, self.is_paused, self.is_playing = True, False, False
            self.is_synthesizing, self.is_reading_plan = False, False
            self.current_plan_path = self.current_turn_id = ""
            if pygame.mixer.get_init(): pygame.mixer.music.stop()
        if not quiet: log("\n[⏹️] Reproducción detenida.")

    def replay_last(self):
        if not self.last_text and os.path.exists(LAST_SPEECH_FILE):
            try:
                with open(LAST_SPEECH_FILE, "r", encoding="utf-8") as f: self.last_text = f.read().strip()
            except Exception: pass
        if self.last_text:
            log("\n[🔁] Repitiendo respuesta...")
            self.play_text(self.last_text, force=True)

    def toggle_or_speak(self, text: str, force_restart: bool = False, turn_id: str = "") -> str:
        self.config = load_config()
        cleaned = TextCleaner.clean_for_speech(text, self.config.get("announce_code_blocks", True), self.config.get("max_characters", 0)) if text else ""
        if not force_restart and ((turn_id and self.current_turn_id == turn_id) or self._matches_current(cleaned)):
            if self.is_playing and not self.is_paused: return "paused" if self.pause_playback() else "idle"
            if self.is_paused: return "playing" if self.resume_playback() else "idle"
        if text and text.strip():
            self.play_text(text, force=True, turn_id=turn_id)
            return "playing"
        return "idle"

    def toggle_plan_speech(self, plan_path: Optional[str] = None, force_restart: bool = False, conv_id: Optional[str] = None) -> str:
        return PlanNarrator.toggle_plan(self, plan_path, force_restart, conv_id)

    def play_text(self, text: str, force: bool = False, turn_id: str = ""):
        self.config = load_config()
        if not force and not self.config.get("enabled", True): return
        cleaned = TextCleaner.clean_for_speech(text, self.config.get("announce_code_blocks", True), self.config.get("max_characters", 0))
        if not cleaned: return
        if turn_id != "plan":
            self.last_text = text.strip()
            try:
                with open(LAST_SPEECH_FILE, "w", encoding="utf-8") as f: f.write(self.last_text)
            except Exception: pass
        with self.lock:
            self.play_id += 1
            my_id = self.play_id
            self.stop_requested, self.is_paused = False, False
            self.is_playing, self.is_synthesizing = True, True
            self.current_sig, self.current_turn_id = self.get_text_sig(cleaned), turn_id
            if pygame.mixer.get_init(): pygame.mixer.music.stop()
        threading.Thread(target=run_playback_worker, args=(self, cleaned, my_id), daemon=True).start()
