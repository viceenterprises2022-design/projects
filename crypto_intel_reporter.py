import json
import urllib.request
import time
import os
import sys
import re
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
        with urllib.request.urlopen(req, timeout=120) as resp:
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

def parse_output(raw):
    txt = raw["content"][0]["text"]
    obj = json.loads(txt)
    r = obj.get("result", {})
    out = r.get("output")
    if isinstance(out, str):
        inner = json.loads(out)
        r = inner.get("result", inner)
    d = r
    if d.get("ok") is True and "data" in d:
        d = d["data"]
    if "data" in d and isinstance(d["data"], dict) and "type" in d:
        d = d["data"]
    dr = d.get("decision_report", d.get("report", {}))
    return d, dr

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
        if fmt == "f2":
            return f"{v:.2f}"
        return str(v)
    return str(v)

def now_ist():
    return datetime.now(IST).strftime("%d %b %Y %H:%M IST")

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
    {"name": "assess_altcoin_sector_relative_position", "params": {"symbol": "RENDER", "convert": "USD"}, "label": "Sector Rotation"},
    {"name": "altcoin_scanner_perp", "params": {"preview": True}, "label": "Altcoin Perp Scanner"},
    {"name": "macro_financial_conditions", "params": {}, "label": "Macro Financial Conditions"},
    {"name": "assess_macro_liquidity_risk_regime", "params": {"preview": True}, "label": "Liquidity Risk Regime"},
    {"name": "detect_holder_distribution_trend", "params": {"token_id_or_symbol": "AAVE", "platform": "ethereum", "token_address": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"}, "label": "Holder Distribution"},
    {"name": "detect_protocol_revenue_tvl_divergence", "params": {"protocol": "Uniswap"}, "label": "Protocol Revenue/TVL"},
    {"name": "rank_defi_protocol_economic_quality", "params": {}, "label": "DeFi Protocol Screen"},
    {"name": "assess_oracle_chain_expansion_trend", "params": {"protocol_or_chain": "Ethereum"}, "label": "Oracle Chain Expansion"},
]

def run_skills(skills):
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

# ─── Text parsers ───

def extract_metrics(text, *fields):
    vals = {}
    for f in fields:
        pat = rf"{re.escape(f)}[:\s]+([\-\d.]+%?)"
        m = re.search(pat, text)
        if m:
            vals[f] = m.group(1).strip() if m.group(1).strip() else m.group(1)
    return vals

def extract_dollar_val(text, label):
    pat = rf"{re.escape(label)}[:\s]*(?:is )?\$?([\-\d,]+(?:\.\d+)?)"
    m = re.search(pat, text)
    if m:
        return m.group(1).strip()
    pat2 = rf"{re.escape(label)}[:\s]*(?:is )?([\-\d,]+(?:\.\d+)?)\s*B(TC|itcoin)?"
    m2 = re.search(pat2, text)
    if m2:
        return m2.group(1).strip()
    return None

# ─── Formatting Functions ───

def fmt_market_overview(data, dr):
    mc = data.get("market_read", {})
    fc = data.get("macro_deep_read", {}).get("financial_conditions", {})
    kms = fc.get("key_metrics", [])
    ta = data.get("trader_assessment", {})
    conflicts = mc.get("primary_conflicts", [])
    lines = ["<b>📊 Market Overview</b>"]
    lines.append(f"Regime: <b>{mc.get('regime','-')}</b> | Score: <b>{mc.get('composite_score','?')}/100</b>")
    lines.append(f"Risk Bias: {mc.get('risk_bias','-')}")
    lines.append(f"Position: {mc.get('risk_budget',{}).get('max_position_pct','?')}% | Leverage: {mc.get('risk_budget',{}).get('leverage','-')}")
    if kms:
        for km in kms[:8]:
            lines.append(f"• {km}")
    if conflicts:
        for c in conflicts[:2]:
            lines.append(f"⚠️ {c}")
    if ta:
        tc = ta.get("conclusion", "")
        if tc:
            lines.append(f"\nTrader: {tc[:200]}")
    conclusion = dr.get("conclusion", "")
    if conclusion:
        lines.append(f"Summary: {conclusion[:250]}")
    return "\n".join(lines)

def fmt_btc_perp(data, dr):
    analysis = dr.get("analysis", "")
    conclusion = dr.get("conclusion", "")
    lines = ["<b>🔷 BTC Perp Analysis</b>"]
    metrics = {}
    m1 = re.search(r"current price(?: is)?[:\s]*\$?([\d,]+\.?\d*)", analysis)
    if m1:
        metrics["Price"] = f"${m1.group(1)}"
    m2 = re.search(r"price change is[:\s]*([-\d.]+%)", analysis)
    if m2:
        metrics["Price Δ (84×4h)"] = m2.group(1)
    m3 = re.search(r"OI change is[:\s]*([-\d.]+%)", analysis)
    if m3:
        metrics["OI Δ (84×4h)"] = m3.group(1)
    m4 = re.search(r"funding is still[^.]*?([-\d.]+%)", analysis)
    if m4:
        metrics["Funding Rate"] = m4.group(1)
    m5 = re.search(r"(futures CVD|spot CVD)[^.]*?([-\d.]+)", analysis)
    if m5:
        metrics[f"{m5.group(1).title()} Δ"] = m5.group(2)
    m6 = re.search(r"classifies the core relation as\s*([\w_]+)", analysis)
    if m6:
        metrics["Core Relation"] = m6.group(1)
    for k, v in metrics.items():
        lines.append(f"• <b>{k}</b>: {v}")
    status_str = re.search(r"the \d+ x \d+h classification is\s*([\w_]+)", analysis)
    if status_str:
        lines.append(f"\nClassification: <b>{status_str.group(1)}</b>")
    lines.append("")
    lines.append(conclusion[:300])
    return "\n".join(lines)

def fmt_etf_demand(data, dr):
    analysis = dr.get("analysis", "")
    conclusion = dr.get("conclusion", "")
    lines = ["<b>🏦 BTC ETF Demand</b>"]
    net_flow = re.search(r"signal-window net flow is\s*\$?([\-\d,]+(?:\.\d+)?)", analysis)
    if net_flow:
        lines.append(f"Net Flow (window): <b>${net_flow.group(1)}</b>")
    btc_flow = re.search(r"or\s*([\-\d,]+\.?\d*)\s*BTC", analysis)
    if btc_flow:
        lines.append(f"Flow (BTC): <b>{btc_flow.group(1)} BTC</b>")
    aum_pct = re.search(r"equals\s*([\-\d.]+%)\s*of the latest spot ETF AUM", analysis)
    if aum_pct:
        lines.append(f"AUM %: {aum_pct.group(1)}")
    score = re.search(r"institutional_demand_score[:\s]*([\d.]+)", analysis)
    if score:
        lines.append(f"Demand Score: <b>{score.group(1)}/1.0</b>")
    lines.append("")
    # Verdict
    if "does NOT qualify" in conclusion:
        lines.append("Verdict: ❌ <b>Does not qualify</b> — insufficient institutional confirmation")
    elif "net outflows" in conclusion.lower() and "not yet" not in conclusion.lower():
        lines.append("Verdict: ⚠️ <b>Net outflows dominate</b>")
    else:
        lines.append(conclusion[:250])
    return "\n".join(lines)

def fmt_cross_asset(data, dr):
    analysis = dr.get("analysis", "")
    conclusion = dr.get("conclusion", "")
    lines = ["<b>🔄 Cross-Asset Correlation</b>"]
    regime = re.search(r"current regime is\s*([\w_]+)", analysis)
    if regime:
        lines.append(f"Regime: <b>{regime.group(1)}</b>")
    for asset in ["Nasdaq", "SPX", "Gold", "DXY"]:
        m = re.search(rf"{asset}[^.]*?([\d.]+)", analysis)
        if m:
            lines.append(f"vs {asset}: {m.group(1)}")
    dxy_backdrop = re.search(r"(dollar backdrop)[^.]*?(is\s[\w\s]+?)(?=\.)", analysis, re.I)
    if dxy_backdrop:
        lines.append(f"DXY: {dxy_backdrop.group(2).strip()}")
    lines.append("")
    lines.append(conclusion[:300])
    return "\n".join(lines)

def fmt_macro_news(data, dr):
    analysis = dr.get("analysis", "")
    conclusion = dr.get("conclusion", "")
    lines = ["<b>📰 Macro News (72h)</b>"]
    events = data.get("events", data.get("key_events", []))
    if events:
        for ev in events[:4]:
            if isinstance(ev, dict):
                t = ev.get("title", ev.get("headline", ev.get("event", "")))
                d = ev.get("date", ev.get("timestamp", ""))
                lines.append(f"• {t} ({d})" if d else f"• {t}")
            else:
                lines.append(f"• {ev}")
    bias = data.get("bias", data.get("impact", ""))
    if bias:
        lines.append(f"\nBias: <b>{bias}</b>")
    if analysis:
        sections = re.split(r"##\s+", analysis)
        for sec in sections:
            sec = sec.strip()
            if not sec:
                continue
            header = sec.split("\n")[0]
            if len(sec) > 30:
                lines.append(f"• <b>{header}</b>: {sec[:200]}")
    lines.append("")
    lines.append(conclusion[:300])
    return "\n".join(lines)

def fmt_crypto_macro(data, dr):
    analysis = dr.get("analysis", "")
    conclusion = dr.get("conclusion", "")
    lines = ["<b>🌍 Crypto Macro Overview</b>"]
    bias = re.search(r"Positioning Bias[:\s]*(.+?)(?=\.)", analysis, re.I)
    if bias:
        lines.append(f"Positioning Bias: <b>{bias.group(1).strip()}</b>")
    for metric in ["ETF demand", "spot strength", "macro layout", "liquidity"]:
        m = re.search(rf"{metric}[^.]*?([\w\s/\-]+?)(?=[,;.])", analysis, re.I)
        if m:
            lines.append(f"• {metric.title()}: {m.group(1).strip()}")
    lines.append("")
    lines.append(conclusion[:300])
    return "\n".join(lines)

# ─── Weekly Formatting ───

def fmt_sector_rotation(data, dr):
    lines = ["<b>📈 Sector Rotation — RENDER (DePIN)</b>"]
    ms = dr.get("market_snapshot", {})
    if ms:
        lines.append(f"Price: <b>${ms.get('price','-')}</b> | MCap: {fval(ms.get('market_cap',0),'money')}")
        chg_24 = ms.get('change_24h', '')
        chg_7d = ms.get('change_7d', '')
        chg_30d = ms.get('change_30d', '')
        lines.append(f"24h: {chg_24}% | 7d: {chg_7d}% | 30d: {chg_30d}%")
    sec_snap = dr.get("sector_snapshot", {})
    if sec_snap:
        avg_chg = sec_snap.get("avg_price_change", "")
        count = sec_snap.get("count", sec_snap.get("tokens", ""))
        lines.append(f"Sector ({sec_snap.get('matched_category','?')}): avg {avg_chg}% ({count} tokens)")
    signal = dr.get("rotation_signal", data.get("rotation_signal", ""))
    if signal:
        lines.append(f"Signal: <b>{signal}</b>")
    s_mom = dr.get("sector_momentum", "")
    if s_mom:
        lines.append(f"Momentum: <b>{s_mom}</b>")
    extremes = dr.get("sector_extremes", {})
    if extremes:
        lines.append(f"Best: {extremes.get('best','-')} | Worst: {extremes.get('worst','-')}")
    summary = data.get("summary", "")
    if summary:
        lines.append("")
        lines.append(summary[:250])
    return "\n".join(lines)

def fmt_altcoin_scanner(data, dr):
    analysis = dr.get("analysis", data.get("analysis", ""))
    conclusion = dr.get("conclusion", data.get("summary", ""))
    lines = ["<b>🪙 Altcoin Perp Scanner</b>"]
    top_setup = re.search(r"#\d[:\s]*([\w]+)", analysis)
    if top_setup:
        rank_info = re.findall(r"#(\d)[\s:]*([\w]+)[^.]*?(?:anomaly[:\s]*([\d.]+))?", analysis)
        for rank, sym, anomaly in rank_info[:5]:
            lines.append(f"• #{rank} <b>{sym}</b>" + (f" — anomalia: {anomaly}" if anomaly else ""))
    else:
        m_queue = re.findall(r"(?:review|priority)\s*(?:queue|candidate)[^:]*:[:\s]*([\w, ]+)", analysis, re.I)
        if m_queue:
            symbols = [s.strip() for s in m_queue[0].split(",")]
            lines.append(f"Queue: {', '.join(symbols[:5])}")
    funding_str = re.search(r"funding.*?([-\d.]+%)", analysis)
    if funding_str:
        lines.append(f"Funding: {funding_str.group(1)}")
    lines.append("")
    if conclusion:
        lines.append(conclusion[:300])
    return "\n".join(lines)

def fmt_macro_financial(data, dr):
    analysis = dr.get("analysis", data.get("analysis", ""))
    conclusion = dr.get("conclusion", data.get("summary", ""))
    lines = ["<b>🏛️ Macro Financial Conditions</b>"]
    metrics_found = {}
    patterns = [
        ("NFCI", r"NFCI[^0-9.-]*?([-\d.]+)"),
        ("2s10s", r"(?:2s10s|2Y.*10Y|2Y/10Y)[^-\d]*?([-\d.]+%?)"),
        ("10Y Real", r"10[Yy].*real[^0-9.]*?([\d.]+%)"),
        ("CPI", r"CPI[^0-9.]*?([\d.]+%)"),
        ("Core CPI", r"(?:core\s+)?CPI[^0-9.]*?([\d.]+%)"),
        ("Unemployment", r"(?:unemployment|U/E)[^0-9.]*?([\d.]+%)"),
        ("Fed Funds", r"(?:fed\s+funds|federal\s+funds)[^0-9.]*?([\d.]+%)"),
        ("Front-End Δ", r"(?:front.end|front\s+end)[^0-9.]*?([-\d.]+%?)"),
    ]
    for label, pat in patterns:
        m = re.search(pat, analysis, re.I)
        if m:
            metrics_found[label] = m.group(1)
    for k, v in metrics_found.items():
        is_red = ("-0" in v.replace("bps","") if k in ("2s10s",) else False)
        lines.append(f"{k}: <b>{v}</b>" + (" ⚠️ inverted" if k == "2s10s" and "-" in v else ""))
    lines.append("")
    if conclusion:
        lines.append(conclusion[:250])
    return "\n".join(lines)

def fmt_liquidity(data, dr):
    lines = ["<b>💧 Liquidity Risk Regime</b>"]
    rprt = dr if "indicator_snapshot" in dr else data.get("report", dr)
    rprt = rprt if "indicator_snapshot" in rprt else dr
    ind_snap = rprt.get("indicator_snapshot", data.get("indicator_snapshot", {}))
    lines.append(f"Risk Level: <b>{rprt.get('risk_level','-')}</b>")
    lines.append(f"Carry Risk: <b>{rprt.get('carry_trade_risk','-')}</b>")
    if ind_snap:
        net_liq = ind_snap.get("net_liquidity", ind_snap.get("net_liquidity_usd", ""))
        if net_liq:
            nl = net_liq.replace("$", "")
            lines.append(f"Net Liquidity: <b>${float(nl):.2f}T</b>" if nl and nl.replace(".","").isdigit() else f"net Liquidity: {net_liq}")
        wo_w = ind_snap.get("weekly_change_pct", "")
        if wo_w:
            lines.append(f"Weekly Δ: {wo_w}%")
        on_fund = ind_snap.get("overnight_funding_rate", "")
        if on_fund:
            lines.append(f"ON Funding: {on_fund}")
        usdjpy = ind_snap.get("usd_jpy", "")
        if usdjpy:
            lines.append(f"USD/JPY: {usdjpy}")
    summary = data.get("summary", "")
    if summary:
        lines.append("")
        lines.append(summary[:300])
    elif dr.get("conclusion", ""):
        lines.append("")
        lines.append(dr["conclusion"][:300])
    return "\n".join(lines)

def fmt_holder_distribution(data, dr):
    rprt = dr if "holder_count" in dr else data.get("report", dr)
    rprt = rprt if "holder_count" in rprt else dr
    lines = ["<b>👥 Holder Distribution (AAVE)</b>"]
    lines.append(f"State: <b>{rprt.get('distribution_state','-')}</b>")
    lines.append(f"Holders: <b>{rprt.get('holder_count',0):,}</b>")
    tm = rprt.get("trend_metrics", {})
    if tm:
        hg = tm.get("holder_growth_pct")
        if hg is not None: lines.append(f"Holder Growth: {hg}%")
        t50 = tm.get("top_50_balance_growth_pct")
        if t50 is not None: lines.append(f"Top 50 Growth: {t50}%")
        t100 = tm.get("top_100_balance_growth_pct")
        if t100 is not None: lines.append(f"Top 100 Growth: {t100}%")
    snap = rprt.get("latest_snapshot", {})
    if snap:
        top10 = snap.get("top_10_holder_share_pct")
        if top10 is not None: lines.append(f"Top 10 Share: <b>{top10:.2f}%</b>")
        t50b = snap.get("top_50_balance")
        if t50b is not None: lines.append(f"Top 50 Balance: {t50b*100:.2f}%")
        t100b = snap.get("top_100_balance")
        if t100b is not None: lines.append(f"Top 100 Balance: {t100b*100:.2f}%")
    summary = data.get("summary", "")
    if summary:
        lines.append("")
        lines.append(summary[:250])
    return "\n".join(lines)

def fmt_protocol_revenue(data, dr):
    rprt = dr if "current_tvl_usd" in dr else data.get("report", dr)
    rprt = rprt if "current_tvl_usd" in rprt else dr
    lines = ["<b>⚡ Uniswap Revenue/TVL</b>"]
    lines.append(f"State: <b>{rprt.get('divergence_state','-')}</b>")
    tvl = rprt.get("current_tvl_usd", 0)
    if tvl:
        lines.append(f"TVL: <b>{fval(tvl, 'money')}</b>")
    tvl_chg = rprt.get("tvl_change_pct_recent_window", rprt.get("tvl_change_pct", ""))
    if tvl_chg:
        lines.append(f"TVL Δ (30d): {tvl_chg}%")
    rev_30d = rprt.get("revenue_30d_usd", 0)
    lines.append(f"Revenue (30d): <b>{fval(rev_30d, 'money')}</b>")
    rev_7d = rprt.get("revenue_7d_usd", 0)
    if rev_7d: lines.append(f"Revenue (7d): {fval(rev_7d, 'money')}")
    fees_30d = rprt.get("fees_30d_usd", 0)
    lines.append(f"Fees (30d): <b>{fval(fees_30d, 'money')}</b>")
    rrr = rprt.get("revenue_run_rate_ratio", "")
    if rrr: lines.append(f"Rev Run Rate Ratio: {rrr}")
    summary = data.get("summary", "")
    if summary:
        lines.append("")
        lines.append(summary[:250])
    return "\n".join(lines)

def fmt_defi_screen(data, dr):
    rprt = dr if "top_protocols" in dr else data.get("report", dr)
    rprt = rprt if "top_protocols" in rprt else dr
    lines = ["<b>🔗 DeFi Protocol Screen</b>"]
    lines.append(f"Screened: <b>{rprt.get('screened_count','?')}</b> | Cash-flowing: <b>{rprt.get('cash_flowing_count','?')}</b>")
    tops = rprt.get("top_protocols", [])
    for p in tops[:3]:
        name = p.get("name", "?")
        cat = p.get("category", "")
        tvl = fval(p.get("tvl_usd", 0), "money")
        rev = fval(p.get("revenue_30d_usd", 0), "money")
        fees = fval(p.get("fees_30d_usd", 0), "money")
        eff = p.get("revenue_to_tvl_bps_30d", "")
        lines.append(f"• <b>{name}</b> ({cat}) — TVL {tvl} | Rev {rev} | Fees {fees} | Eff: {eff}bps")
    summary = data.get("summary", "")
    if summary:
        lines.append("")
        lines.append(summary[:250])
    return "\n".join(lines)

def fmt_oracle_expansion(data, dr):
    rprt = dr if "expansion_state" in dr else data.get("report", dr)
    rprt = rprt if "expansion_state" in rprt else dr
    lines = ["<b>⛓️ Oracle Chain Expansion</b>"]
    lines.append(f"Chain: <b>Ethereum</b> | State: <b>{rprt.get('expansion_state','-')}</b>")
    sv = rprt.get("latest_secured_value", rprt.get("oracle_secured_value", 0))
    if sv: lines.append(f"Secured Value: <b>{fval(sv, 'money')}</b>")
    gp = rprt.get("growth_pct", "")
    if gp: lines.append(f"Growth (90 obs): <b>{gp}%</b>")
    sp = rprt.get("chain_share_pct", "")
    sdel = rprt.get("share_delta_pct", "")
    if sp:
        sd = f" (Δ{sdel}% vs prior)" if sdel else ""
        lines.append(f"Chain Share: {sp}%{sd}")
    rank = rprt.get("chain_rank", "")
    if rank: lines.append(f"Rank: #{rank}")
    chains = rprt.get("leading_chain_snapshot", [])
    if chains:
        parts = []
        for c in chains:
            if isinstance(c, dict):
                parts.append(f"{c.get('chain',c.get('name','?'))}: {fval(c.get('secured_value',c.get('value',0)),'money')}")
            elif isinstance(c, str) and ":" in c:
                parts.append(c)
            elif isinstance(c, str):
                parts.append(c)
        if parts:
            lines.append(f"Leading chains: {', '.join(parts[:5])}")
    summary = data.get("summary", "")
    if summary:
        lines.append("")
        lines.append(summary[:250])
    return "\n".join(lines)

# ─── Report Builder ───

FMT_LOOKUP = {
    "Market Overview": fmt_market_overview,
    "BTC Perp Analysis": fmt_btc_perp,
    "BTC ETF Demand": fmt_etf_demand,
    "Cross-Asset Correlation": fmt_cross_asset,
    "Macro News": fmt_macro_news,
    "Crypto Macro Overview": fmt_crypto_macro,
    "Sector Rotation": fmt_sector_rotation,
    "Altcoin Perp Scanner": fmt_altcoin_scanner,
    "Macro Financial Conditions": fmt_macro_financial,
    "Liquidity Risk Regime": fmt_liquidity,
    "Holder Distribution": fmt_holder_distribution,
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
    header = f"{title}\n{now_ist()}\n{'─'*40}\n\n"
    body_parts = []
    for s in skills:
        label = s["label"]
        raw = raw_results.get(label)
        if raw is None:
            body_parts.append(f"<b>{label}</b>\n⚠️ Data unavailable\n")
            continue
        data, dr = parse_output(raw)
        fmt_fn = FMT_LOOKUP.get(label)
        if fmt_fn:
            section = fmt_fn(data, dr)
        else:
            section = f"<b>{label}</b>\n{dr.get('conclusion', data.get('summary',''))[:200]}"
        body_parts.append(section)
    return header + "\n\n".join(body_parts)

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
    parser.add_argument("--force", action="store_true", help="Force re-run all skills")
    args = parser.parse_args()
    if not args.daily and not args.weekly:
        parser.print_help()
        sys.exit(1)
    if args.daily:
        print("=== Crypto Intelligence Daily Brief ===")
        print(f"Running {len(DAILY_SKILLS)} daily skills...")
        raw = run_skills(DAILY_SKILLS)
        print("Building daily report...")
        report = build_report("daily", raw)
        print(f"Report size: {len(report)} chars")
        print("Sending to Telegram...")
        n = send_report(report)
        print(f"Sent in {n} message(s).")
    if args.weekly:
        print("\n=== Crypto Intelligence Weekly Report ===")
        print(f"Running {len(WEEKLY_SKILLS)} weekly skills...")
        raw = run_skills(WEEKLY_SKILLS)
        print("Building weekly report...")
        report = build_report("weekly", raw)
        print(f"Report size: {len(report)} chars")
        print("Sending to Telegram...")
        n = send_report(report)
        print(f"Sent in {n} message(s).")

if __name__ == "__main__":
    main()
