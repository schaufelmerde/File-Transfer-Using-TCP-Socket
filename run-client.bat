@echo off
cd /d "%~dp0"
title TCP File Transfer - Client

if not exist ".venv\Scripts\python.exe" (
    echo [X] The dependencies are not installed yet.
    echo     Run setup.bat first, then try again.
    echo.
    pause
    exit /b 1
)

echo [*] Starting the client...
echo     Put the OTHER device's IP address in the "Server IP" box.
echo     That device needs run-server.bat running.
echo.

.venv\Scripts\python.exe client.py
if errorlevel 1 (
    echo.
    echo [X] The client exited with an error.
    pause
)
