import re
from typing import Dict, Any


_HISTORICAL_PATTERNS = re.compile(
    r"\b(?:history|historical|past|last.*day|last.*week|last.*month|all time|ath)",
    re.IGNORECASE,
)
_PRICE_PATTERNS = re.compile(
    r"\b(price|quote|worth|how much|rate|value|cost|trading at|ltp)\b", re.IGNORECASE
)
_TA_PATTERNS = re.compile(
    r"\b(ta|technical|rsi|macd|moving average|ema|sma|fibonacci|pivot|support|resistance|trend|indicator)\b",
    re.IGNORECASE,
)
_ONCHAIN_PATTERNS = re.compile(
    r"\b(onchain|on-chain|holder|circulat|supply|tx fee|transaction fee|active|whale)\b",
    re.IGNORECASE,
)
_NEWS_PATTERNS = re.compile(
    r"\b(news|headline|breaking|update on)\b", re.IGNORECASE
)
_GLOBAL_PATTERNS = re.compile(
    r"\b(global|market cap|total cap|dominance|fear|greed|overview|market state)\b",
    re.IGNORECASE,
)
_ETF_PATTERNS = re.compile(r"\b(etf|etf flow|spot etf|inflow|outflow)\b", re.IGNORECASE)
_LEVERAGE_PATTERNS = re.compile(
    r"\b(leverage|future|liquidation|funding|open interest|oi)\b", re.IGNORECASE
)
_TRENDING_PATTERNS = re.compile(
    r"\b(trending|narrative|hot|meme|sector|rotation)\b", re.IGNORECASE
)
_MARKET_REPORT_PATTERNS = re.compile(
    r"\b(market report|daily brief|morning brief|market overview|market summary)",
    re.IGNORECASE,
)
_DEEP_DIVE_PATTERNS = re.compile(
    r"\b(deep dive|deep-dive|fundamental analys|full research|should I (buy|sell)|do a full)",
    re.IGNORECASE,
)
_SEARCH_PATTERNS = re.compile(
    r"\b(search|find|look.?up|discover|tell me about)\b", re.IGNORECASE
)


def _classify_intent(query: str) -> str:
    q = query.lower()

    if _HISTORICAL_PATTERNS.search(q) and _PRICE_PATTERNS.search(q):
        return "historical"
    if _MARKET_REPORT_PATTERNS.search(q):
        return "market_report"
    if _DEEP_DIVE_PATTERNS.search(q):
        return "deep_dive"
    if _TA_PATTERNS.search(q):
        return "ta_analysis"
    if _ONCHAIN_PATTERNS.search(q):
        return "onchain"
    if _NEWS_PATTERNS.search(q):
        return "news"
    if _GLOBAL_PATTERNS.search(q):
        return "global_metrics"
    if _ETF_PATTERNS.search(q):
        return "etf_flows"
    if _LEVERAGE_PATTERNS.search(q):
        return "leverage"
    if _TRENDING_PATTERNS.search(q):
        return "trending"
    if _PRICE_PATTERNS.search(q):
        return "price_quote"
    if _SEARCH_PATTERNS.search(q):
        return "search"
    if _HISTORICAL_PATTERNS.search(q):
        return "historical"
    if "semantic" in q or "meaning" in q:
        return "semantic"
    if "skill" in q or "mcp" in q or "hub" in q:
        return "skill_hub"
    return "general"


async def plan_node(state: Dict[str, Any]) -> Dict[str, Any]:
    query = state.get("query", "")
    trace = list(state.get("reasoning_trace", []))
    intent = _classify_intent(query)
    trace.append(f"Plan: intent={intent} query='{query}'")
    return {"reasoning_trace": trace, "intent": intent}


async def act_node(state: Dict[str, Any]) -> Dict[str, Any]:
    intent = state.get("intent", "general")
    query = state.get("query", "")
    trace = list(state.get("reasoning_trace", []))
    tools_executed = list(state.get("tools_executed", []))
    trace.append(f"Act: resolving intent={intent}")

    if intent == "market_report":
        from agent.orchestrators import run_market_report
        output = await run_market_report(query)
        tools_executed.append({
            "tool_name": "market_report",
            "arguments": {"sub_tools": "global,leverage,etf,trending,news,BTC_TA,ETH_TA"},
            "result": output[:300],
        })
    elif intent == "deep_dive":
        from agent.orchestrators import run_crypto_research
        output = await run_crypto_research(query)
        tools_executed.append({
            "tool_name": "crypto_research",
            "arguments": {"sub_tools": "quotes,TA,onchain,history,news"},
            "result": output[:300],
        })
    elif intent == "skill_hub":
        from agent.tools.crypto_lookup import find_skill
        skills = await find_skill(query)
        tools_executed.append({
            "tool_name": "find_skill",
            "arguments": {"query": query},
            "result": str([s.get("uniqueName", "") for s in (skills or [])]),
        })
        output = f"Found skills: {[s.get('uniqueName', '') for s in (skills or [])]}"
    else:
        from agent.tools.cmc_mcp_tools import dispatch_cmc_mcp_tool
        tool_name, tool_args, formatted = await dispatch_cmc_mcp_tool(intent, query)
        tools_executed.append({
            "tool_name": tool_name,
            "arguments": tool_args,
            "result": formatted,
        })
        output = formatted

    trace.append(f"Act: completed tool={tools_executed[-1]['tool_name']}")
    return {"reasoning_trace": trace, "tools_executed": tools_executed, "output": output}


async def observe_node(state: Dict[str, Any]) -> Dict[str, Any]:
    trace = list(state.get("reasoning_trace", []))
    trace.append("Observe: execution audited, result ready")
    return {"reasoning_trace": trace, "finalized": True}
