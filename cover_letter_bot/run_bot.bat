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

where claude >nul 2>nul
if errorlevel 1 (
    echo.
    echo Claude Code CLI not found. This bot uses it to generate letters
    echo instead of a paid API key. Install it first:
    echo   npm install -g @anthropic-ai/claude-code
    echo then run "claude" once to log in, and run this script again.
    echo.
    pause
    exit /b 1
)

if not exist .env (
    copy .env.example .env >nul
    echo.
    echo A .env file was created. In the Notepad window that is about to open,
    echo fill in BOT_TOKEN ^(from @BotFather^), then save and close it.
    echo.
    pause
    notepad .env
)

echo.
echo Starting bot... close this window or press Ctrl+C to stop.
echo.
python bot.py

pause
