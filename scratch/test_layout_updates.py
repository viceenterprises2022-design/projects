#!/usr/bin/env python3
import asyncio
import aiohttp
import sys
import os

sys.path.append("/home/vreddy1/Desktop/Projects/scripts")
import fo_breakout_scanner as fbs

async def main():
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
    
    print("Executing single data fetch step...")
    async with aiohttp.ClientSession() as session:
        # Fetch spots
        url_quotes = "https://api.upstox.com/v2/market-quote/quotes"
        quotes_res = await fbs.safe_get(session, url_quotes, {"instrument_key": ",".join(fbs.INDICES.values())})
        if isinstance(quotes_res, dict) and quotes_res.get("status") == "success":
            raw_data = quotes_res.get("data", {})
            for idx_name, idx_key in fbs.INDICES.items():
                api_key = idx_key.replace('|', ':')
                q = raw_data.get(api_key, {})
                spot = q.get("last_price", 0.0)
                ohlc = q.get("ohlc", {})
                close = ohlc.get("close", 0.0) or spot or 1.0
                chg = ((spot - close) / close) * 100
                state["spots"][idx_name] = spot
                state["spots_chg"][idx_name] = chg
            state["status"] = "OK"
        
        # Fetch Nifty option chain
        active_idx = state["active_idx"]
        active_key = fbs.INDICES[active_idx]
        expiries = await fbs.fetch_expiries(session, active_key)
        if expiries:
            state["current_expiry"] = expiries[0]
            chain_raw = await fbs.fetch_option_chain(session, active_key, expiries[0])
            spot = state["spots"].get(active_idx, 0.0)
            if chain_raw and spot > 0:
                processed = fbs.process_option_chain(chain_raw, spot)
                state["visible_rows"] = processed["visible_rows"]
                state["walls"] = processed["walls"]
                state["alerts"] = processed["alerts"]
                
    print("\nData fetched status:")
    print("state['visible_rows'] length:", len(state["visible_rows"]))
    print("state['spots']:", state["spots"])
    
    print("\nUpdating layout panels...")
    layout["header"].update(fbs.render_header(state))
    layout["calls_panel"].update(fbs.render_chains(state, "CALLS"))
    layout["strikes_panel"].update(fbs.render_strikes(state))
    layout["puts_panel"].update(fbs.render_chains(state, "PUTS"))
    layout["walls_panel"].update(fbs.render_walls(state))
    layout["alerts_panel"].update(fbs.render_alerts(state))
    
    print("\nVerifying layout updates in memory:")
    panels = ["header", "calls_panel", "strikes_panel", "puts_panel", "walls_panel", "alerts_panel"]
    for p_name in panels:
        renderable = layout[p_name].renderable
        print(f"Panel '{p_name}' renderable type: {type(renderable)}")
        if renderable is not None:
            # Let's check if the renderable is still the default placeholder
            is_placeholder = "Placeholder" in type(renderable).__name__
            print(f"  Is placeholder? {is_placeholder}")
            if hasattr(renderable, "title"):
                print(f"  Panel Title: {renderable.title}")

if __name__ == "__main__":
    asyncio.run(main())
