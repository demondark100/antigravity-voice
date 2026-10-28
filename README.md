# 🎙️ Antigravity Voice Assistant & J.A.R.V.I.S. Plan Narrator

[![Platform: Windows 10/11](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?style=flat&logo=windows)](https://microsoft.com)
[![Engine: Edge-TTS Neural](https://img.shields.io/badge/Engine-Microsoft%20Edge%20Neural%20TTS-0078D7?style=flat)](https://github.com/rany2/edge-tts)
[![Antigravity: IDE & 2.0 Ready](https://img.shields.io/badge/Antigravity-IDE%20%26%202.0%20Compatible-4285F4?style=flat)](https://antigravity.google)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Asistente de voz neuronal humano y narrador ejecutivo de planes de implementación para Antigravity IDE y Antigravity 2.0.**
> Diseñado para ejecutarse de forma silenciosa, autónoma y con **1 solo clic en cualquier PC con Windows 10 u 11**, sin necesidad de instalar Python ni librerías adicionales.

---

## 🌟 Características Principales

* 📋 **J.A.R.V.I.S. Plan Narrator**: Lee con voz ejecutiva natural los planes de implementación generados por la IA tras el comando `/plan`. Convierte diagramas Mermaid, alertas `> [!IMPORTANT]`, listas de tareas y rutas técnicas en una narrativa clara y ejecutiva.
* 🎙️ **Voces Neuronales Gratuitas en Español**: Calidad de estudio impulsada por Microsoft Edge TTS (Dalia, Jorge, Álvaro, Elvira, Gonzalo, Alex, Tomás).
* ⚡ **Botón Flotante Inteligente**: Píldora interactiva `[ 📋 Leer Plan ]` / `[ ⏸️ Pausar Plan ]` / `[ ▶️ Continuar Plan ]` inyectada directamente en Antigravity IDE y 2.0.
* ⌨️ **Atajos de Teclado Globales**: Controla la voz desde cualquier aplicación sin perder el foco.
* 🖥️ **Widget de Escritorio Flotante**: Barra minimalista siempre visible para pausar, silenciar o cambiar voces sobre la marcha.
* 🔄 **Arranque Automático Silencioso**: Se integra en el Programador de Tareas de Windows para activarse automáticamente al iniciar sesión, sin ventanas de consola CMD.

---

## ⌨️ Atajos de Teclado Globales

| Atajo | Función | Descripción |
| :--- | :--- | :--- |
| **`Ctrl + Alt + P`** | **Leer / Pausar Plan** | Lee el plan de implementación activo o lo pausa en el segundo exacto. |
| **`Ctrl + Alt + S`** | **Detener Audio** | Detiene de inmediato cualquier locución en curso. |
| **`Ctrl + Alt + R`** | **Repetir Última Respuesta** | Vuelve a leer la última respuesta recibida del asistente. |
| **`Ctrl + Alt + M`** | **Silenciar / Activar** | Conmuta el modo de silencio del asistente. |

---

## 🚀 Instalación en 1 Clic (Sin configuración previa)

1. Descarga o clona este repositorio:
   ```bash
   git clone https://github.com/demondark100/antigravity-voice.git
   ```
2. Ejecuta cualquiera de las dos opciones:
   * **Opción A (Recomendada - Con ventana gráfica)**: Haz doble clic en **`AntigravityVoice_Setup.exe`**.
   * **Opción B (Directa)**: Haz doble clic en **`Instalar_Antigravity_Voice.bat`**.
3. El instalador se encargará de todo automáticamente:
   - Despliega los archivos en `%LOCALAPPDATA%\AntigravityVoice`.
   - Configura el arranque automático con Windows en segundo plano.
   - Crea los accesos directos en tu **Escritorio** y **Menú Inicio**.
   - Inicia el servicio de voz y el widget flotante inmediatamente.

> [!TIP]
> No necesitas instalar Python ni librerías adicionales. Los binarios incluidos en `bin/` son autónomos y listos para usar.

### 🗑️ Desinstalación Limpia
Para desinstalar por completo el asistente sin dejar ningún residuo, haz doble clic en:
**`Desinstalar_Antigravity_Voice.bat`** (o en `installer/uninstall.bat`).

---

## ⚙️ Configuración (`config.json`)

El archivo de configuración reside en `%LOCALAPPDATA%\AntigravityVoice\config.json`:

```json
{
    "voice": "es-MX-DaliaNeural",
    "rate": "+10%",
    "volume": "+0%",
    "announce_code_blocks": true,
    "max_characters": 0,
    "enabled": true,
    "hotkeys_enabled": true
}
```

### Voces Neuronales Recomendadas:
* `es-MX-DaliaNeural` (México - Femenina, cálida y natural - *Predeterminada*)
* `es-MX-JorgeNeural` (México - Masculina, fluida y profesional)
* `es-ES-AlvaroNeural` (España - Masculina, expresiva y enérgica)
* `es-ES-ElviraNeural` (España - Femenina, formal y suave)
* `es-CO-GonzaloNeural` (Colombia - Masculina, pausada y amigable)
* `es-PE-AlexNeural` (Perú - Masculina, neutra y técnica)
* `es-AR-TomasNeural` (Argentina - Masculina, acento rioplatense)

---

## 🔨 Cómo Recompilar los Ejecutables Standalone (Opcional)

Si eres desarrollador y deseas modificar el código o recompilar los binarios nativos:
1. Asegúrate de tener Python 3.10+ instalado.
2. Instala dependencias: `pip install -r requirements.txt`.
3. Haz doble clic en **`build.bat`** (o ejecuta `python build_dist.py`).
4. Los ejecutables se generarán automáticamente en `bin/`:
   - `bin/AntigravityVoiceService.exe`
   - `bin/AntigravityVoiceWidget.exe`

---

## 📄 Licencia

Este proyecto está bajo la licencia [MIT](LICENSE).
