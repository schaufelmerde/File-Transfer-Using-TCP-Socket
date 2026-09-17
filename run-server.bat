@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title TCP File Transfer - Server

echo ================================================
echo   TCP File Transfer - Server ^(receiving^)
echo ================================================
echo.

REM server.py uses only the standard library, so any Python 3 will do.
REM Prefer the project venv if it exists, otherwise fall back to the system one.
set "PY="
if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
) else (
    where py >nul 2>&1
    if not errorlevel 1 (
        set "PY=py"
    ) else (
        where python >nul 2>&1
        if not errorlevel 1 set "PY=python"
    )
)

if not defined PY (
    echo [X] Python was not found on this machine.
    echo     Install Python 3 from https://www.python.org/downloads/
    echo     and tick "Add python.exe to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [*] Using Python: !PY!
echo.
echo [*] This machine's IP address^(es^).
echo     Type one of these into the OTHER device's "Server IP" box:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set "IP=%%a"
    set "IP=!IP: =!"
    echo         !IP!
)
echo.

netsh advfirewall firewall show rule name="TCP File Transfer" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] No firewall rule for port 5555 was found on this machine.
    echo     If the other device cannot connect, run this once in an
    echo     Administrator PowerShell:
    echo.
    echo     New-NetFirewallRule -DisplayName "TCP File Transfer" -Direction Inbound -LocalPort 5555 -Protocol TCP -Action Allow
    echo.
)

echo [*] Incoming files are saved to: %~dp0REC
echo [*] Press Ctrl+C to stop the server.
echo.

!PY! -u server.py

echo.
echo [*] Server stopped.
pause
