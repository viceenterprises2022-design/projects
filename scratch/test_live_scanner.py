#!/usr/bin/env python3
import asyncio
import sys
import os

sys.path.append("/home/vreddy1/Desktop/Projects/scripts")
import fo_breakout_scanner as fbs

# Mock Live context manager to avoid console takeover and print updates
class MockLive:
    def __init__(self, layout, console, screen, refresh_per_second):
        self.layout = layout
        self.console = console
        
    def __enter__(self):
        print("MockLive entered")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        print("MockLive exited. Exception:", exc_val)
        return False # Propagate exceptions

async def run_mock_scanner():
    fbs.Live = MockLive # Monkeypatch Live
    
    # We will run a modified run_scanner that only runs for 3 iterations
    console = fbs.Console()
    layout = fbs.make_layout()
    
    state = {
        "spots": {"NIFTY 50": 0.0, "NIFTY BANK": 0.0},
        "spots_chg": {"NIFTY 50": 0.0, "NIFTY BANK": 0.0},
        "active_idx": "NIFTY 50",
        "current_expiry": None,
        "visible_rows": [],
        "walls": {},
        "alerts": {"volume_spurts": [], "iv_squeeze": ""},
        "status": "Initializing...",
        "switch_in": 15
    }
    
    # Start background tasks
    asyncio.create_task(fbs.update_data_loop(state))
    asyncio.create_task(fbs.index_switcher_loop(state))
    
    print("Starting MockLive loop...")
    with fbs.Live(layout, console=console, screen=False, refresh_per_second=1) as live:
        for i in range(3):
            print(f"\n--- Iteration {i+1} ---")
            
            # Update Layout Panels
            layout["header"].update(fbs.render_header(state))
            layout["calls_panel"].update(fbs.render_chains(state, "CALLS"))
            layout["strikes_panel"].update(fbs.render_strikes(state))
            layout["puts_panel"].update(fbs.render_chains(state, "PUTS"))
            layout["walls_panel"].update(fbs.render_walls(state))
            layout["alerts_panel"].update(fbs.render_alerts(state))
            
            print("Status:", state["status"])
            print("Header title:", getattr(layout["header"].renderable, "title", "None"))
            print("Calls Panel title:", getattr(layout["calls_panel"].renderable, "title", "None"))
            
            await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(run_mock_scanner())
    except Exception as e:
        print("CRASHED in main:", e)
