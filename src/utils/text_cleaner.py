import re

class TextCleaner:
    @staticmethod
    def clean_for_speech(text: str, announce_code: bool = True, max_chars: int = 0) -> str:
        if not text:
            return ""

        # 1. Tratar bloques de código
        if announce_code:
            text = re.sub(r"```[\w\-]*\n[\s\S]*?```", " [He incluido un bloque de código en pantalla]. ", text)
        else:
            text = re.sub(r"```[\w\-]*\n[\s\S]*?```", " ", text)

        # 2. Código inline y enlaces Markdown
        text = re.sub(r"`([^`]+)`", r"\1", text)
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        text = re.sub(r"!\[[^\]]*\]\([^\)]+\)", "", text)

        # 3. Negrita, cursiva y encabezados
        text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
        text = re.sub(r"(\*|_)(.*?)\1", r"\2", text)
        text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)

        # 4. Citas, viñetas y listas
        text = re.sub(r"^\s*>\s*(\[![\w]+\])?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

        # 5. Tablas Markdown y emojis
        text = re.sub(r"\|[-:\s|]+\|", "", text)
        text = re.sub(r"\|", " ", text)
        text = re.sub(r"[\U00010000-\U0010ffff]", "", text)

        # 6. Puntuación y saltos de línea
        text = re.sub(r"\n{2,}", ". \n", text)
        text = re.sub(r"\n", " ", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = text.strip()

        if max_chars and max_chars > 0 and len(text) > max_chars:
            text = text[:max_chars] + " ... [El resto continúa en pantalla]."

        return text
