#!/bin/bash
# start_collectors.sh
# Starts all AlphaEdge market data collectors in the background cleanly

CDIR="/home/vreddy1/Desktop/Projects/scripts"
cd "$CDIR"

# Create logs directory if not exists
mkdir -p logs

echo "=== Stopping existing collector instances ==="
pkill -f "collector.py --loop"
pkill -f "options_cli.py"
pkill -f "oi_collector_daemon.py"
sleep 1

echo "=== Starting data collectors in background ==="

# 1. Start alphaedge.db collector (1-min interval)
nohup "$CDIR/venv/bin/python" collector.py --loop --interval 1 > logs/collector_background.log 2>&1 &
echo "✓ Started collector.py (alphaedge.db) in background"

# 2. Start options chain collector (5-sec polling)
nohup "$CDIR/venv/bin/python" options_cli.py > logs/options_background.log 2>&1 &
echo "✓ Started options_cli.py (intraday_options_cli.db) in background"

# 3. Start intraday PCR trend collector (1-min interval)
nohup "$CDIR/venv/bin/python" oi_collector_daemon.py > logs/oi_background.log 2>&1 &
echo "✓ Started oi_collector_daemon.py (intraday_oi.db) in background"

echo "=== All collectors initialized ==="
