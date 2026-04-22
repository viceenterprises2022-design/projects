@echo off
:: AlphaEdge Ticker Banner — Windows Launcher
:: Double-click to run, or add to Task Scheduler for auto-start

echo AlphaEdge Ticker Banner
echo =======================

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install from https://python.org
    pause
    exit /b 1
)

:: Install dependencies
echo Installing dependencies...
python -m pip install requests yfinance --quiet --upgrade

:: Launch (hidden console window)
echo Starting ticker...
pythonw alphaedge_ticker.py
if errorlevel 1 (
    :: Fallback if pythonw not found
    python alphaedge_ticker.py
)
