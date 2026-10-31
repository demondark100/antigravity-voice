import os
import glob
import re
from typing import Optional, Tuple, List

class PlanTextCleaner:
    @staticmethod
    def clean_plan_for_speech(markdown_text: str, max_chars: int = 0) -> Tuple[str, str]:
        if not markdown_text or not markdown_text.strip():
            return ("", "Plan")

        text = markdown_text
        title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        raw_title = title_match.group(1).strip() if title_match else "Plan de Implementación"
        clean_title = re.sub(r"^(Implementation Plan\s*[:-]\s*|Plan de Implementación\s*[:-]\s*)", "", raw_title, flags=re.I).strip()
        clean_title = re.sub(r"[\U00010000-\U0010ffff]", "", clean_title).strip()

        text = re.sub(r"^#\s+.+$", "", text, flags=re.MULTILINE)
        text = re.sub(r"```mermaid\n[\s\S]*?```", " [He incluido un diagrama de arquitectura en pantalla]. ", text, flags=re.I)
        text = re.sub(r"```[\w\-]*\n[\s\S]*?```", " [He incluido un bloque de código técnico en pantalla]. ", text)
        text = re.sub(r"`([^`]+)`", r"\1", text)
        text = re.sub(r"\[([^\]]+)\]\(file:///[^\)]+\)", r"\1", text)
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        text = re.sub(r"!\[[^\]]*\]\([^\)]+\)", "", text)
        text = re.sub(r"[A-Za-z]:\\[\w\.\-\\]+\\([\w\.\-]+)", r"la ruta \1", text)
        text = re.sub(r"####?\s*\[NEW\]\s*", "Crear archivo nuevo: ", text, flags=re.I)
        text = re.sub(r"####?\s*\[UPDATE\]\s*", "Modificar archivo: ", text, flags=re.I)
        text = re.sub(r"####?\s*\[DELETE\]\s*", "Eliminar archivo: ", text, flags=re.I)
        text = re.sub(r"^\s*>\s*\[!(IMPORTANT|WARNING|CAUTION)\][ \t]*\n?", "Atención requerida: \n", text, flags=re.M | re.I)
        text = re.sub(r"^\s*>\s*\[!(NOTE|TIP)\][ \t]*\n?", "Nota: \n", text, flags=re.M | re.I)
        text = re.sub(r"^\s*>\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*#{2,6}\s*(.+)$", r". \1. ", text, flags=re.MULTILINE)
        text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
        text = re.sub(r"(\*|_)(.*?)\1", r"\2", text)
        text = re.sub(r"^\s*[-*+]\s*\[\s*\]\s*", "Pendiente: ", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*[-*+]\s*\[x\]\s*", "Completado: ", text, flags=re.MULTILINE | re.I)
        text = re.sub(r"^\s*[-*+]\s+", ". ", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*\d+\.\s+", ". ", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"\|[-:\s|]+\|", "", text)
        text = re.sub(r"\|", " ", text)
        text = re.sub(r"[\U00010000-\U0010ffff]", "", text)
        text = re.sub(r"\n{2,}", ". \n", text)
        text = re.sub(r"\n", " ", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\s+\.", ".", text)
        text = re.sub(r"\.{2,}", ".", text)

        cleaned = text.strip()
        speech = f"Plan de implementación: {clean_title}. {cleaned}"
        if max_chars and max_chars > 0 and len(speech) > max_chars:
            speech = speech[:max_chars] + " ... El resto del plan continúa en pantalla."
        return speech, clean_title

import time
def find_latest_plan(brain_dirs: List[str], conv_id: Optional[str] = None) -> Optional[str]:
    candidates = []
    if conv_id:
        for bdir in brain_dirs:
            conv_folder = os.path.join(bdir, conv_id)
            if os.path.isdir(conv_folder):
                for p in glob.glob(os.path.join(conv_folder, "*plan*.md")):
                    if not p.endswith(".metadata.json"):
                        candidates.append(p)
        if candidates:
            candidates.sort(key=os.path.getmtime, reverse=True)
            return candidates[0]
        return None
    cutoff = time.time() - (6 * 3600)
    for bdir in brain_dirs:
        if os.path.isdir(bdir):
            for p in glob.glob(os.path.join(bdir, "*", "*plan*.md")):
                if not p.endswith(".metadata.json") and os.path.getmtime(p) > cutoff:
                    candidates.append(p)
    if not candidates:
        return None
    candidates.sort(key=os.path.getmtime, reverse=True)
    return candidates[0]

def get_plan_info(brain_dirs: List[str], conv_id: Optional[str] = None) -> Tuple[Optional[str], str]:
    plan_path = find_latest_plan(brain_dirs, conv_id)
    if not plan_path or not os.path.exists(plan_path):
        return None, ""
    try:
        with open(plan_path, "r", encoding="utf-8", errors="ignore") as f:
            first_lines = [f.readline() for _ in range(10)]
        for line in first_lines:
            m = re.match(r"^#\s+(.+)$", line.strip())
            if m:
                title = re.sub(r"^(Implementation Plan\s*[:-]\s*|Plan de Implementación\s*[:-]\s*)", "", m.group(1), flags=re.I).strip()
                return plan_path, re.sub(r"[\U00010000-\U0010ffff]", "", title).strip()
    except Exception:
        pass
    return plan_path, "Plan de Implementación"
