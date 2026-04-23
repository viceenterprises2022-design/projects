import argparse
import json
import os
import asyncio
from src.orchestrator.main import TradingOrchestrator
from src.common.telegram_client import TelegramClient

async def run_analysis(ticker, asset_type, send_telegram=False):
    try:
        orchestrator = TradingOrchestrator()
        
        print(f"--- Analyzing {ticker} ({asset_type}) ---")
        
        if asset_type == "equity":
            report = orchestrator.analyze_equity(ticker)
        elif asset_type == "crypto":
            report = orchestrator.analyze_crypto(ticker)
        else:
            print("Commodity analysis not yet implemented in orchestrator.")
            return

        print(json.dumps(report, indent=2))

        if send_telegram:
            tg = TelegramClient()
            if tg.is_configured:
                print(f"Sending report for {ticker} to Telegram...")
                success = await tg.send_report(ticker, report)
                if success:
                    print("✅ Telegram report sent.")
                else:
                    print("❌ Failed to send Telegram report.")
            else:
                print("⚠️ Telegram not configured. Skip sending.")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        if "GOOGLE_API_KEY" in str(e):
            print("\nPlease set your GOOGLE_API_KEY environment variable.")
            print("Example: export GOOGLE_API_KEY='your-key-here'")

def main():
    parser = argparse.ArgumentParser(description="Multi-Market Trading Analysis System")
    parser.add_argument("ticker", help="Ticker symbol (e.g., RELIANCE.NS, BTC/USDT, AAPL)")
    parser.add_argument("--type", choices=["equity", "crypto", "commodity"], default="equity", help="Asset type")
    parser.add_argument("--telegram", action="store_true", help="Send report to Telegram")
    
    args = parser.parse_args()
    
    # Auto-detect type if possible
    ticker_upper = args.ticker.upper()
    if "/" in args.ticker or (ticker_upper == args.ticker and len(args.ticker) <= 5 and ticker_upper not in ["GOLD", "SILVER", "OIL"]):
        if "/" in args.ticker:
            args.type = "crypto"
        else:
            args.type = "equity"
    elif ticker_upper in ["GOLD", "SILVER", "OIL"]:
        args.type = "commodity"
    
    asyncio.run(run_analysis(args.ticker, args.type, args.telegram))

if __name__ == "__main__":
    main()
