@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title TCP File Transfer - Setup

echo ================================================
echo   TCP File Transfer - Setup
echo ================================================
echo.
echo This installs what the CLIENT needs to send files ^(PyQt5, tqdm^).
echo To only RECEIVE files, you can skip this and run run-server.bat.
echo.

if exist ".venv\Scripts\python.exe" (
    echo [*] .venv already exists - reusing it.
    goto :install
)

REM PyQt5 has no wheels for Python 3.14 yet, so pick a version it supports.
set "PY="
for %%v in (3.13 3.12 3.11 3.10 3.9 3.8) do (
    if not defined PY (
        py -%%v -c "pass" >nul 2>&1
        if not errorlevel 1 set "PY=py -%%v"
    )
)

if not defined PY (
    echo [X] No suitable Python found. PyQt5 needs Python 3.8 - 3.13.
    echo     Install one from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [*] Creating virtual environment with !PY! ...
!PY! -m venv .venv
if errorlevel 1 (
    echo [X] Could not create the virtual environment.
    echo.
    pause
    exit /b 1
)

:install
echo [*] Installing dependencies ^(this can take a minute^)...
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.venv\Scripts\python.exe -m pip install pyqt5 tqdm
if errorlevel 1 (
    echo.
    echo [X] Installing the dependencies failed. See the messages above.
    echo.
    pause
    exit /b 1
)

echo.
echo [*] Setup complete.
echo.
echo     run-server.bat  - receive files on this machine
echo     run-client.bat  - send a file to the other machine
echo.
pause
