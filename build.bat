@echo off
title Compilador de Antigravity Voice Assistant
cd /d "%~dp0"
chcp 65001 >nul

echo ============================================================
echo   🔨 COMPILADOR STANDALONE DE ANTIGRAVITY VOICE
echo ============================================================
echo.
python build_dist.py
if %errorlevel% neq 0 (
    echo.
    echo [-] Error durante la compilación.
    pause
    exit /b %errorlevel%
)

echo.
echo Presione cualquier tecla para salir...
pause >nul
