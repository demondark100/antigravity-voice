import os
import glob
import time
import json
from typing import Dict, Any, List
from utils.config import log, REPLAY_FILE

class AntigravityConversationWatcher:
    def __init__(self, player):
        self.player, self.brain_dirs = player, player.brain_dirs
        self.file_states: Dict[str, Dict[str, Any]] = {}

    def get_surface_name(self, path: str) -> str:
        if "antigravity-ide" in path: return "Antigravity IDE"
        if "antigravity-cli" in path: return "Antigravity CLI"
        return "Antigravity 2.0"

    def find_recent_transcripts(self, limit: int = 15) -> List[str]:
        files = []
        for bdir in self.brain_dirs:
            if os.path.exists(bdir):
                files.extend(glob.glob(os.path.join(bdir, "*", ".system_generated", "logs", "transcript.jsonl")))
        if not files: return []
        files.sort(key=os.path.getmtime, reverse=True)
        return files[:limit]

    def initialize_file_state(self, path: str, at_eof: bool = True):
        surface = self.get_surface_name(path)
        conv_id = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(path))))
        log(f"[📡] Sintonizado con {surface} (Chat: {conv_id[:8]}...)")
        seen, pos = set(), 0
        if at_eof and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        try:
                            idx = json.loads(line).get("step_index")
                            if idx is not None: seen.add(idx)
                        except Exception: pass
                    pos = f.tell()
            except Exception: pos = 0
        self.file_states[path] = {"pos": pos, "seen": seen, "surface": surface, "conv_id": conv_id}

    def _read_full_content(self, path: str, step: Dict[str, Any]) -> str:
        content = step.get("content") or ""
        if "content" not in (step.get("truncated_fields") or []): return content
        full = os.path.join(os.path.dirname(path), "transcript_full.jsonl")
        if not os.path.exists(full): return content
        try:
            with open(full, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    try:
                        st = json.loads(line)
                        if st.get("step_index") == step.get("step_index"): return st.get("content") or content
                    except Exception: pass
        except Exception: pass
        return content

    def check_for_new_responses(self):
        if os.path.exists(REPLAY_FILE):
            try: os.remove(REPLAY_FILE)
            except Exception: pass
            self.player.replay_last()
        for path in self.find_recent_transcripts(10):
            if path not in self.file_states: self.initialize_file_state(path, at_eof=False)
            st = self.file_states[path]
            try:
                if not os.path.exists(path) or os.path.getsize(path) == st["pos"]: continue
                if os.path.getsize(path) < st["pos"]: st["pos"] = 0
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    f.seek(st["pos"])
                    lines = f.readlines()
                    st["pos"] = f.tell()
                for line in lines:
                    if not line.strip(): continue
                    try:
                        step = json.loads(line)
                        idx = step.get("step_index")
                        if idx in st["seen"]: continue
                        st["seen"].add(idx)
                        if step.get("source") == "MODEL" and step.get("type") == "PLANNER_RESPONSE" and step.get("content") and not step.get("tool_calls"):
                            full = self._read_full_content(path, step)
                            log(f"\n[✨ {st['surface']}] Respuesta en chat {st['conv_id'][:8]}...")
                            self.player.play_text(full)
                    except Exception: continue
            except Exception: pass

    def run_loop(self):
        log("\n" + "="*60)
        log("  🎙️ ANTIGRAVITY VOICE ASSISTANT (TTS Neuronal)")
        log("="*60)
        log(f"• Voz activa:     {self.player.config.get('voice')}")
        log(f"• Velocidad:      {self.player.config.get('rate')}")
        log("• Atajo Silencio: [Ctrl + Alt + S] para detener voz actual")
        log("• Atajo Repetir:  [Ctrl + Alt + R] para repetir respuesta")
        log("• Atajo Plan:     [Ctrl + Alt + P] para leer / pausar Plan")
        log("• Atajo Mute:     [Ctrl + Alt + M] para silenciar/activar")
        log("="*60)
        for t in self.find_recent_transcripts(500): self.initialize_file_state(t, at_eof=True)
        log("\n[🟢] Asistente escuchando activamente en segundo plano...")
        while True:
            self.check_for_new_responses()
            time.sleep(0.4)
