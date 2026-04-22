#!/bin/bash
# AlphaEdge Ticker Banner — macOS Launcher
# Run: bash launch_macos.sh
# Auto-start: add to Login Items or use launchd plist

echo "AlphaEdge Ticker Banner"
echo "========================"

# Check Python3
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install from https://python.org or via Homebrew:"
    echo "  brew install python"
    exit 1
fi

echo "Installing dependencies..."
pip3 install requests yfinance --quiet --upgrade

echo "Starting ticker..."
python3 "$(dirname "$0")/alphaedge_ticker.py"
