# 🎙️ Antigravity Voice Assistant & J.A.R.V.I.S. Plan Narrator

[![Platform: Windows 10/11](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?style=flat&logo=windows)](https://microsoft.com)
[![Engine: Edge-TTS Neural](https://img.shields.io/badge/Engine-Microsoft%20Edge%20Neural%20TTS-0078D7?style=flat)](https://github.com/rany2/edge-tts)
[![Antigravity: IDE & 2.0 Ready](https://img.shields.io/badge/Antigravity-IDE%20%26%202.0%20Compatible-4285F4?style=flat)](https://antigravity.google)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Asistente de voz neuronal humano y narrador ejecutivo de planes de implementación para Antigravity IDE y Antigravity 2.0.**
> Diseñado para ejecutarse de forma silenciosa, autónoma y con **1 solo clic en Windows recién formateado**, sin requerir instalación manual de Python ni librerías adicionales.

---

## 🌟 Características Principales

* 📋 **J.A.R.V.I.S. Plan Narrator**: Lee con voz ejecutiva natural los planes de implementación generados por la IA tras el comando `/plan`. Convierte diagramas Mermaid, alertas `> [!IMPORTANT]`, listas de tareas pendientes y rutas técnicas en una narrativa clara y ejecutiva.
* 🎙️ **Voces Neuronales Gratuitas en Español**: Calidad de estudio impulsada por Microsoft Edge TTS (Dalia, Jorge, Álvaro, Elvira, Gonzalo, Alex, Tomás).
* ⚡ **Botón Flotante Dinámico en Pantalla**: Píldora interactiva inteligente `[ 📋 Leer Plan ]` / `[ ⏸️ Pausar Plan ]` / `[ ▶️ Continuar Plan ]` inyectada directamente en Antigravity IDE y 2.0.
* ⌨️ **Atajos de Teclado Globales**: Controla la voz desde cualquier aplicación sin perder el foco.
* 🖥️ **Widget de Escritorio Flotante**: Mini barra minimalista siempre visible para pausar, silenciar o cambiar voces sobre la marcha.
* 🔄 **Arranque Automático Silencioso**: Se integra en el Programador de Tareas de Windows para activarse automáticamente al iniciar sesión, sin ventanas negras de consola CMD.

---

## ⌨️ Atajos de Teclado Globales

| Atajo | Función | Descripción |
| :--- | :--- | :--- |
| **`Ctrl + Alt + P`** | **Leer / Pausar Plan** | Lee el plan de implementación activo o lo pausa en el segundo exacto. |
| **`Ctrl + Alt + S`** | **Detener Audio** | Detiene de inmediato cualquier locución en curso. |
| **`Ctrl + Alt + R`** | **Repetir Última Respuesta** | Vuelve a leer la última respuesta recibida del asistente. |
| **`Ctrl + Alt + M`** | **Silenciar / Activar** | Conmuta el modo de silencio del asistente. |

---

## 🚀 Instalación en 1 Clic (Ideal tras formatear la PC)

1. Descarga o clona este repositorio.
2. Abre la carpeta `installer/` y haz doble clic en:
   **`install.bat`**
3. El instalador automáticamente:
   - Desplegará los archivos en `%LOCALAPPDATA%\AntigravityVoice`.
   - Configurará el servicio en el Programador de Tareas de Windows (`AntigravityVoiceService`).
   - Creará accesos directos en tu **Escritorio** y **Menú Inicio**.
   - Iniciará el servicio y el widget flotante inmediatamente.

### 🗑️ Desinstalación Limpia
Para desinstalar por completo el asistente sin dejar ningún residuo, haz doble clic en:
`installer/uninstall.bat`

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

## 🔨 Cómo Compilar los Ejecutables Standalone (.exe)

Si deseas recompilar los binarios nativos por tu cuenta:
1. Asegúrate de tener Python 3.10+ instalado.
2. Haz doble clic en **`build.bat`** (o ejecuta `python build_dist.py`).
3. Los ejecutables se generarán automáticamente en la carpeta `bin/`:
   - `bin/AntigravityVoiceService.exe`
   - `bin/AntigravityVoiceWidget.exe`

---

## 🏛️ Arquitectura Modular (SOLID)

* `src/voice_reader.py`: Orquestador principal, servidor HTTP local (`127.0.0.1:49152`), inyector CDP de interfaz y observador de conversaciones.
* `src/plan_manager.py`: Limpieza semántica (`PlanTextCleaner`) y descubrimiento de planes Markdown.
* `src/floating_control.py`: Interfaz de usuario de escritorio en Tkinter.
* `installer/`: Scripts automatizados de ciclo de vida en Windows (Task Scheduler y VBScript shortcuts).

---

## 📄 Licencia

Este proyecto está bajo la licencia [MIT](LICENSE).
