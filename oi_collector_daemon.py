#!/usr/bin/env python3
"""
AlphaEdge Intraday OI Collector Daemon
Standalone wrapper that runs market_analysis_v3's oi_collector_thread to continuously
populate intraday_oi.db.
"""
import sys
import os

# Ensure same-directory imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import market_analysis_v3 as ma

def main():
    print("[OI Collector Daemon] Initializing Database...", flush=True)
    ma.init_db()
    print("[OI Collector Daemon] Starting collection loop...", flush=True)
    ma.oi_collector_thread()

if __name__ == "__main__":
    main()
