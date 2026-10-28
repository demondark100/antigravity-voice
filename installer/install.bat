@echo off
setlocal enabledelayedexpansion
title Instalador de Antigravity Voice Assistant
chcp 65001 >nul

echo ============================================================
echo   🎙️  ANTIGRAVITY VOICE ASSISTANT - INSTALADOR WINDOWS
echo ============================================================
echo.

set "INSTALL_DIR=%LOCALAPPDATA%\AntigravityVoice"
set "GEMINI_DIR=%USERPROFILE%\.gemini\config\sidecars\voice-reader"

echo [*] Carpeta de instalación: "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\bin" mkdir "%INSTALL_DIR%\bin"
if not exist "%INSTALL_DIR%\.audio_cache" mkdir "%INSTALL_DIR%\.audio_cache"

if not exist "%GEMINI_DIR%" mkdir "%GEMINI_DIR%"

echo [*] Copiando archivos del sistema...
set "SRC_DIR=%~dp0..\src"
set "BIN_DIR=%~dp0..\bin"

if exist "%BIN_DIR%\AntigravityVoiceService.exe" (
    echo [OK] Copiando ejecutables nativos standalone...
    copy /y "%BIN_DIR%\*.exe" "%INSTALL_DIR%\bin\" >nul
)

if exist "%SRC_DIR%\voice_reader.py" (
    echo [OK] Copiando módulos de código fuente...
    copy /y "%SRC_DIR%\*.py" "%INSTALL_DIR%\" >nul
    copy /y "%SRC_DIR%\config.json" "%INSTALL_DIR%\" >nul
    copy /y "%SRC_DIR%\*.py" "%GEMINI_DIR%\" >nul
    copy /y "%SRC_DIR%\config.json" "%GEMINI_DIR%\" >nul
)

rem Copiar scripts auxiliares de control
copy /y "%~dp0uninstall.bat" "%INSTALL_DIR%\" >nul 2>&1

rem Crear script de detención en INSTALL_DIR
(
echo @echo off
echo echo deteniendo... ^> "%%~dp0.stop_trigger"
echo taskkill /f /im AntigravityVoiceService.exe ^>nul 2^>^&1
echo taskkill /f /im AntigravityVoiceWidget.exe ^>nul 2^>^&1
echo taskkill /f /fi "WINDOWTITLE eq Antigravity Voice*" ^>nul 2^>^&1
echo echo Asistente de voz detenido.
echo timeout /t 2 ^>nul
) > "%INSTALL_DIR%\detener_voz.bat"

rem Registrar tarea en el Programador de Tareas de Windows (Inicio automático en logon)
echo [*] Configurando arranque automático con Windows...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_task.ps1" -InstallDir "%INSTALL_DIR%"

rem Crear accesos directos en Escritorio y Menú Inicio
echo [*] Creando accesos directos en Escritorio y Menú Inicio...
cscript //nologo "%~dp0create_shortcuts.vbs"

rem Iniciar widget flotante
echo [*] Lanzando widget flotante...
if exist "%INSTALL_DIR%\bin\AntigravityVoiceWidget.exe" (
    start "" "%INSTALL_DIR%\bin\AntigravityVoiceWidget.exe"
) else (
    start "" pythonw "%INSTALL_DIR%\floating_control.py"
)

echo.
echo ============================================================
echo   ✨ INSTALACIÓN COMPLETADA CON ÉXITO
echo ============================================================
echo   • Servicio en segundo plano: ACTIVO
echo   • Atajo para leer Planes:   [ Ctrl + Alt + P ]
echo   • Atajo para detener voz:   [ Ctrl + Alt + S ]
echo   • Atajo para repetir audio: [ Ctrl + Alt + R ]
echo   • Atajo silenciar/activar:  [ Ctrl + Alt + M ]
echo ============================================================
echo.
pause
