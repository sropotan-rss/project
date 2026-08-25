#!/bin/bash
cd "$(dirname "$0")"

if ! command -v python3 &> /dev/null; then
    echo "Python 3 not found. Install it from python.org and run this again."
    read -p "Press Enter to close..."
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "Creating virtual environment and installing dependencies, please wait..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "A .env file was created at $(pwd)/.env"
    echo "Fill in BOT_TOKEN (from @BotFather) and ANTHROPIC_API_KEY"
    echo "(from console.anthropic.com) in the editor that is about to open,"
    echo "save it, then run this script again."
    open -e .env
    read -p "Press Enter to close..."
    exit 1
fi

echo ""
echo "Starting bot... press Ctrl+C to stop, or just close this window."
echo ""
python bot.py

read -p "Bot stopped. Press Enter to close..."
