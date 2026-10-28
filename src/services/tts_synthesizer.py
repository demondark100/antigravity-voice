import os
import asyncio
from typing import Optional, Callable
import edge_tts
import edge_tts.constants
import edge_tts.communicate
from utils.config import log

_NEW_WSS_URL = (
    "wss://api.msedgeservices.com/tts/cognitiveservices/websocket/v1"
    f"?Ocp-Apim-Subscription-Key={edge_tts.constants.TRUSTED_CLIENT_TOKEN}"
)
edge_tts.constants.WSS_URL = _NEW_WSS_URL
edge_tts.communicate.WSS_URL = _NEW_WSS_URL

class TTSSynthesizer:
    @staticmethod
    def synthesize_to_file(
        text: str,
        voice: str,
        rate: str,
        volume: str,
        cache_file: str,
        is_cancelled: Optional[Callable[[], bool]] = None,
        max_attempts: int = 3
    ) -> bool:
        async def _run():
            last_err = None
            for attempt in range(1, max_attempts + 1):
                if is_cancelled and is_cancelled():
                    return False
                try:
                    communicate = edge_tts.Communicate(
                        text=text,
                        voice=voice,
                        rate=rate,
                        volume=volume
                    )
                    await communicate.save(cache_file)
                    if os.path.exists(cache_file) and os.path.getsize(cache_file) > 0:
                        return True
                except Exception as e:
                    last_err = e
                    log(f"[⚠️ TTS] Intento {attempt}/{max_attempts} falló ({e}). Reintentando...")
                    await asyncio.sleep(0.3 * attempt)

            if last_err:
                log(f"[!] Falló la síntesis TTS tras {max_attempts} intentos: {last_err}")
            return False

        try:
            return asyncio.run(_run())
        except Exception as e:
            log(f"[!] Error ejecutando evento async de TTS: {e}")
            return False
