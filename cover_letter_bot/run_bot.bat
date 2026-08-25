@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set PYTHON=
where python >nul 2>nul && set PYTHON=python
if not defined PYTHON (
    where py >nul 2>nul && set PYTHON=py
)
if not defined PYTHON (
    echo Python not found. Install Python 3.11+ from python.org
    echo ^(tick "Add python.exe to PATH" during install^) and run this again.
    pause
    exit /b 1
)

if not exist venv (
    echo Creating virtual environment and installing dependencies, please wait...
    %PYTHON% -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

if not exist .env (
    copy .env.example .env >nul
    echo.
    echo A .env file was created. In the Notepad window that is about to open,
    echo fill in BOT_TOKEN ^(from @BotFather^) and ANTHROPIC_API_KEY
    echo ^(from console.anthropic.com^), then save and close it.
    echo.
    pause
    notepad .env
)

echo.
echo Starting bot... close this window or press Ctrl+C to stop.
echo.
python bot.py

pause
