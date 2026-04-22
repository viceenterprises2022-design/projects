#!/bin/bash
# AlphaEdge Ticker Banner — Ubuntu/Linux Launcher
# Run: bash launch_ubuntu.sh
# Auto-start: copy .desktop file to ~/.config/autostart/

echo "AlphaEdge Ticker Banner"
echo "========================"

# Ensure tkinter is available (Ubuntu needs separate install)
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "Installing python3-tk..."
    sudo apt-get install -y python3-tk
fi

# Ensure pip
if ! command -v pip3 &>/dev/null; then
    sudo apt-get install -y python3-pip
fi

echo "Installing Python dependencies..."
pip3 install requests yfinance --quiet --upgrade --break-system-packages 2>/dev/null || \
pip3 install requests yfinance --quiet --upgrade

echo "Starting ticker..."
python3 "$(dirname "$0")/alphaedge_ticker.py"
