import os
import time
import json
import asyncio
import threading
import urllib.request
import aiohttp
from utils.config import log
from templates.injector_loader import get_ui_injector_js

PORT_FILES = [
    os.path.expandvars(r"%APPDATA%\Antigravity\DevToolsActivePort"),
    os.path.expandvars(r"%APPDATA%\Antigravity IDE\DevToolsActivePort"),
]

async def inject_into_port(port: int, script_code: str):
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
                        "params": {"expression": script_code, "returnByValue": True}
                    })
                    res = await ws.receive_json(timeout=2.0)
                    if res.get("result", {}).get("result", {}).get("value") == "injected":
                        log(f"[✨ UI] Inyectado en ({t.get('title', 'Antigravity')[:30]}...)")
        except Exception:
            pass

def start_cdp_button_injector():
    def _loop():
        while True:
            script_code = get_ui_injector_js()
            if script_code:
                ports_to_try = {61603, 61604}
                for pf in PORT_FILES:
                    if os.path.exists(pf):
                        try:
                            with open(pf, "r", encoding="utf-8") as f:
                                port_line = f.readline().strip()
                            if port_line.isdigit():
                                ports_to_try.add(int(port_line))
                        except Exception:
                            pass
                for port in ports_to_try:
                    try:
                        asyncio.run(inject_into_port(port, script_code))
                    except Exception:
                        pass
            time.sleep(2.5)

    threading.Thread(target=_loop, daemon=True).start()
