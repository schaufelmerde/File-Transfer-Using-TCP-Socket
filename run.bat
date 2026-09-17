@echo off
setlocal
cd /d "%~dp0"
title TCP File Transfer

echo ================================================
echo   TCP File Transfer
echo ================================================
echo.

REM install dependencies the first time this is run on a machine
if not exist ".venv\Scripts\python.exe" (
    echo [*] First run on this machine - installing dependencies.
    echo.
    call "%~dp0setup.bat" /quiet
    if not exist ".venv\Scripts\python.exe" (
        echo [X] Setup did not finish. Run setup.bat on its own to see why.
        echo.
        pause
        exit /b 1
    )
    echo.
)

REM only start a server if this machine is not already listening
netstat -ano | findstr /c:":5555" | findstr /c:"LISTENING" >nul
if errorlevel 1 (
    echo [*] Starting the server in its own window.
    echo     Leave that window open - it is what receives files.
    start "TCP File Transfer - Server" "%~dp0run-server.bat"
) else (
    echo [*] A server is already running on port 5555 - reusing it.
)

echo.
echo [*] Opening the client, for sending a file to the other machine.
echo.

call "%~dp0run-client.bat"
