@echo off
setlocal enabledelayedexpansion
title 🤵 LISBON Personal AI Butler
cd /d "%~dp0"
set PYTHONPATH=%~dp0src;%PYTHONPATH%

cls
echo ================================================================
echo             BOOTING LISBON PERSONAL AI BUTLER
echo ================================================================
echo.

python src\lisbon\main.py %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo LISBON session ended with code %ERRORLEVEL%.
    pause
)
