@echo off
setlocal
title Desinstalador de Antigravity Voice Assistant
chcp 65001 >nul

echo ============================================================
echo   🗑️  DESINSTALADOR DE ANTIGRAVITY VOICE ASSISTANT
echo ============================================================
echo.

set /p CONFIRM="¿Estás seguro de que deseas desinstalar Antigravity Voice Assistant? (S/N): "
if /i not "%CONFIRM%"=="S" (
    echo Operación cancelada por el usuario.
    pause
    exit /b
)

echo [*] Deteniendo servicios y procesos activos...
taskkill /f /im AntigravityVoiceService.exe >nul 2>&1
taskkill /f /im AntigravityVoiceWidget.exe >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq Antigravity Voice*" >nul 2>&1

echo [*] Eliminando tarea programada de Windows...
schtasks /delete /tn "AntigravityVoiceService" /f >nul 2>&1

echo [*] Eliminando accesos directos...
del /f /q "%USERPROFILE%\Desktop\Antigravity Voice Widget.lnk" >nul 2>&1
rmdir /s /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Antigravity Voice" >nul 2>&1

echo [*] Eliminando archivos instalados en LocalAppData...
set "INSTALL_DIR=%LOCALAPPDATA%\AntigravityVoice"
if exist "%INSTALL_DIR%" (
    rmdir /s /q "%INSTALL_DIR%" >nul 2>&1
)

echo.
echo ============================================================
echo   ✅ DESINSTALACIÓN COMPLETADA
echo ============================================================
echo El sistema ha sido desinstalado limpiamente.
echo.
pause
