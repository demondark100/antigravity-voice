import os
import sys

def get_ui_injector_js() -> str:
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui_injector.js"),
        os.path.join(getattr(sys, '_MEIPASS', ''), "templates", "ui_injector.js"),
        os.path.join(getattr(sys, '_MEIPASS', ''), "ui_injector.js"),
        os.path.join(os.path.dirname(sys.executable), "templates", "ui_injector.js"),
    ]

    for p in candidates:
        if p and os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            except Exception:
                continue

    return ""
