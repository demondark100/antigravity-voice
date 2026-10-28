import os
import sys
import time
import json
import glob
import re
import asyncio
import tempfile
import threading
from typing import Optional, Dict, Any
from plan_manager import PlanTextCleaner, find_latest_plan, get_plan_info

# Configurar salida segura UTF-8 para consolas Windows
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import ctypes

# Silenciar prompt de pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

_APP_MUTEX = None

def check_single_instance():
    global _APP_MUTEX
    try:
        kernel32 = ctypes.windll.kernel32
        ERROR_ALREADY_EXISTS = 183
        _APP_MUTEX = kernel32.CreateMutexW(None, False, "AntigravityVoiceReader_Mutex_Unique")
        if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
            # Otra instancia activa ya está corriendo
            log("[!] Otra instancia activa ya está corriendo (Mutex ocupado). Saliendo.")
            sys.exit(0)
    except Exception as e:
        log(f"[!] Error comprobando mutex: {e}")

# Third-party libraries
try:
    import edge_tts
    import edge_tts.constants
    import edge_tts.communicate
    import pygame
    # Ensure Microsoft Edge 155+ WebSocket endpoint is used (fixes HTTP 403 on legacy bing endpoint)
    _NEW_WSS_URL = (
        "wss://api.msedgeservices.com/tts/cognitiveservices/websocket/v1"
        f"?Ocp-Apim-Subscription-Key={edge_tts.constants.TRUSTED_CLIENT_TOKEN}"
    )
    edge_tts.constants.WSS_URL = _NEW_WSS_URL
    edge_tts.communicate.WSS_URL = _NEW_WSS_URL
except ImportError as e:
    print(f"Error importando dependencias: {e}")
    print("Ejecuta: pip install edge-tts pygame pynput")
    sys.exit(1)

