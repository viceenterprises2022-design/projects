import json
import urllib.request
import time
import os
import sys
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

CMC_API_KEY = "7f165fb95f174e6381a0d98391e1e53b"
CMC_URL = "https://mcp.coinmarketcap.com/skill-hub/stream"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import send_telegram_msg as tg

def call_mcp(method, params):
    req_body = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    req = urllib.request.Request(
        CMC_URL,
        data=json.dumps(req_body).encode("utf-8"),
        headers={"X-CMC-MCP-API-KEY": CMC_API_KEY, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            result = None
            for line in raw.split("\n"):
                if line.startswith("data:"):
                    ld = json.loads(line[5:])
                    if "result" in ld:
                        result = ld["result"]
            if result is None:
                try:
                    ld = json.loads(raw)
                    if "result" in ld:
                        result = ld["result"]
                except:
                    pass
            return result
    except Exception as e:
        return {"error": str(e)}

def execute_skill(name, params):
    return call_mcp("tools/call", {"name": "execute_skill", "arguments": {"unique_name": name, "parameters": params}})

def find_skill(query):
    return call_mcp("tools/call", {"name": "find_skill", "arguments": {"query": query}})

def parse_output(raw):
    txt = raw["content"][0]["text"]
    obj = json.loads(txt)
    r = obj.get("result", {})
    out = r.get("output")
    if isinstance(out, str):
        inner = json.loads(out)
        r = inner.get("result", inner)
    data = r.get("data", r)
    if not isinstance(data, dict):
        data = {}
    report = data.get("decision_report", data.get("report", {}))
    return data, report

def fval(v, fmt=""):
    if v is None:
        return "-"
    if isinstance(v, (int, float)):
        if fmt == "money":
            if abs(v) >= 1e9:
                return f"${v/1e9:.2f}B"
            if abs(v) >= 1e6:
                return f"${v/1e6:.2f}M"
            return f"${v:,.0f}"
        if fmt == "pct2":
            return f"{v:.2f}%"
        if fmt == "pct4":
            return f"{v:.4f}%"
        if fmt == "f4":
            return f"{v:.4f}"
        if fmt == "f2":
            return f"{v:.2f}"
        return str(v)
    return str(v)

def now_ist():
    return datetime.now(IST).strftime("%d %b %Y %H:%M IST")

def now_ist_date():
    return datetime.now(IST).strftime("%d %b %Y")

# ─── Skill Definitions ───

DAILY_SKILLS = [
    {"name": "daily_market_overview", "params": {"preview": True}, "label": "Market Overview"},
    {"name": "perp_contract_analysis", "params": {"symbol": "BTC", "timeframe": "4h", "lookback_days": 14, "exchange_list": "Binance,OKX,Bybit"}, "label": "BTC Perp Analysis"},
    {"name": "btc_etf_institutional_demand", "params": {"preview": True}, "label": "BTC ETF Demand"},
    {"name": "btc_cross_asset_correlation", "params": {"preview": True}, "label": "Cross-Asset Correlation"},
    {"name": "macro_news_aggregator", "params": {"preview": True, "lookback_hours": 72, "live_fetch": False}, "label": "Macro News"},
    {"name": "crypto_macro_overview", "params": {"preview": True}, "label": "Crypto Macro Overview"},
]

WEEKLY_SKILLS = [
    {"name": "assess_altcoin_sector_relative_position", "params": {"symbol": "RENDER", "convert": "USD"}, "label": "Sector Rotation Analysis"},
    {"name": "altcoin_scanner_perp", "params": {"preview": True}, "label": "Altcoin Perp Scanner"},
    {"name": "macro_financial_conditions", "params": {}, "label": "Macro Financial Conditions"},
    {"name": "assess_macro_liquidity_risk_regime", "params": {"preview": True}, "label": "Liquidity Risk Regime"},
    {"name": "detect_holder_distribution_trend", "params": {"token_id_or_symbol": "AAVE", "platform": "ethereum", "token_address": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"}, "label": "Holder Distribution Trend"},
    {"name": "detect_protocol_revenue_tvl_divergence", "params": {"protocol": "Uniswap"}, "label": "Protocol Revenue/TVL"},
    {"name": "rank_defi_protocol_economic_quality", "params": {}, "label": "DeFi Protocol Screen"},
    {"name": "assess_oracle_chain_expansion_trend", "params": {"protocol_or_chain": "Ethereum"}, "label": "Oracle Chain Expansion"},
]

def run_skills(skills, force=False):
    results = {}
    for s in skills:
        label = s["label"]
        print(f"  [{label}] executing...", end=" ", flush=True)
        res = execute_skill(s["name"], s["params"])
        if not res or "error" in res:
            print(f"FAILED: {res.get('error', 'no response')}")
            results[label] = None
        else:
            print("OK")
            results[label] = res
        time.sleep(2)
    return results

# ─── Formatting Functions ───

def fmt_daily_market_overview(data, report):
    mr = data.get("market_read", {})
    fc = data.get("macro_deep_read", {}).get("financial_conditions", {})
    nfci = fc.get("nfci", {})
    inf = fc.get("inflation_outlook", {})
    kms = fc.get("key_metrics", [])
    lines = [
        "<b>📊 Market Overview</b>",
        f"Regime: {mr.get('regime','-')}",
        f"Composite Score: <b>{mr.get('composite_score','?')}/100</b>",
        f"Risk Bias: {mr.get('risk_bias','-')}",
        f"Max Position: {mr.get('risk_budget',{}).get('max_position_pct','?')}% | Leverage: {mr.get('risk_budget',{}).get('leverage','-')}",
        "",
        f"Fear & Greed: <b>{kms[0].split()[-1] if kms else '?'}</b> | CMC100 24h: {kms[1] if len(kms)>1 else '?'}",
        f"Altcoin Season: {kms[2] if len(kms)>2 else '?'}/100",
        f"NFCI: {fval(nfci.get('current'),'f2')} ({nfci.get('regime','-')})",
        f"CPI: {fval(inf.get('cpi_latest'),'f2')}% | DXY: {fval(fc.get('dxy_analysis',{}).get('current'),'f2')}",
    ]
    return "\n".join(lines)

def fmt_btc_perp(data, report):
    ccl = report.get("conclusion", data.get("summary", ""))
    lines = ["<b>🔷 BTC Perp Analysis</b>"]
    if "current price is" in ccl:
        price = ccl.split("current price is")[1].split(",")[0].strip()
        lines.append(f"Price: <b>${price}</b>")
    if "84 x 4h price change is" in ccl:
        pchg = ccl.split("84 x 4h price change is")[1].split(",")[0].strip()
        lines.append(f"Price Δ (84×4h): {pchg}")
    if "84 x 4h OI change is" in ccl:
        oichg = ccl.split("84 x 4h OI change is")[1].split(",")[0].strip()
        lines.append(f"OI Δ (84×4h): {oichg}")
    if "funding is still mildly positive at" in ccl:
        fund = ccl.split("funding is still mildly positive at")[1].split("%")[0].strip()
        lines.append(f"Funding Rate: {fund}% (mildly positive)")
    if "84 x 4h futures CVD latest_delta is" in ccl:
        fCVD = ccl.split("84 x 4h futures CVD latest_delta is")[1].split("and")[0].strip()
        lines.append(f"Futures CVD Δ: {fCVD}")
    if "84 x 4h spot CVD latest_delta is" in ccl:
        sCVD = ccl.split("84 x 4h spot CVD latest_delta is")[1].split(",")[0].strip()
        lines.append(f"Spot CVD Δ: {sCVD}")
    lines.append("")
    # Conclusion snippet
    lines.append(ccl[:300].rsplit(".", 1)[0] + ".")
    return "\n".join(lines)

def fmt_etf_demand(data, report):
    lines = ["<b>🏦 BTC ETF Demand</b>"]
    if "signal-window net flow" in str(data):
        rawstr = str(data)
        import re
        net = re.search(r"signal-window net flow[^,]*?([-\d.]+[BMK]?|\-?\$[\d.]+[BMK]?)", rawstr)
        ibit = re.search(r"IBIT[^}]*?outflow[^}]*?([-\d.]+[BMK]?|\-?\$[\d.]+[BMK]?)", rawstr)
        if net:
            lines.append(f"Net Flow (signal window): {net.group(1)}")
        if ibit:
            lines.append(f"IBIT: {ibit.group(1)}")
    else:
        lines.append("Net flow data unavailable in parse output")
    conclusion = data.get("summary", report.get("conclusion", ""))
    if conclusion:
        if "does NOT qualify" in conclusion:
            lines.append("Verdict: ❌ Does not qualify as institutional confirmation")
        elif "net outflows" in conclusion.lower():
            lines.append("Verdict: ⚠️ Net outflows dominate")
        elif "neutral" in conclusion.lower():
            lines.append("Verdict: ⚖️ Neutral")
        else:
            lines.append(f"Verdict: {conclusion[:200]}")
    return "\n".join(lines)

def fmt_cross_asset(data, report):
    ccl = report.get("conclusion", data.get("summary", ""))
    lines = ["<b>🔄 Cross-Asset Correlation</b>"]
    if "current regime is" in ccl:
        reg = ccl.split("current regime is")[1].split(",")[0].strip()
        lines.append(f"Regime: <b>{reg}</b>")
    for pair, label in [("Nasdaq", "Nasdaq"), ("SPX", "S&P 500"), ("Gold", "Gold"), ("DXY", "DXY")]:
        if f"versus {pair} is" in ccl:
            short = ccl.split(f"versus {pair} is")[1].split(",")[0].strip()
            lines.append(f"vs {label}: {short}")
    if "dollar backdrop is" in ccl:
        dxy = ccl.split("dollar backdrop is")[1].split(",")[0].strip()
        lines.append(f"DXY Backdrop: {dxy}")
    lines.append("")
    if ccl:
        lines.append(ccl[:300].rsplit(".", 1)[0] + ".")
    return "\n".join(lines)

def fmt_macro_news(data, report):
    lines = ["<b>📰 Macro News (72h)</b>"]
    events = data.get("events", data.get("key_events", []))
    if not events:
        events = data.get("report", {}).get("events", [])
    if events:
        for ev in events[:5]:
            if isinstance(ev, dict):
                title = ev.get("title", ev.get("headline", ev.get("event", "")))
                date = ev.get("date", ev.get("timestamp", ""))
                lines.append(f"• {title} ({date})" if date else f"• {title}")
            else:
                lines.append(f"• {ev}")
    else:
        summary = data.get("summary", report.get("conclusion", ""))
        if summary:
            lines.append(summary[:300])
    bias = data.get("bias", data.get("impact", ""))
    if bias:
        lines.append(f"\nBias: <b>{bias}</b>")
    return "\n".join(lines)

def fmt_crypto_macro_overview(data, report):
    lines = ["<b>🌍 Crypto Macro Overview</b>"]
    summary = data.get("summary", report.get("conclusion", ""))
    if summary:
        lines.append(summary[:300])
    status = data.get("status", "")
    if status:
        lines.append(f"Status: {status}")
    return "\n".join(lines)

# ─── Weekly Formatting ───

def fmt_sector_rotation(data, report):
    lines = ["<b>📈 Sector Rotation Analysis</b>"]
    for k in ["primary_subject", "symbol"]:
        if k in report:
            lines.append(f"Asset: {report[k]}")
            break
    state = report.get("rotation_signal", data.get("rotation_signal", ""))
    if state:
        lines.append(f"Rotation Signal: <b>{state}</b>")
    momentum = report.get("sector_momentum", data.get("sector_momentum", ""))
    if momentum:
        lines.append(f"Momentum: {momentum}")
    summary = data.get("summary", report.get("conclusion", ""))
    if summary:
        lines.append(f"\n{summary[:250]}")
    return "\n".join(lines)

def fmt_altcoin_scanner(data, report):
    lines = ["<b>🪙 Altcoin Perp Scanner</b>"]
    candidates = data.get("candidates", report.get("candidates", []))
    if candidates:
        lines.append(f"Total candidates: {len(candidates)}")
        for c in candidates[:3]:
            if isinstance(c, dict):
                name = c.get("symbol", c.get("name", "?"))
                score = c.get("score", c.get("rank", ""))
                bias = c.get("bias", c.get("signal", ""))
                lines.append(f"• {name} | Score: {score} | Bias: {bias}")
    else:
        summary = data.get("summary", report.get("conclusion", data.get("conclusion", "")))
        if summary:
            lines.append(summary[:250])
    return "\n".join(lines)

def fmt_macro_financial(data, report):
    lines = ["<b>🏛️ Macro Financial Conditions</b>"]
    if report:
        for k in ["financial_conditions_index", "current", "value"]:
            if k in report:
                lines.append(f"FCI: {report[k]}")
                break
    for metric in ["2y_yield", "10y_yield", "cpi", "unemployment"]:
        for lookup in [data, report]:
            if isinstance(lookup, dict) and metric in lookup:
                lines.append(f"{metric.replace('_',' ').title()}: {lookup[metric]}")
                break
    if not lines:
        summary = data.get("summary", report.get("conclusion", ""))
        if summary:
            lines.append(summary[:300])
    return "\n".join(lines)

def fmt_liquidity(data, report):
    lines = ["<b>💧 Liquidity Risk Regime</b>"]
    for key in ["fed_balance_sheet", "rrp", "tga", "net_liquidity"]:
        for lookup in [data, report]:
            if isinstance(lookup, dict) and key in lookup:
                val = lookup[key]
                if isinstance(val, (int, float)):
                    lines.append(f"{key.replace('_',' ').title()}: ${val:,.0f}")
                else:
                    lines.append(f"{key.replace('_',' ').title()}: {val}")
                break
    trend = data.get("trend", report.get("trend", data.get("liquidity_trend", "")))
    if trend:
        lines.append(f"Trend: {trend}")
    summary = data.get("summary", report.get("conclusion", ""))
    if summary and len(lines) < 3:
        lines.append(summary[:250])
    return "\n".join(lines)

def fmt_holder_distribution(data, report):
    lines = ["<b>👥 Holder Distribution (AAVE)</b>"]
    lines.append(f"Holders: {fval(report.get('holder_count'),',')}")
    lines.append(f"State: {report.get('distribution_state','-')}")
    lines.append(f"Growth: {fval(report.get('trend_metrics',{}).get('holder_growth_pct'),'pct2')}")
    lines.append(f"Top 10 Share: {fval(report.get('latest_snapshot',{}).get('top_10_holder_share_pct'),'pct2')}")
    lines.append(f"Top 50: {fval(report.get('latest_snapshot',{}).get('top_50_balance'),'pct2')}")
    summary = data.get("summary", report.get("conclusion", ""))
    if summary:
        lines.append(f"\n{summary[:200]}")
    return "\n".join(lines)

def fmt_protocol_revenue(data, report):
    lines = ["<b>⚡ Uniswap Revenue/TVL</b>"]
    lines.append(f"Divergence: {report.get('divergence_state','-')}")
    lines.append(f"TVL: {fval(report.get('current_tvl_usd'),'money')}")
    lines.append(f"TVL Δ: {fval(report.get('tvl_change_pct_recent_window'),'pct2')}")
    lines.append(f"Revenue (30d): {fval(report.get('revenue_30d_usd'),'money')}")
    lines.append(f"Fees (30d): {fval(report.get('fees_30d_usd'),'money')}")
    return "\n".join(lines)

def fmt_defi_screen(data, report):
    lines = ["<b>🔗 DeFi Protocol Screen</b>"]
    protocols = data.get("protocols", report.get("protocols", []))
    if protocols:
        for p in protocols[:3]:
            if isinstance(p, dict):
                name = p.get("name", p.get("protocol", "?"))
                tvl = fval(p.get("tvl", p.get("current_tvl_usd")), "money")
                rev = fval(p.get("revenue_30d", p.get("revenue_30d_usd")), "money")
                eff = p.get("revenue_efficiency", p.get("rev_tvl_bps", ""))
                lines.append(f"• {name}: TVL {tvl} | Rev {rev} | Eff: {eff}")
    else:
        for pname in ["Aave", "Uniswap", "Lido"]:
            pdata = data.get(pname.lower(), report.get(pname.lower(), {}))
            if pdata:
                tvl = fval(pdata.get("tvl", pdata.get("current_tvl_usd")), "money")
                rev = fval(pdata.get("revenue_30d", pdata.get("revenue_30d_usd")), "money")
                lines.append(f"• {pname}: TVL {tvl} | Rev {rev}")
    summary = data.get("summary", report.get("conclusion", ""))
    if summary:
        lines.append(f"\n{summary[:200]}")
    return "\n".join(lines)

def fmt_oracle_expansion(data, report):
    lines = ["<b>⛓️ Oracle Chain Expansion</b>"]
    lines.append(f"Chain: Ethereum")
    tvl = report.get("current_value", data.get("current_value", ""))
    if not tvl:
        tvl = report.get("oracle_secured_value", data.get("oracle_secured_value", ""))
    if tvl:
        lines.append(f"Secured Value: {fval(tvl,'money') if isinstance(tvl,(int,float)) else tvl}")
    growth = report.get("growth_pct", data.get("growth_pct", ""))
    if growth:
        lines.append(f"Growth: {fval(growth,'pct2') if isinstance(growth,(int,float)) else growth}")
    else:
        growth_delta = report.get("90d_growth", data.get("90d_growth", ""))
        if growth_delta:
            lines.append(f"90d Δ: {fval(growth_delta,'pct2') if isinstance(growth_delta,(int,float)) else growth_delta}")
    summary = data.get("summary", report.get("conclusion", ""))
    if summary:
        lines.append(f"\n{summary[:200]}")
    return "\n".join(lines)

# ─── Report Builder ───

FMT_LOOKUP = {
    "Market Overview": fmt_daily_market_overview,
    "BTC Perp Analysis": fmt_btc_perp,
    "BTC ETF Demand": fmt_etf_demand,
    "Cross-Asset Correlation": fmt_cross_asset,
    "Macro News": fmt_macro_news,
    "Crypto Macro Overview": fmt_crypto_macro_overview,
    "Sector Rotation Analysis": fmt_sector_rotation,
    "Altcoin Perp Scanner": fmt_altcoin_scanner,
    "Macro Financial Conditions": fmt_macro_financial,
    "Liquidity Risk Regime": fmt_liquidity,
    "Holder Distribution Trend": fmt_holder_distribution,
    "Protocol Revenue/TVL": fmt_protocol_revenue,
    "DeFi Protocol Screen": fmt_defi_screen,
    "Oracle Chain Expansion": fmt_oracle_expansion,
}

def build_report(report_type, raw_results):
    if report_type == "daily":
        title = "📡 <b>Crypto Intelligence — Daily Brief</b>"
        skills = DAILY_SKILLS
    else:
        title = "📡 <b>Crypto Intelligence — Weekly Report</b>"
        skills = WEEKLY_SKILLS

    header = f"{title}\n{now_ist()}\n{'='*40}\n\n"
    body_parts = []

    for s in skills:
        label = s["label"]
        raw = raw_results.get(label)
        if raw is None:
            body_parts.append(f"<b>{label}</b>\n⚠️ Data unavailable\n")
            continue
        data, report = parse_output(raw)
        fmt_fn = FMT_LOOKUP.get(label)
        if fmt_fn:
            section = fmt_fn(data, report)
        else:
            section = f"<b>{label}</b>\n{data.get('summary','')[:200]}"
        body_parts.append(section)

    report_text = header + "\n\n".join(body_parts)
    return report_text

def send_report(text):
    MAX_CHARS = 3900
    chunks = [text[i:i+MAX_CHARS] for i in range(0, len(text), MAX_CHARS)]
    for i, chunk in enumerate(chunks):
        tag = f" ({i+1}/{len(chunks)})" if len(chunks) > 1 else ""
        tg.send_text(chunk + tag)
        if i < len(chunks) - 1:
            time.sleep(1)
    return len(chunks)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Crypto Intelligence Reporter")
    parser.add_argument("--daily", action="store_true", help="Generate and send daily report")
    parser.add_argument("--weekly", action="store_true", help="Generate and send weekly report")
    parser.add_argument("--force", action="store_true", help="Force re-run all skills even if cached recently")
    args = parser.parse_args()

    if not args.daily and not args.weekly:
        parser.print_help()
        sys.exit(1)

    if args.daily:
        print("=== Crypto Intelligence Daily Brief ===")
        print(f"Running {len(DAILY_SKILLS)} daily skills...")
        raw = run_skills(DAILY_SKILLS, force=args.force)
        print("Building daily report...")
        report = build_report("daily", raw)
        print(f"Report size: {len(report)} chars")
        print("Sending to Telegram...")
        n = send_report(report)
        print(f"Sent in {n} message(s).")

    if args.weekly:
        print("\n=== Crypto Intelligence Weekly Report ===")
        print(f"Running {len(WEEKLY_SKILLS)} weekly skills...")
        raw = run_skills(WEEKLY_SKILLS, force=args.force)
        print("Building weekly report...")
        report = build_report("weekly", raw)
        print(f"Report size: {len(report)} chars")
        print("Sending to Telegram...")
        n = send_report(report)
        print(f"Sent in {n} message(s).")

if __name__ == "__main__":
    main()
