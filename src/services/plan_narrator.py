import os
from typing import Optional
from utils.config import log, load_config
from plan_manager import PlanTextCleaner, find_latest_plan

class PlanNarrator:
    @staticmethod
    def toggle_plan(player, plan_path: Optional[str] = None, force_restart: bool = False, conv_id: Optional[str] = None) -> str:
        same_plan = not plan_path or (player.current_plan_path and os.path.abspath(plan_path) == os.path.abspath(player.current_plan_path))
        if player.is_reading_plan and not force_restart and same_plan:
            if player.is_playing and not player.is_paused:
                player.pause_playback()
                return "paused"
            if player.is_paused:
                player.resume_playback()
                return "playing"

        if not plan_path:
            plan_path = find_latest_plan(player.brain_dirs, conv_id)
        if not plan_path or not os.path.exists(plan_path):
            return "no_plan"

        try:
            with open(plan_path, "r", encoding="utf-8", errors="ignore") as f:
                speech, title = PlanTextCleaner.clean_plan_for_speech(f.read(), load_config().get("max_characters", 0))
            if not speech:
                return "no_plan"

            log(f"\n[📋 PLAN NARRATOR] Leyendo: {title}\nArchivo: {plan_path}")
            player.is_reading_plan, player.current_plan_path = True, plan_path
            player.play_text(speech, force=True, turn_id="plan")
            player.is_reading_plan, player.current_plan_path = True, plan_path
            return "playing"
        except Exception as e:
            log(f"[!] Error leyendo plan: {e}")
            return "error"
