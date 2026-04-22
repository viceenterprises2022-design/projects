import argparse
import json
import os
from src.orchestrator.main import TradingOrchestrator

def main():
    parser = argparse.ArgumentParser(description="Multi-Market Trading Analysis System")
    parser.add_argument("ticker", help="Ticker symbol (e.g., RELIANCE.NS, BTC/USDT, AAPL)")
    parser.add_argument("--type", choices=["equity", "crypto", "commodity"], default="equity", help="Asset type")
    
    args = parser.parse_args()
    
    # Auto-detect type if possible
    if "/" in args.ticker or args.ticker.isupper() and len(args.ticker) <= 5 and args.ticker not in ["GOLD", "SILVER", "OIL"]:
        # Simple heuristic for crypto (BTC/USDT) or US Stocks (AAPL)
        if "/" in args.ticker:
            args.type = "crypto"
        else:
            args.type = "equity"
    elif args.ticker in ["GOLD", "SILVER", "OIL"]:
        args.type = "commodity"
    
    try:
        orchestrator = TradingOrchestrator()
        
        print(f"--- Analyzing {args.ticker} ({args.type}) ---")
        
        if args.type == "equity":
            report = orchestrator.analyze_equity(args.ticker)
        elif args.type == "crypto":
            report = orchestrator.analyze_crypto(args.ticker)
        else:
            print("Commodity analysis not yet implemented in orchestrator.")
            return

        print(json.dumps(report, indent=2))
        
    except Exception as e:
        print(f"Error: {str(e)}")
        if "GOOGLE_API_KEY" in str(e):
            print("\nPlease set your GOOGLE_API_KEY environment variable.")
            print("Example: export GOOGLE_API_KEY='your-key-here'")

if __name__ == "__main__":
    main()
