import json
import os

def main():
    files = {
        "Daily Overview": "scratch/daily_market_overview_output.json",
        "Market Sentiment Shift": "scratch/monitor_market_sentiment_shift_output.json",
        "Revenue/TVL Divergence": "scratch/detect_protocol_revenue_tvl_divergence_output.json",
        "Holder Distribution": "scratch/detect_holder_distribution_trend_output.json",
        "Perp Contract Analysis": "scratch/perp_analysis_output.json",
        "Orderbook Wall Migration": "scratch/detect_orderbook_wall_migration_output.json",
        "BTC Cross-Asset Correlation": "scratch/cross_asset_analysis_output.json"
    }

    for label, path in files.items():
        if not os.path.exists(path):
            print(f"[{label}] File not found.")
            continue
        try:
            with open(path, "r") as f:
                raw = json.load(f)
            text = raw["content"][0]["text"]
            data = json.loads(text)
            
            # Unpack nested output string if present
            if "result" in data and "output" in data["result"]:
                inner = json.loads(data["result"]["output"])
                data = inner
                
            report_data = data.get("result", {}).get("data", {})
            if not report_data:
                report_data = data.get("data", {})
                
            rep = report_data.get("decision_report", {})
            if not rep:
                rep = report_data.get("report", {})
            if not rep:
                rep = report_data
                
            print(f"\n=== {label} ===")
            status = report_data.get("status", "N/A")
            conf = report_data.get("confidence", "N/A")
            if isinstance(conf, dict):
                conf = conf.get("level", "N/A")
            print(f"Status: {status} | Confidence: {conf}")
            
            conclusion = rep.get("conclusion", report_data.get("summary", "N/A"))
            print(f"Conclusion: {conclusion}")
            
            # Print unique keys depending on skill
            if "correlation" in report_data:
                print(f"Correlations: {json.dumps(report_data.get('correlation'), indent=2)}")
            elif "correlation" in rep:
                print(f"Correlations: {json.dumps(rep.get('correlation'), indent=2)}")
            elif "top_protocols" in rep:
                print(f"Protocols: {[p.get('name') for p in rep.get('top_protocols', [])]}")
            elif "holder_count" in rep:
                print(f"Holders: {rep.get('holder_count')} | Base State: {rep.get('holder_base_state')}")
            elif "latest_closed_price" in rep:
                print(f"Price: {rep.get('latest_closed_price')} | Trend: {rep.get('trend_context', {}).get('trend')}")
        except Exception as e:
            print(f"Error parsing {label}: {e}")

if __name__ == "__main__":
    main()