# Optional global hotkeys via pynput
try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
LOG_FILE = os.path.join(BASE_DIR, "voice_reader.log")
CACHE_DIR = os.path.join(BASE_DIR, ".audio_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

DEFAULT_CONFIG = {
    "voice": "es-MX-DaliaNeural",
    "rate": "+10%",
    "volume": "+0%",
    "announce_code_blocks": True,
    "max_characters": 0,
    "enabled": True,
    "hotkeys_enabled": True
}

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
            log(f"[!] Error leyendo config.json ({e}), usando valores predeterminados.")
    return DEFAULT_CONFIG.copy()

def save_config(config: Dict[str, Any]):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        log(f"[!] Error guardando config.json: {e}")

class TextCleaner:
    @staticmethod
    def clean_for_speech(text: str, announce_code: bool = True, max_chars: int = 0) -> str:
        if not text:
            return ""

        # 1. Tratar bloques de código PRIMERO para no inflar la longitud del texto
        if announce_code:
            text = re.sub(r"```[\w\-]*\n[\s\S]*?```", " [He incluido un bloque de código en pantalla]. ", text)
        else:
            text = re.sub(r"```[\w\-]*\n[\s\S]*?```", " ", text)

        # 2. Código inline
        text = re.sub(r"`([^`]+)`", r"\1", text)

        # 3. Enlaces Markdown [texto](url) -> texto
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)

        # 4. Imágenes Markdown ![alt](url) -> remover
        text = re.sub(r"!\[[^\]]*\]\([^\)]+\)", "", text)

        # 5. Negrita y cursiva
        text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
        text = re.sub(r"(\*|_)(.*?)\1", r"\2", text)

        # 6. Encabezados (#, ##, ###)
        text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)

        # 7. Citas (> [!NOTE], etc.)
        text = re.sub(r"^\s*>\s*(\[![\w]+\])?\s*", "", text, flags=re.MULTILINE)

        # 8. Viñetas y listas numeradas
        text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)

        # 9. Separadores horizontales (---, ***, ___)
        text = re.sub(r"^\s*[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

        # 10. Tablas Markdown
        text = re.sub(r"\|[-:\s|]+\|", "", text)
        text = re.sub(r"\|", " ", text)

        # 11. Múltiples saltos de línea a pausas naturales
        text = re.sub(r"\n{2,}", ". \n", text)
        text = re.sub(r"\n", " ", text)
        text = re.sub(r"[ \t]+", " ", text)

        text = text.strip()

        # 12. Truncado opcional: solo si max_chars es mayor que 0
        if max_chars and max_chars > 0 and len(text) > max_chars:
            text = text[:max_chars] + " ... [El resto de la respuesta continúa en pantalla]."

        return text


STOP_FILE = os.path.join(BASE_DIR, ".stop_trigger")
REPLAY_FILE = os.path.join(BASE_DIR, ".replay_trigger")
LAST_SPEECH_FILE = os.path.join(BASE_DIR, ".last_speech.txt")
HTTP_PORT = 49152

UI_INJECTOR_JS = r"""
(function() {
    if (window.__agyVoiceBtnVersion === 5) return "already_injected";
    window.__agyVoiceBtnVersion = 5;
    window.__agyVoiceBtnInjected = true;

    const SPEAKER_PATH = "M560-131v-82q90-26 145-100t55-168q0-94-55-168T560-749v-82q124 28 202 125.5T840-481q0 127-78 224.5T560-131ZM120-360v-240h160l200-200v640L280-360H120Zm440 40v-322q47 22 73.5 66t26.5 96q0 51-26.5 94.5T560-320ZM400-606l-86 86H200v80h114l86 86v-252ZM300-480Z";
    const PAUSE_PATH = "M520-200v-560h240v560H520Zm-320 0v-560h240v560H200Zm400-80h80v-400h-80v400Zm-320 0h80v-400h-80v400Zm0-400v400-400Zm320 0v400-400Z";
    const PLAY_PATH = "M320-200v-560l440 280-440 280Zm80-280Zm0 134 210-134-210-134v268Z";
    const RESTART_PATH = "M480-80q-75 0-140.5-28.5t-114-77q-48.5-48.5-77-114T120-440h80q0 117 81.5 198.5T480-160q117 0 198.5-81.5T760-440q0-117-81.5-198.5T480-720h-6l62 62-56 58-160-160 160-160 56 58-62 62h6q75 0 140.5 28.5t114 77q48.5 48.5 77 114T840-440q0 75-28.5 140.5t-77 114q-48.5 48.5-114 77T480-80Z";
    const CLIPBOARD_PATH = "M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h168q13-36 43.5-58t68.5-22q38 0 68.5 22t43.5 58h168q33 0 56.5 23.5T840-760v560q0 33-23.5 56.5T760-120H200Zm0-80h560v-560H200v560Zm280-590q17 0 28.5-11.5T520-830q0-17-11.5-28.5T480-870q-17 0-28.5 11.5T440-830q0 17 11.5 28.5T480-790ZM280-360h400v-60H280v60Zm0-120h400v-60H280v60Zm0-120h400v-60H280v60Z";

    function createSvgIcon(pathData, size) {
        if (!size) size = 16;
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("width", String(size));
        svg.setAttribute("height", String(size));
        svg.setAttribute("viewBox", "0 -960 960 960");
        svg.setAttribute("fill", "currentColor");
        svg.setAttribute("class", "agy-voice-icon");
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", pathData);
        svg.appendChild(path);
        return svg;
    }

    function setBtnIcon(btn, pathData, size) {
        while (btn.firstChild) btn.removeChild(btn.firstChild);
        btn.appendChild(createSvgIcon(pathData, size || 16));
    }

    function getTextSig(text) {
        return (text || "").toLowerCase().replace(/[^a-z0-9áéíóúñü]+/g, "").slice(0, 60);
    }

    function setBtnState(btn, restartBtn, state) {
        btn.dataset.voiceState = state;
        if (state === "playing") {
            setBtnIcon(btn, PAUSE_PATH, 16);
            btn.style.color = "#38bdf8";
            btn.title = "Pausar lectura de voz";
            if (restartBtn) restartBtn.style.display = "inline-flex";
        } else if (state === "paused") {
            setBtnIcon(btn, PLAY_PATH, 16);
            btn.style.color = "#4ade80";
            btn.title = "Continuar lectura desde donde se quedó";
            if (restartBtn) restartBtn.style.display = "inline-flex";
        } else {
            setBtnIcon(btn, SPEAKER_PATH, 16);
            btn.style.color = "";
            btn.title = "Leer respuesta en voz alta (J.A.R.V.I.S.)";
            if (restartBtn) restartBtn.style.display = "none";
        }
    }

    function extractTurnText(copyBtn) {
        try {
            const footer = copyBtn.closest('.pt-3') || (copyBtn.parentElement && copyBtn.parentElement.parentElement && copyBtn.parentElement.parentElement.parentElement && copyBtn.parentElement.parentElement.parentElement.parentElement);
            let body = (footer && footer.previousElementSibling) ? footer.previousElementSibling : null;
            if (!body) {
                body = copyBtn.closest('[role="article"][aria-label="Agent response"]') || 
                       (footer && footer.parentElement && footer.parentElement.querySelector('[role="article"][aria-label="Agent response"]'));
            }
            if (body) {
                let blocks = Array.from(body.querySelectorAll('.px-2.py-1')).filter(function(el) {
                    if (el.closest('button')) return false;
                    if (el.closest('[data-testid="worked-for-collapsible"]')) return false;
                    let p = el.parentElement;
                    while (p && p !== body) {
                        const prev = p.previousElementSibling;
                        if (prev && prev.tagName === 'BUTTON' && (prev.hasAttribute('aria-expanded') || prev.getAttribute('data-testid') === 'worked-for-collapsible')) {
                            return false;
                        }
                        p = p.parentElement;
                    }
                    return true;
                });

                if (blocks.length === 0) {
                    const clone = body.cloneNode(true);
                    clone.querySelectorAll('style, script, button, .select-none, [data-testid="worked-for-collapsible"]').forEach(function(s) { s.remove(); });
                    clone.querySelectorAll('pre').forEach(function(pre) {
                        pre.textContent = ' [He incluido un bloque de código en pantalla]. ';
                    });
                    const fullText = (clone.textContent || '').trim();
                    if (fullText && fullText !== 'User cancelled agent execution.') {
                        return fullText;
                    }
                }

                const texts = blocks.map(function(b) {
                    const clone = b.cloneNode(true);
                    clone.querySelectorAll('style, script, button, .select-none').forEach(function(s) { s.remove(); });
                    clone.querySelectorAll('pre').forEach(function(pre) {
                        pre.textContent = ' [He incluido un bloque de código en pantalla]. ';
                    });
                    return (clone.textContent || '').trim();
                }).filter(function(t) { return t && t !== 'User cancelled agent execution.'; });
                if (texts.length > 0) {
                    return texts.join('\n\n');
                }
            }
        } catch (e) {}
        return "";
    }

    function getOrCreateFloatingPlanPill() {
        let pill = document.getElementById("agy-floating-plan-pill");
        if (!pill) {
            pill = document.createElement("div");
            pill.id = "agy-floating-plan-pill";
            pill.style.position = "fixed";
            pill.style.bottom = "68px";
            pill.style.right = "24px";
            pill.style.zIndex = "999999";
            pill.style.display = "none";
            pill.style.alignItems = "center";
            pill.style.gap = "8px";
            pill.style.padding = "6px 14px";
            pill.style.borderRadius = "20px";
            pill.style.fontSize = "12px";
            pill.style.fontWeight = "600";
            pill.style.fontFamily = "Segoe UI, -apple-system, BlinkMacSystemFont, sans-serif";
            pill.style.cursor = "pointer";
            pill.style.userSelect = "none";
            pill.style.transition = "all 0.2s ease";
            pill.style.boxShadow = "0 4px 14px rgba(0,0,0,0.35)";
            pill.style.backdropFilter = "blur(10px)";

            const iconSpan = document.createElement("span");
            iconSpan.className = "agy-plan-icon-span";
            iconSpan.style.display = "inline-flex";
            iconSpan.style.alignItems = "center";

            const labelSpan = document.createElement("span");
            labelSpan.className = "agy-plan-label-span";
            labelSpan.textContent = "Leer Plan";

            pill.appendChild(iconSpan);
            pill.appendChild(labelSpan);
            document.body.appendChild(pill);

            pill.addEventListener("click", async function(e) {
                e.preventDefault();
                e.stopPropagation();
                if (pill.dataset.isBusy === "1") return;
                pill.dataset.isBusy = "1";
                setTimeout(function() { delete pill.dataset.isBusy; }, 600);

                try {
                    const res = await fetch("http://127.0.0.1:49152/plan/speak", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ action: "toggle" })
                    });
                    const d = await res.json();
                    updatePlanPillUI(d.state, d.is_reading_plan, d.plan_title || "Plan");
                } catch (err) {}
            });
        }
        return pill;
    }

    function updatePlanPillUI(state, isReading, planTitle) {
        const pill = getOrCreateFloatingPlanPill();
        if (!pill) return;
        const iconSpan = pill.querySelector(".agy-plan-icon-span");
        const labelSpan = pill.querySelector(".agy-plan-label-span");

        while (iconSpan && iconSpan.firstChild) iconSpan.removeChild(iconSpan.firstChild);

        if (isReading && state === "playing") {
            pill.style.display = "inline-flex";
            pill.style.background = "rgba(14, 116, 144, 0.92)";
            pill.style.border = "1px solid #38bdf8";
            pill.style.color = "#ffffff";
            pill.title = "Pausar narración del plan (Ctrl + Alt + P)";
            if (iconSpan) iconSpan.appendChild(createSvgIcon(PAUSE_PATH, 15));
            if (labelSpan) labelSpan.textContent = "Pausar Plan";
        } else if (isReading && state === "paused") {
            pill.style.display = "inline-flex";
            pill.style.background = "rgba(20, 83, 45, 0.92)";
            pill.style.border = "1px solid #4ade80";
            pill.style.color = "#ffffff";
            pill.title = "Continuar narración del plan (Ctrl + Alt + P)";
            if (iconSpan) iconSpan.appendChild(createSvgIcon(PLAY_PATH, 15));
            if (labelSpan) labelSpan.textContent = "Continuar Plan";
        } else {
            pill.style.display = "inline-flex";
            pill.style.background = "rgba(30, 41, 59, 0.92)";
            pill.style.border = "1px solid rgba(148, 163, 184, 0.3)";
            pill.style.color = "#e2e8f0";
            pill.title = "Leer plan de implementación generado por la IA (Ctrl + Alt + P)";
            if (iconSpan) iconSpan.appendChild(createSvgIcon(CLIPBOARD_PATH, 15));
            if (labelSpan) labelSpan.textContent = "Leer Plan";
        }
    }

    function injectArtifactButtons() {
        const badges = document.querySelectorAll('button, a, div[role="button"], span');
        badges.forEach(function(b) {
            const txt = (b.textContent || '').trim();
            const isPlanBadge = (txt.indexOf("Implementation Plan") !== -1 || txt.indexOf("Plan de Implementación") !== -1 || (txt.indexOf("plan") !== -1 && b.getAttribute("href") && b.getAttribute("href").indexOf(".md") !== -1));
            if (isPlanBadge && !b.querySelector('.agy-inline-plan-btn') && !b.classList.contains('agy-inline-plan-btn')) {
                if (b.parentElement && !b.parentElement.querySelector('.agy-inline-plan-btn')) {
                    const btn = document.createElement("button");
                    btn.type = "button";
                    btn.className = "agy-inline-plan-btn";
                    btn.style.marginLeft = "6px";
                    btn.style.padding = "2px 6px";
                    btn.style.borderRadius = "12px";
                    btn.style.background = "rgba(56, 189, 248, 0.15)";
                    btn.style.border = "1px solid rgba(56, 189, 248, 0.4)";
                    btn.style.color = "#38bdf8";
                    btn.style.cursor = "pointer";
                    btn.style.display = "inline-flex";
                    btn.style.alignItems = "center";
                    btn.style.gap = "4px";
                    btn.style.fontSize = "11px";
                    btn.title = "Escuchar este plan con J.A.R.V.I.S. (Ctrl + Alt + P)";
                    btn.appendChild(createSvgIcon(SPEAKER_PATH, 13));
                    const s = document.createElement("span");
                    s.textContent = "Voz";
                    btn.appendChild(s);

                    btn.addEventListener("click", async function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        try {
                            await fetch("http://127.0.0.1:49152/plan/speak", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ action: "toggle" })
                            });
                        } catch (err) {}
                    });

                    b.parentElement.insertBefore(btn, b.nextSibling);
                }
            }
        });
    }

    function injectButtons() {
        injectArtifactButtons();
        const copyBtns = document.querySelectorAll('button[aria-label="Copy"], button[aria-label="Copied"]');
        copyBtns.forEach(function(copyBtn) {
            const parent = copyBtn.parentElement;
            if (!parent) return;
            const isResponseFooter = copyBtn.closest('.pt-3') || parent.querySelector('button[aria-label="Good response"]');
            if (!isResponseFooter) return;
            if (parent.querySelector('.agy-voice-replay-btn')) return;

            if (!copyBtn.dataset.agyTurnId) {
                copyBtn.dataset.agyTurnId = 'turn_' + Math.random().toString(36).slice(2, 9) + '_' + Date.now();
            }
            const turnId = copyBtn.dataset.agyTurnId;

            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = (copyBtn.className || '') + ' agy-voice-replay-btn';
            btn.setAttribute('aria-label', 'Leer en voz alta');
            btn.dataset.agyTurnId = turnId;

            const restartBtn = document.createElement('button');
            restartBtn.type = 'button';
            restartBtn.className = (copyBtn.className || '') + ' agy-voice-restart-btn';
            restartBtn.setAttribute('aria-label', 'Reiniciar lectura');
            restartBtn.title = 'Reiniciar lectura desde el principio';
            restartBtn.dataset.agyTurnId = turnId;
            setBtnIcon(restartBtn, RESTART_PATH, 16);
            restartBtn.style.display = "none";

            setBtnState(btn, restartBtn, "idle");

            btn.addEventListener('click', async function(e) {
                e.preventDefault();
                e.stopPropagation();

                if (btn.dataset.isBusy === "1") return;
                btn.dataset.isBusy = "1";
                setTimeout(function() { delete btn.dataset.isBusy; }, 600);

                window.__agyActiveTurnId = turnId;
                const text = extractTurnText(copyBtn);
                setBtnState(btn, restartBtn, "playing");

                document.querySelectorAll('.agy-voice-replay-btn').forEach(function(other) {
                    if (other !== btn) {
                        const otherRestart = other.parentElement && other.parentElement.querySelector('.agy-voice-restart-btn');
                        setBtnState(other, otherRestart, "idle");
                    }
                });

                try {
                    const res = await fetch('http://127.0.0.1:49152/speak', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ text: text, action: 'toggle', turn_id: turnId })
                    });
                    const data = await res.json();
                    if (data.state === "paused") {
                        setBtnState(btn, restartBtn, "paused");
                    } else if (data.state === "playing") {
                        setBtnState(btn, restartBtn, "playing");
                    } else {
                        setBtnState(btn, restartBtn, "idle");
                        if (window.__agyActiveTurnId === turnId) window.__agyActiveTurnId = null;
                    }
                } catch (err) {
                    setBtnState(btn, restartBtn, "idle");
                    if (window.__agyActiveTurnId === turnId) window.__agyActiveTurnId = null;
                }
            });

            restartBtn.addEventListener('click', async function(e) {
                e.preventDefault();
                e.stopPropagation();

                if (restartBtn.dataset.isBusy === "1") return;
                restartBtn.dataset.isBusy = "1";
                setTimeout(function() { delete restartBtn.dataset.isBusy; }, 600);

                window.__agyActiveTurnId = turnId;
                const text = extractTurnText(copyBtn);
                setBtnState(btn, restartBtn, "playing");

                try {
                    await fetch('http://127.0.0.1:49152/speak', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ text: text, restart: true, turn_id: turnId })
                    });
                    setBtnState(btn, restartBtn, "playing");
                } catch (err) {
                    setBtnState(btn, restartBtn, "idle");
                    if (window.__agyActiveTurnId === turnId) window.__agyActiveTurnId = null;
                }
            });

            parent.insertBefore(btn, copyBtn);
            parent.insertBefore(restartBtn, copyBtn);
        });
    }

    if (window.__agyVoiceInterval) clearInterval(window.__agyVoiceInterval);
    window.__agyVoiceInterval = setInterval(async function() {
        injectButtons();
        try {
            const res = await fetch('http://127.0.0.1:49152/status');
            const data = await res.json();
            const srvState = data.is_paused ? "paused" : (data.is_playing ? "playing" : "idle");
            const activeTurnId = data.turn_id || window.__agyActiveTurnId || "";
            const srvSig = data.sig || "";

            const allBtns = Array.from(document.querySelectorAll('.agy-voice-replay-btn'));
            let matchedBtn = null;

            if (srvState !== "idle") {
                if (activeTurnId) {
                    matchedBtn = allBtns.find(function(b) { return b.dataset.agyTurnId === activeTurnId; });
                }
                if (!matchedBtn && srvSig) {
                    for (let i = allBtns.length - 1; i >= 0; i--) {
                        const b = allBtns[i];
                        const cBtn = b.parentElement && b.parentElement.querySelector('button[aria-label="Copy"], button[aria-label="Copied"]');
                        if (cBtn) {
                            const sig = getTextSig(extractTurnText(cBtn));
                            if (sig && (sig.startsWith(srvSig.slice(0, 35)) || srvSig.startsWith(sig.slice(0, 35)))) {
                                matchedBtn = b;
                                if (b.dataset.agyTurnId) window.__agyActiveTurnId = b.dataset.agyTurnId;
                                break;
                            }
                        }
                    }
                }
            } else {
                window.__agyActiveTurnId = null;
            }

            allBtns.forEach(function(b) {
                const rBtn = b.parentElement && b.parentElement.querySelector('.agy-voice-restart-btn');
                if (srvState === "idle") {
                    setBtnState(b, rBtn, "idle");
                } else if (b === matchedBtn) {
                    setBtnState(b, rBtn, srvState);
                } else {
                    setBtnState(b, rBtn, "idle");
                }
            });

            const planRes = await fetch('http://127.0.0.1:49152/plan/status');
            const planData = await planRes.json();
            const pill = getOrCreateFloatingPlanPill();
            if (!planData.has_plan) {
                if (pill) pill.style.display = "none";
            } else {
                const pState = planData.is_paused ? "paused" : (planData.is_playing ? "playing" : "idle");
                updatePlanPillUI(pState, planData.is_reading_plan, planData.plan_title);
            }
        } catch (e) {}
    }, 600);

    if (window.__agyVoiceObserver) window.__agyVoiceObserver.disconnect();
    const obs = new MutationObserver(function() { injectButtons(); });
    window.__agyVoiceObserver = obs;
    if (document.body) {
        obs.observe(document.body, { childList: true, subtree: true });
        injectButtons();
    } else {
        window.addEventListener('DOMContentLoaded', function() {
            obs.observe(document.body, { childList: true, subtree: true });
            injectButtons();
        });
    }
    return "injected";
})();
"""


class AudioPlayer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_playing = False
        self.is_paused = False
        self.is_synthesizing = False
        self.stop_requested = False
        self.play_id = 0
        self.last_text = ""
        self.current_cleaned_text = ""
        self.current_sig = ""
        self.current_turn_id = ""
        self.is_reading_plan = False
        self.current_plan_path = ""
        self.brain_dirs = [
            os.path.expanduser(r"~\.gemini\antigravity-ide\brain"),
            os.path.expanduser(r"~\.gemini\antigravity\brain"),
            os.path.expanduser(r"~\.gemini\antigravity-cli\brain")
        ]
        self.lock = threading.Lock()
        pygame.mixer.init()
        if os.path.exists(LAST_SPEECH_FILE):
            try:
                with open(LAST_SPEECH_FILE, "r", encoding="utf-8") as f:
                    self.last_text = f.read().strip()
            except Exception:
                pass

    @staticmethod
    def get_text_sig(text: str) -> str:
        return re.sub(r"[^a-z0-9áéíóúñü]+", "", (text or "").lower())[:60]

    def _matches_current(self, cleaned_text: str) -> bool:
        if not cleaned_text or not self.current_sig:
            return not cleaned_text
        sig = self.get_text_sig(cleaned_text)
        if not sig:
            return False
        prefix_len = min(35, len(sig), len(self.current_sig))
        return prefix_len > 0 and sig[:prefix_len] == self.current_sig[:prefix_len]

    def pause_playback(self) -> bool:
        with self.lock:
            if self.is_playing and not self.is_paused:
                if pygame.mixer.get_init():
                    pygame.mixer.music.pause()
                self.is_paused = True
                self.is_playing = False
                log("\n[⏸️] Lectura en pausa.")
                return True
        return False

    def resume_playback(self) -> bool:
        with self.lock:
            if self.is_paused:
                if pygame.mixer.get_init():
                    pygame.mixer.music.unpause()
                self.is_paused = False
                self.is_playing = True
                log("\n[▶️] Continuando lectura desde donde se quedó...")
                return True
        return False

    def stop_playback(self, quiet: bool = False):
        with self.lock:
            self.stop_requested = True
            self.is_paused = False
            self.is_playing = False
            self.is_synthesizing = False
            self.is_reading_plan = False
            self.current_plan_path = ""
            self.current_turn_id = ""
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        if not quiet:
            log("\n[⏹️] Reproducción detenida por el usuario.")

    def toggle_or_speak(self, text: str, force_restart: bool = False, turn_id: str = "") -> str:
        self.config = load_config()
        cleaned = TextCleaner.clean_for_speech(
            text,
            announce_code=self.config.get("announce_code_blocks", True),
            max_chars=self.config.get("max_characters", 0)
        ) if text else ""

        is_same_turn = (turn_id and self.current_turn_id == turn_id) or self._matches_current(cleaned)

        if not force_restart and is_same_turn:
            if self.is_playing and not self.is_paused:
                self.pause_playback()
                return "paused"
            if self.is_paused:
                self.resume_playback()
                return "playing"

        if text and text.strip():
            self.play_text(text, force=True, turn_id=turn_id)
            return "playing"
        elif force_restart:
            self.replay_last()
            return "playing"
        else:
            log("[!] Solicitud recibida pero no se detectó texto válido para leer.")
            return "idle"

    def toggle_plan_speech(self, plan_path: Optional[str] = None, force_restart: bool = False, conv_id: Optional[str] = None) -> str:
        if self.is_reading_plan and not force_restart:
            if self.is_playing and not self.is_paused:
                self.pause_playback()
                return "paused"
            elif self.is_paused:
                self.resume_playback()
                return "playing"

        if not plan_path:
            plan_path = find_latest_plan(self.brain_dirs, conv_id)

        if not plan_path or not os.path.exists(plan_path):
            log("[!] No se encontró ningún archivo de plan de implementación.")
            return "no_plan"

        try:
            with open(plan_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_plan = f.read()
        except Exception as e:
            log(f"[!] Error leyendo plan ({plan_path}): {e}")
            return "error"

        self.config = load_config()
        cleaned_speech, title = PlanTextCleaner.clean_plan_for_speech(
            raw_plan,
            max_chars=self.config.get("max_characters", 0)
        )

        if not cleaned_speech or not cleaned_speech.strip():
            log("[!] El plan no contiene texto legible.")
            return "no_plan"

        log("\n" + "="*60)
        log(f"[📋 PLAN NARRATOR] Leyendo Plan: {title}")
        log(f"Archivo: {plan_path}")
        log("="*60)

        with self.lock:
            self.is_reading_plan = True
            self.current_plan_path = plan_path

        self.play_text(cleaned_speech, force=True, turn_id="plan")
        with self.lock:
            self.is_reading_plan = True
            self.current_plan_path = plan_path
        return "playing"

    def replay_last(self):
        if not self.last_text and os.path.exists(LAST_SPEECH_FILE):
            try:
                with open(LAST_SPEECH_FILE, "r", encoding="utf-8") as f:
                    self.last_text = f.read().strip()
            except Exception:
                pass
        if self.last_text:
            log("\n[🔁] Volviendo a reproducir la última respuesta...")
            self.play_text(self.last_text, force=True)
        else:
            log("\n[!] Aún no hay un texto previo guardado para repetir.")

    def play_text(self, text: str, force: bool = False, turn_id: str = ""):
        # Recargar configuración dinámicamente
        self.config = load_config()

        if text and text.strip():
            self.last_text = text.strip()
            try:
                with open(LAST_SPEECH_FILE, "w", encoding="utf-8") as f:
                    f.write(self.last_text)
            except Exception:
                pass

        if not force and not self.config.get("enabled", True):
            log("[🔇] Voz silenciada actualmente en la configuración.")
            return

        cleaned_text = TextCleaner.clean_for_speech(
            text, 
            announce_code=self.config.get("announce_code_blocks", True),
            max_chars=self.config.get("max_characters", 0)
        )

        if not cleaned_text or len(cleaned_text.strip()) == 0:
            return

        log("\n" + "="*60)
        log(f"[🔊] Reproduciendo respuesta con voz: {self.config.get('voice')}")
        log("="*60)
        preview = cleaned_text[:180] + ("..." if len(cleaned_text) > 180 else "")
        log(f"Texto a leer: \"{preview}\"")

        with self.lock:
            self.play_id += 1
            my_id = self.play_id
            self.stop_requested = False
            self.is_paused = False
            self.is_playing = True
            self.is_synthesizing = True
            self.current_cleaned_text = cleaned_text
            self.current_sig = self.get_text_sig(cleaned_text)
            self.current_turn_id = turn_id
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()

        thread = threading.Thread(target=self._synthesize_and_play, args=(cleaned_text, my_id), daemon=True)
        thread.start()

    def _synthesize_and_play(self, text: str, my_id: int):
        cache_file = os.path.join(CACHE_DIR, f"speech_{int(time.time()*1000)}_{my_id}.mp3")

        try:
            # 1. Synthesize audio with edge-tts with automatic retry (up to 3 attempts)
            async def run_tts_with_retry():
                max_attempts = 3
                last_err = None
                for attempt in range(1, max_attempts + 1):
                    with self.lock:
                        if self.stop_requested or self.play_id != my_id:
                            return False

                    try:
                        communicate = edge_tts.Communicate(
                            text=text,
                            voice=self.config.get("voice", "es-MX-DaliaNeural"),
                            rate=self.config.get("rate", "+10%"),
                            volume=self.config.get("volume", "+0%")
                        )
                        await communicate.save(cache_file)
                        if os.path.exists(cache_file) and os.path.getsize(cache_file) > 0:
                            return True
                    except Exception as e:
                        last_err = e
                        log(f"[⚠️ TTS] Intento {attempt}/{max_attempts} falló ({e}). Reintentando...")
                        await asyncio.sleep(0.3 * attempt)

                if last_err:
                    raise last_err
                return False

            success = asyncio.run(run_tts_with_retry())
            if not success:
                return

            with self.lock:
                self.is_synthesizing = False
                if self.stop_requested or self.play_id != my_id:
                    return

            # 2. Play audio with pygame
            pygame.mixer.music.load(cache_file)
            pygame.mixer.music.play()
            with self.lock:
                if self.is_paused and self.play_id == my_id:
                    pygame.mixer.music.pause()

            while (pygame.mixer.music.get_busy() or self.is_paused) and not self.stop_requested and self.play_id == my_id:
                if os.path.exists(STOP_FILE):
                    try:
                        os.remove(STOP_FILE)
                    except Exception:
                        pass
                    self.stop_playback()
                    break
                time.sleep(0.08)

            if self.play_id == my_id and pygame.mixer.music.get_busy() and self.stop_requested:
                pygame.mixer.music.stop()

        except Exception as e:
            log(f"[!] Error durante la síntesis/reproducción: {e}")
        finally:
            with self.lock:
                if self.play_id == my_id:
                    self.is_playing = False
                    self.is_paused = False
                    self.is_synthesizing = False
                    self.is_reading_plan = False
                    self.current_plan_path = ""
                    self.current_turn_id = ""
                    try:
                        if pygame.mixer.get_init():
                            pygame.mixer.music.unload()
                    except Exception:
                        pass
            # Clean up audio file
            try:
                if os.path.exists(cache_file):
                    os.remove(cache_file)
            except Exception:
                pass


def start_local_http_server(player: AudioPlayer):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class VoiceRequestHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def _send_cors(self, status=200, content_type="application/json"):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Private-Network", "true")
            self.end_headers()

        def do_OPTIONS(self):
            self._send_cors(204)

        def do_GET(self):
            if self.path.startswith("/plan/status"):
                path, title = get_plan_info(player.brain_dirs)
                self._send_cors(200)
                payload = json.dumps({
                    "has_plan": bool(path),
                    "plan_file": path or "",
                    "plan_title": title,
                    "is_reading_plan": player.is_reading_plan,
                    "is_playing": player.is_playing,
                    "is_paused": player.is_paused,
                    "is_synthesizing": player.is_synthesizing
                }).encode("utf-8")
                self.wfile.write(payload)
            elif self.path.startswith("/status"):
                self._send_cors(200)
                payload = json.dumps({
                    "is_playing": player.is_playing,
                    "is_paused": player.is_paused,
                    "is_synthesizing": player.is_synthesizing,
                    "turn_id": player.current_turn_id,
                    "sig": player.current_sig,
                    "enabled": player.config.get("enabled", True)
                }).encode("utf-8")
                self.wfile.write(payload)
            elif self.path.startswith("/replay"):
                player.replay_last()
                self._send_cors(200)
                self.wfile.write(b'{"ok":true,"state":"playing"}')
            elif self.path.startswith("/stop"):
                if player.is_playing and not player.is_paused:
                    player.pause_playback()
                    state = "paused"
                else:
                    player.stop_playback()
                    state = "idle"
                self._send_cors(200)
                self.wfile.write(json.dumps({"ok": True, "state": state}).encode("utf-8"))
            else:
                self._send_cors(404)
                self.wfile.write(b'{"error":"not_found"}')

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(length).decode("utf-8", errors="ignore") if length > 0 else "{}"
            try:
                data = json.loads(raw_body) if raw_body else {}
            except Exception:
                data = {}

            if self.path.startswith("/plan/speak"):
                plan_path = (data.get("plan_path") or "").strip() or None
                force_restart = bool(data.get("restart"))
                conv_id = (data.get("conv_id") or "").strip() or None
                state = player.toggle_plan_speech(plan_path=plan_path, force_restart=force_restart, conv_id=conv_id)
                _, title = get_plan_info(player.brain_dirs, conv_id)
                self._send_cors(200)
                self.wfile.write(json.dumps({
                    "ok": True,
                    "state": state,
                    "plan_file": player.current_plan_path,
                    "plan_title": title,
                    "is_reading_plan": player.is_reading_plan
                }).encode("utf-8"))
            elif self.path.startswith("/plan/stop"):
                if player.is_reading_plan:
                    if player.is_playing and not player.is_paused:
                        player.pause_playback()
                        state = "paused"
                    else:
                        player.stop_playback()
                        state = "idle"
                else:
                    state = "idle"
                self._send_cors(200)
                self.wfile.write(json.dumps({"ok": True, "state": state}).encode("utf-8"))
            elif self.path.startswith("/speak"):
                text = (data.get("text") or "").strip()
                force_restart = bool(data.get("restart"))
                turn_id = (data.get("turn_id") or "").strip()
                state = player.toggle_or_speak(text, force_restart=force_restart, turn_id=turn_id)
                self._send_cors(200)
                self.wfile.write(json.dumps({
                    "ok": True,
                    "state": state,
                    "turn_id": player.current_turn_id,
                    "sig": player.current_sig
                }).encode("utf-8"))
            elif self.path.startswith("/replay"):
                player.replay_last()
                self._send_cors(200)
                self.wfile.write(b'{"ok":true,"state":"playing"}')
            elif self.path.startswith("/stop"):
                if player.is_playing and not player.is_paused:
                    player.pause_playback()
                    state = "paused"
                else:
                    player.stop_playback()
                    state = "idle"
                self._send_cors(200)
                self.wfile.write(json.dumps({"ok": True, "state": state}).encode("utf-8"))
            else:
                self._send_cors(404)
                self.wfile.write(b'{"error":"not_found"}')

    def run_server():
        try:
            ThreadingHTTPServer.allow_reuse_address = True
            server = None
            for attempt in range(10):
                try:
                    server = ThreadingHTTPServer(("127.0.0.1", HTTP_PORT), VoiceRequestHandler)
                    break
                except OSError as e:
                    time.sleep(0.5)
            if server:
                log(f"[🌐] Servidor local de botones UI activo en http://127.0.0.1:{HTTP_PORT}")
                server.serve_forever()
            else:
                log(f"[!] No se pudo enlazar el servidor HTTP en el puerto {HTTP_PORT} tras varios intentos.")
        except Exception as e:
            log(f"[!] Error iniciando servidor HTTP local: {e}")

    t = threading.Thread(target=run_server, daemon=True)
    t.start()


def start_cdp_button_injector():
    import urllib.request
    import aiohttp

    port_files = [
        os.path.expandvars(r"%APPDATA%\Antigravity\DevToolsActivePort"),
        os.path.expandvars(r"%APPDATA%\Antigravity IDE\DevToolsActivePort"),
    ]

    async def inject_into_port(port: int):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=1.5) as resp:
                targets = json.loads(resp.read().decode("utf-8", errors="ignore"))
        except Exception:
            return

        for t in targets:
            if t.get("type") != "page":
                continue
            ws_url = t.get("webSocketDebuggerUrl")
            if not ws_url:
                continue
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(ws_url, timeout=2.0) as ws:
                        await ws.send_json({
                            "id": 1,
                            "method": "Runtime.evaluate",
                            "params": {
                                "expression": UI_INJECTOR_JS,
                                "returnByValue": True
                            }
                        })
                        res = await ws.receive_json(timeout=2.0)
                        val = res.get("result", {}).get("result", {}).get("value")
                        if val == "injected":
                            log(f"[✨ UI] Botón de repetición de voz inyectado en ventana ({t.get('title', 'Antigravity')[:35]})")
            except Exception:
                pass

    def loop_injector():
        while True:
            for pf in port_files:
                if os.path.exists(pf):
                    try:
                        with open(pf, "r", encoding="utf-8") as f:
                            first_line = f.readline().strip()
                        if first_line.isdigit():
                            asyncio.run(inject_into_port(int(first_line)))
                    except Exception:
                        pass
            time.sleep(2.5)

    t = threading.Thread(target=loop_injector, daemon=True)
    t.start()


class AntigravityConversationWatcher:
    def __init__(self, player: AudioPlayer):
        self.player = player
        self.brain_dirs = [
            os.path.expanduser(r"~\.gemini\antigravity-ide\brain"),
            os.path.expanduser(r"~\.gemini\antigravity\brain"),
            os.path.expanduser(r"~\.gemini\antigravity-cli\brain")
        ]
        self.file_states: Dict[str, Dict[str, Any]] = {}

    def get_surface_name(self, path: str) -> str:
        if "antigravity-ide" in path:
            return "Antigravity IDE"
        elif "antigravity-cli" in path:
            return "Antigravity CLI"
        elif "antigravity" in path:
            return "Antigravity 2.0"
        return "Antigravity"

    def find_recent_transcripts(self, limit: int = 15) -> list:
        all_files = []
        for bdir in self.brain_dirs:
            if os.path.exists(bdir):
                pattern = os.path.join(bdir, "*", ".system_generated", "logs", "transcript.jsonl")
                all_files.extend(glob.glob(pattern))
        if not all_files:
            return []
        all_files.sort(key=os.path.getmtime, reverse=True)
        return all_files[:limit]

    def initialize_file_state(self, transcript_path: str, at_eof: bool = True):
        surface = self.get_surface_name(transcript_path)
        conv_id = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(transcript_path))))
        log(f"[📡] Sintonizado con {surface} (Chat: {conv_id[:8]}...)")

        seen_indices = set()
        pos = 0
        if at_eof:
            try:
                with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        try:
                            step = json.loads(line)
                            idx = step.get("step_index")
                            if idx is not None:
                                seen_indices.add(idx)
                        except Exception:
                            pass
                    pos = f.tell()
            except Exception as e:
                log(f"[!] Error inicializando {transcript_path}: {e}")
                pos = 0

        self.file_states[transcript_path] = {
            "pos": pos,
            "seen_indices": seen_indices,
            "surface": surface,
            "conv_id": conv_id
        }

    def _read_full_content_if_truncated(self, transcript_path: str, step: Dict[str, Any]) -> str:
        content = step.get("content") or ""
        truncated_fields = step.get("truncated_fields") or []
        if "content" not in truncated_fields:
            return content
        full_path = os.path.join(os.path.dirname(transcript_path), "transcript_full.jsonl")
        if not os.path.exists(full_path):
            return content
        target_idx = step.get("step_index")
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        full_step = json.loads(line)
                        if full_step.get("step_index") == target_idx:
                            return full_step.get("content") or content
                    except Exception:
                        continue
        except Exception:
            pass
        return content

    def check_for_new_responses(self):
        if os.path.exists(REPLAY_FILE):
            try:
                os.remove(REPLAY_FILE)
            except Exception:
                pass
            self.player.replay_last()

        recent = self.find_recent_transcripts(limit=10)
        if not recent:
            return

        for transcript_path in recent:
            if transcript_path not in self.file_states:
                # Chat nuevo creado después del arranque: inicializar desde el inicio para no perder su primer mensaje
                self.initialize_file_state(transcript_path, at_eof=False)

            state = self.file_states[transcript_path]
            try:
                if not os.path.exists(transcript_path):
                    continue

                current_size = os.path.getsize(transcript_path)
                if current_size < state["pos"]:
                    state["pos"] = 0

                if current_size == state["pos"]:
                    continue

                with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
                    f.seek(state["pos"])
                    new_lines = f.readlines()
                    state["pos"] = f.tell()

                for line in new_lines:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        step = json.loads(line)
                        step_idx = step.get("step_index")
                        source = step.get("source")
                        step_type = step.get("type")
                        content = step.get("content")
                        tool_calls = step.get("tool_calls")

                        if step_idx in state["seen_indices"]:
                            continue

                        state["seen_indices"].add(step_idx)

                        # Only speak final PLANNER_RESPONSE directed to the user without tool calls
                        if source == "MODEL" and step_type == "PLANNER_RESPONSE" and content and not tool_calls:
                            full_content = self._read_full_content_if_truncated(transcript_path, step)
                            log(f"\n[✨ {state['surface']}] Respuesta detectada en chat {state['conv_id'][:8]}...")
                            self.player.play_text(full_content)

                    except json.JSONDecodeError:
                        continue

            except Exception as e:
                log(f"[!] Error monitoreando {transcript_path}: {e}")

    def run_loop(self):
        log("\n" + "="*60)
        log("  🎙️ ANTIGRAVITY VOICE ASSISTANT (TTS Neuronal Multi-Plataforma)")
        log("="*60)
        log(f"• Soporte activo: Antigravity IDE + Antigravity 2.0 + CLI")
        log(f"• Voz activa:     {self.player.config.get('voice')}")
        log(f"• Velocidad:      {self.player.config.get('rate')}")
        log(f"• Atajo Silencio: [Ctrl + Alt + S] para detener voz actual")
        log(f"• Atajo Repetir:  [Ctrl + Alt + R] para repetir última lectura")
        log(f"• Atajo Plan:     [Ctrl + Alt + P] para leer / pausar el Plan de Implementación")
        log(f"• Atajo Mute:     [Ctrl + Alt + M] para silenciar/activar asistente")
        log(f"• Salir:          [Ctrl + C] en esta consola")
        log("="*60)

        # Pre-inicializar todos los transcripts existentes al final del archivo (EOF)
        initial_transcripts = self.find_recent_transcripts(limit=500)
        for t in initial_transcripts:
            self.initialize_file_state(t, at_eof=True)

        log("\n[🟢] Asistente escuchando activamente en segundo plano...")

        while True:
            self.check_for_new_responses()
            time.sleep(0.4)


def setup_global_hotkeys(player: AudioPlayer, config: Dict[str, Any]):
    if not PYNPUT_AVAILABLE or not config.get("hotkeys_enabled", True):
        return

    # Track pressed keys
    current_keys = set()

    def on_press(key):
        current_keys.add(key)
        is_ctrl = any(k in current_keys for k in [keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r])
        is_alt = any(k in current_keys for k in [keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr])

        try:
            if is_ctrl and is_alt:
                if hasattr(key, 'char') and key.char:
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
                        log(f"\n[🔔] Voz {state} por atajo de teclado.")
                        save_config(config)
        except Exception:
            pass

    def on_release(key):
        current_keys.discard(key)

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.daemon = True
    listener.start()


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
        log(f"[💥 CRASH] Error fatal en bucle principal: {e}\n{traceback.format_exc()}")
        time.sleep(2)

if __name__ == "__main__":
    main()
