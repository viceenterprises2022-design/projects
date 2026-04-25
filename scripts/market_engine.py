#!/usr/bin/env python3
"""
AlphaEdge Daily Market Snippet Engine v2
NSE/BSE  → Upstox (direct exchange feed)
Others   → Yahoo Finance / CoinGecko
AI       → Claude batch (1 API call for all 11 instruments)
Output   → 13 Telegram messages to @dvr_market_snippet
Cron     → 7:00 AM IST daily (1:30 AM UTC)
"""

import sys
import json
import time
import logging
import requests
from datetime import datetime
from typing import Optional
import pytz

# ──────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────
ANTHROPIC_API_KEY  = "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"
TELEGRAM_BOT_TOKEN = "8777670827:AAFJpLDZCHLrnAOV4ygA1AqTXGubE9H22RI"
TELEGRAM_CHANNEL   = "@dvr_market_snippet"
CLAUDE_MODEL       = "claude-sonnet-4-20250514"

# Upstox — direct NSE/BSE exchange feed
UPSTOX_TOKEN = (
    "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ"
    ".eyJzdWIiOiJGVzY0MDYiLCJqdGkiOiI2OWVjZDE1NTU0ZTdlMzBhNmY0NTZkODYiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaXNFeHRlbmRlZCI6dHJ1ZSwiaWF0IjoxNzc3MTI3NzY1LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE4MDg2OTA0MDB9"
    ".lxl6fYYoKH1_2AItX-XN40eNsYhbAzbjnwbvyopgSUo"
)

IST = pytz.timezone("Asia/Kolkata")

import os
import subprocess
import tempfile
os.makedirs("/home/claude/market_snippets/logs", exist_ok=True)

BELT_BIN = os.path.expanduser("~/.local/bin/belt")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/home/claude/market_snippets/logs/market_engine.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# INSTRUMENT DEFINITIONS
# ──────────────────────────────────────────────
INSTRUMENTS = [
    # Indian indices — Upstox (direct exchange)
    {"id": "NSE",    "name": "NIFTY 50",     "upstox": "NSE_INDEX|Nifty 50",  "type": "index",     "currency": "INR", "emoji": "🇮🇳"},
    {"id": "BSE",    "name": "SENSEX",        "upstox": "BSE_INDEX|SENSEX",    "type": "index",     "currency": "INR", "emoji": "🇮🇳"},
    # Global indices — Yahoo Finance
    {"id": "US30",   "name": "Dow Jones",     "yahoo": "^DJI",                 "type": "index",     "currency": "USD", "emoji": "🇺🇸"},
    {"id": "USTEC",  "name": "NASDAQ 100",    "yahoo": "^NDX",                 "type": "index",     "currency": "USD", "emoji": "🇺🇸"},
    # Commodities — Yahoo Finance
    {"id": "USOIL",  "name": "WTI Crude Oil", "yahoo": "CL=F",                 "type": "commodity", "currency": "USD", "emoji": "🛢️"},
    {"id": "GOLD",   "name": "Gold",          "yahoo": "GC=F",                 "type": "commodity", "currency": "USD", "emoji": "🥇"},
    {"id": "SILVER", "name": "Silver",        "yahoo": "SI=F",                 "type": "commodity", "currency": "USD", "emoji": "🥈"},
    # Crypto — CoinGecko (single batch call)
    {"id": "BTC",    "name": "Bitcoin",       "coingecko": "bitcoin",          "type": "crypto",    "currency": "USD", "emoji": "₿"},
    {"id": "ETH",    "name": "Ethereum",      "coingecko": "ethereum",         "type": "crypto",    "currency": "USD", "emoji": "Ξ"},
    {"id": "XRP",    "name": "XRP",           "coingecko": "ripple",           "type": "crypto",    "currency": "USD", "emoji": "◈"},
    {"id": "SOL",    "name": "Solana",        "coingecko": "solana",           "type": "crypto",    "currency": "USD", "emoji": "◎"},
]

# ──────────────────────────────────────────────
# STEP 1: PRICE FETCHING
# ──────────────────────────────────────────────

def fetch_upstox_batch(instrument_keys: list) -> dict:
    """
    Fetch NSE/BSE indices from Upstox in a single API call.
    Returns dict keyed by upstox instrument_key.
    """
    keys_param = ",".join(instrument_keys)
    url = "https://api.upstox.com/v2/market-quote/quotes"
    headers = {
        "Authorization": f"Bearer {UPSTOX_TOKEN}",
        "Accept": "application/json",
    }
    params = {"instrument_key": keys_param}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "success":
            log.warning(f"Upstox returned non-success: {data}")
            return {}

        result = {}
        for key, quote in data["data"].items():
            ohlc       = quote.get("ohlc", {})
            last_price = quote.get("last_price", 0)
            prev_close = ohlc.get("close", last_price)
            change     = quote.get("net_change", last_price - prev_close)
            change_pct = (change / prev_close * 100) if prev_close else 0

            result[key] = {
                "price":      last_price,
                "open":       ohlc.get("open", last_price),
                "high":       ohlc.get("high", last_price),
                "low":        ohlc.get("low", last_price),
                "prev_close": prev_close,
                "change":     change,
                "change_pct": change_pct,
                "closes_5d":  [prev_close, last_price],
                "highs_5d":   [ohlc.get("high", last_price)],
                "lows_5d":    [ohlc.get("low", last_price)],
                "volume":     quote.get("volume"),
                "source":     "Upstox",
            }
        return result
    except Exception as e:
        log.warning(f"Upstox batch fetch failed: {e}")
        return {}


def fetch_yahoo_quote(symbol: str) -> Optional[dict]:
    """Fetch OHLCV + previous close from Yahoo Finance v8 API."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    headers = {"User-Agent": "Mozilla/5.0"}
    params = {"interval": "1d", "range": "5d"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        data   = r.json()
        result = data["chart"]["result"][0]
        meta   = result["meta"]
        q      = result["indicators"]["quote"][0]

        closes = [c for c in q.get("close", []) if c is not None]
        highs  = [h for h in q.get("high",  []) if h is not None]
        lows   = [l for l in q.get("low",   []) if l is not None]
        opens  = [o for o in q.get("open",  []) if o is not None]

        if len(closes) < 2:
            return None

        prev_close = closes[-2]
        curr_close = meta.get("regularMarketPrice") or closes[-1]
        day_high   = meta.get("regularMarketDayHigh") or highs[-1]
        day_low    = meta.get("regularMarketDayLow")  or lows[-1]
        day_open   = opens[-1] if opens else prev_close
        change     = curr_close - prev_close
        change_pct = (change / prev_close) * 100

        return {
            "price":      curr_close,
            "open":       day_open,
            "high":       day_high,
            "low":        day_low,
            "prev_close": prev_close,
            "change":     change,
            "change_pct": change_pct,
            "closes_5d":  closes[-5:],
            "highs_5d":   highs[-5:],
            "lows_5d":    lows[-5:],
            "source":     "Yahoo Finance",
        }
    except Exception as e:
        log.warning(f"Yahoo fetch failed for {symbol}: {e}")
        return None


def fetch_coingecko_batch(coin_ids: list) -> dict:
    """Fetch all crypto in a single CoinGecko call."""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ",".join(coin_ids),
        "order": "market_cap_desc",
        "sparkline": "false",
        "price_change_percentage": "24h",
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        result = {}
        for coin in r.json():
            cid   = coin["id"]
            price = coin.get("current_price", 0)
            pct   = coin.get("price_change_percentage_24h", 0)
            prev  = price / (1 + pct / 100) if price and pct else price
            result[cid] = {
                "price":      price,
                "open":       prev,
                "high":       coin.get("high_24h", price),
                "low":        coin.get("low_24h",  price),
                "prev_close": prev,
                "change":     coin.get("price_change_24h", 0),
                "change_pct": pct,
                "market_cap": coin.get("market_cap", 0),
                "volume":     coin.get("total_volume", 0),
                "closes_5d":  [prev, price],
                "highs_5d":   [coin.get("high_24h", price)],
                "lows_5d":    [coin.get("low_24h",  price)],
                "source":     "CoinGecko",
            }
        return result
    except Exception as e:
        log.warning(f"CoinGecko batch fetch failed: {e}")
        return {}


# ──────────────────────────────────────────────
# STEP 2: TECHNICAL CALCULATIONS
# ──────────────────────────────────────────────

def calc_pivot_points(high: float, low: float, close: float) -> dict:
    pp = (high + low + close) / 3
    return {
        "PP": pp,
        "R1": (2 * pp) - low,
        "R2": pp + (high - low),
        "S1": (2 * pp) - high,
        "S2": pp - (high - low),
    }


def calc_rsi(closes: list, period: int = 14) -> Optional[float]:
    if len(closes) < period + 1:
        return None
    gains  = [max(closes[i] - closes[i-1], 0) for i in range(1, len(closes))]
    losses = [max(closes[i-1] - closes[i], 0) for i in range(1, len(closes))]
    avg_g  = sum(gains[-period:])  / period
    avg_l  = sum(losses[-period:]) / period
    if avg_l == 0:
        return 100.0
    return 100 - (100 / (1 + avg_g / avg_l))


def determine_trend(price: float, pp: float, r1: float, s1: float) -> str:
    if price > r1:   return "Strong Bullish"
    elif price > pp: return "Bullish"
    elif price < s1: return "Strong Bearish"
    elif price < pp: return "Bearish"
    else:            return "Neutral"


def format_price(price: float, instrument_id: str) -> str:
    if instrument_id in ("NSE", "BSE"):
        return f"{price:,.2f}"
    elif instrument_id == "BTC":
        return f"{price:,.0f}"
    elif price >= 1000:
        return f"{price:,.2f}"
    elif price >= 1:
        return f"{price:.4f}"
    else:
        return f"{price:.6f}"


def enrich_instrument(inst: dict, raw: dict) -> dict:
    price  = raw["price"]
    high   = raw["high"]
    low    = raw["low"]
    prev   = raw["prev_close"]

    pivots = calc_pivot_points(high, low, prev)
    rsi    = calc_rsi(raw.get("closes_5d", [prev, price]))
    trend  = determine_trend(price, pivots["PP"], pivots["R1"], pivots["S1"])

    score = 50
    if raw["change_pct"] > 1:    score += 20
    elif raw["change_pct"] > 0:  score += 10
    elif raw["change_pct"] < -1: score -= 20
    else:                         score -= 10
    if price > pivots["PP"]:     score += 10
    if rsi:
        if rsi > 60: score += 10
        elif rsi < 40: score -= 10
    score = max(0, min(100, score))

    return {
        **inst,
        **raw,
        "pivots":          pivots,
        "rsi":             rsi,
        "trend":           trend,
        "above_pivot":     price > pivots["PP"],
        "sentiment_score": score,
        "price_fmt":       format_price(price, inst["id"]),
        "change_sign":     "+" if raw["change"] >= 0 else "",
    }


# ──────────────────────────────────────────────
# STEP 3: AI BATCH ANALYSIS — 1 API CALL
# ──────────────────────────────────────────────

def build_batch_prompt(instruments_data: list) -> str:
    lines = []
    for d in instruments_data:
        pv = d["pivots"]
        fp = lambda x: format_price(x, d["id"])
        line = (
            f"{d['id']} ({d['name']}): Price={d['price_fmt']} {d['currency']}, "
            f"Change={d['change_sign']}{d['change_pct']:.2f}%, "
            f"Open={fp(d['open'])}, High={fp(d['high'])}, Low={fp(d['low'])}, "
            f"Pivot={fp(pv['PP'])}, R1={fp(pv['R1'])}, R2={fp(pv['R2'])}, "
            f"S1={fp(pv['S1'])}, S2={fp(pv['S2'])}, "
            f"Trend={d['trend']}, Sentiment={d['sentiment_score']}/100"
            + (f", RSI={d['rsi']:.1f}" if d.get("rsi") else "")
            + (f", Source={d.get('source','')}")
        )
        lines.append(line)

    return f"""You are a professional market analyst. Analyze the following {len(instruments_data)} instruments and return ONLY a valid JSON array (no markdown, no preamble, no explanation).

MARKET DATA:
{chr(10).join(lines)}

For EACH instrument return an object with EXACTLY these fields:
- "id": instrument ID string (e.g. "NSE")
- "bias": one of "Strongly Bullish" | "Bullish" | "Neutral" | "Bearish" | "Strongly Bearish"
- "summary": 1 sharp sentence about today's price action (max 15 words)
- "key_level": the single most critical price level to watch (number as string, no currency symbol)
- "key_level_label": "Resistance" | "Support" | "Pivot"
- "outlook": 1 forward-looking sentence for next session (max 20 words)
- "risk_note": 1 short risk or caution note (max 12 words)

Respond ONLY with the JSON array."""


def call_claude_batch(instruments_data: list) -> dict:
    """One Claude API call for ALL instruments. Returns dict keyed by id."""
    headers = {
        "x-api-key":         ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type":      "application/json",
    }
    payload = {
        "model":      CLAUDE_MODEL,
        "max_tokens": 2000,
        "messages":   [{"role": "user", "content": build_batch_prompt(instruments_data)}],
    }
    log.info(f"Calling Claude API — batch of {len(instruments_data)} instruments...")
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers, json=payload, timeout=60,
    )
    r.raise_for_status()
    raw = r.json()["content"][0]["text"].strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    analyses = json.loads(raw)
    return {a["id"]: a for a in analyses}


# ──────────────────────────────────────────────
# STEP 4: SNIPPET BUILDER
# ──────────────────────────────────────────────

BIAS_EMOJI = {
    "Strongly Bullish": "🚀",
    "Bullish":          "📈",
    "Neutral":          "⚖️",
    "Bearish":          "📉",
    "Strongly Bearish": "🔻",
}

def get_sentiment_bar(score: int) -> str:
    if score >= 80:   return "🟢🟢🟢🟢🟢"
    elif score >= 65: return "🟢🟢🟢🟢⬜"
    elif score >= 50: return "🟢🟢🟢⬜⬜"
    elif score >= 35: return "🔴🔴⬜⬜⬜"
    elif score >= 20: return "🔴🔴🔴🔴⬜"
    else:             return "🔴🔴🔴🔴🔴"


def build_snippet(d: dict, ai: dict) -> str:
    now_ist   = datetime.now(IST).strftime("%B %d, %Y • %I:%M %p IST")
    bias      = ai.get("bias", d["trend"])
    bias_icon = BIAS_EMOJI.get(bias, "➡️")
    chg_icon  = "🔺" if d["change"] >= 0 else "🔻"
    sent_bar  = get_sentiment_bar(d["sentiment_score"])
    pp_icon   = "✅" if d["above_pivot"] else "❌"
    change_str = f"{d['change_sign']}{d['change_pct']:.2f}%"
    pv = d["pivots"]
    fp = lambda x: format_price(x, d["id"])
    rsi_line = f"📊 RSI: `{d['rsi']:.1f}`\n" if d.get("rsi") else ""
    src_line = f"🔗 Source: _{d.get('source', 'Market Data')}_\n" if d.get("source") else ""

    return f"""{d['emoji']} *{d['name']} — Daily Snapshot*
🗓 _{now_ist}_
━━━━━━━━━━━━━━━━━━━━

💰 *Price:* `{d['price_fmt']}` {d['currency']}
{chg_icon} *Change:* `{change_str}`  |  📂 Open: `{fp(d['open'])}`
📈 High: `{fp(d['high'])}`   📉 Low: `{fp(d['low'])}`
{src_line}
━━━━━━━━━━━━━━━━━━━━
📐 *Pivot Levels*

🔴 R2: `{fp(pv['R2'])}`
🟠 R1: `{fp(pv['R1'])}`
🟡 PP: `{fp(pv['PP'])}` {pp_icon} {'Above' if d['above_pivot'] else 'Below'}
🟢 S1: `{fp(pv['S1'])}`
🔵 S2: `{fp(pv['S2'])}`
{rsi_line}
━━━━━━━━━━━━━━━━━━━━
🎯 *AI Market Analysis*

{sent_bar} `{d['sentiment_score']}/100`
{bias_icon} *{bias}*

📝 _{ai.get('summary', '—')}_

🔑 *Watch:* `{ai.get('key_level', '—')}` {d['currency']} _{ai.get('key_level_label','')}_
🔭 *Outlook:* {ai.get('outlook', '—')}
⚠️ *Risk:* _{ai.get('risk_note', '—')}_

━━━━━━━━━━━━━━━━━━━━
_AlphaEdge • Financial Intelligence_"""


# ──────────────────────────────────────────────
# STEP 5: GEMINI IMAGE GENERATION
# ──────────────────────────────────────────────

def build_image_prompt(enriched: list, ai_results: dict, date_str: str) -> str:
    bullish = [d for d in enriched if ai_results.get(d["id"], {}).get("bias", "").lower() in ("bullish", "strongly bullish")]
    bearish = [d for d in enriched if ai_results.get(d["id"], {}).get("bias", "").lower() in ("bearish", "strongly bearish")]
    neutral = [d for d in enriched if d not in bullish and d not in bearish]

    btc = next((d for d in enriched if d["id"] == "BTC"), None)
    nse = next((d for d in enriched if d["id"] == "NSE"), None)
    gold = next((d for d in enriched if d["id"] == "GOLD"), None)

    mood = "optimistic green" if len(bullish) > len(bearish) else ("gloomy red" if len(bearish) > len(bullish) else "balanced neutral gold")
    btc_str = f"Bitcoin at ${btc['price_fmt']}" if btc else ""
    nse_str = f"NIFTY 50 at {nse['price_fmt']}" if nse else ""
    gold_str = f"Gold at ${gold['price_fmt']}" if gold else ""

    highlights = ", ".join([btc_str, nse_str, gold_str])

    return (
        f"Create a stunning financial market dashboard visualization for {date_str}. "
        f"Style: dark luxury Bloomberg terminal aesthetic, deep navy background with glowing {mood} accents. "
        f"Show a professional market summary panel with: {highlights}. "
        f"{len(bullish)} of 11 markets bullish, {len(bearish)} bearish. "
        f"Include flowing data streams, candlestick chart silhouettes, and holographic price tickers. "
        f"Bottom text: 'AlphaEdge Daily Market Intelligence'. "
        f"Ultra-detailed, cinematic lighting, 4K quality, no text errors."
    )


def generate_market_image(enriched: list, ai_results: dict, date_str: str) -> str | None:
    prompt = build_image_prompt(enriched, ai_results, date_str)
    log.info(f"Generating market image via Gemini... prompt: {prompt[:80]}...")
    try:
        import json as _json
        result = subprocess.run(
            [BELT_BIN, "app", "run", "google/gemini-2-5-flash-image",
             "--input", _json.dumps({"prompt": prompt, "aspect_ratio": "16:9"})],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            log.error(f"belt failed: {result.stderr[:300]}")
            return None
        # belt outputs JSON with image URL
        output = result.stdout.strip()
        data = _json.loads(output)
        # Extract image URL from belt response
        images = data.get("images") or data.get("output") or []
        if isinstance(images, list) and images:
            url = images[0].get("url") or images[0]
        elif isinstance(data, dict):
            url = data.get("url") or data.get("image_url")
        else:
            url = None
        if url:
            log.info(f"  ✓ Image generated: {url}")
        else:
            log.warning(f"  ⚠ Could not parse image URL from: {output[:200]}")
        return url
    except subprocess.TimeoutExpired:
        log.error("belt timed out after 120s")
        return None
    except Exception as e:
        log.error(f"Image generation failed: {e}")
        return None


def send_telegram_photo(image_url: str, caption: str, chat_id: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        r = requests.post(url, json={
            "chat_id": chat_id,
            "photo": image_url,
            "caption": caption,
            "parse_mode": "Markdown",
        }, timeout=30)
        if r.status_code == 200:
            return True
        log.error(f"Telegram photo {r.status_code}: {r.text[:200]}")
        return False
    except Exception as e:
        log.error(f"Telegram photo send failed: {e}")
        return False


# ──────────────────────────────────────────────
# STEP 6: TELEGRAM SENDER
# ──────────────────────────────────────────────

def send_telegram(text: str, chat_id: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id":    chat_id,
            "text":       text,
            "parse_mode": "Markdown",
        }, timeout=15)
        if r.status_code == 200:
            return True
        log.error(f"Telegram {r.status_code}: {r.text[:200]}")
        return False
    except Exception as e:
        log.error(f"Telegram send failed: {e}")
        return False


# ──────────────────────────────────────────────
# MAIN ORCHESTRATOR
# ──────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("AlphaEdge Daily Market Engine v2 — Starting")
    log.info("=" * 60)

    now_ist  = datetime.now(IST)
    date_str = now_ist.strftime("%A, %B %d, %Y")
    enriched = []
    failed   = []

    # ── 1a. Upstox — NSE & BSE (single batch call) ──
    upstox_instruments = [i for i in INSTRUMENTS if "upstox" in i]
    upstox_keys = [i["upstox"] for i in upstox_instruments]
    log.info(f"Fetching {len(upstox_instruments)} Indian indices from Upstox...")
    upstox_data = fetch_upstox_batch(upstox_keys)

    for inst in upstox_instruments:
        key = inst["upstox"]
        # Upstox returns key with colon separator in response
        resp_key = key.replace("|", ":")
        raw = upstox_data.get(resp_key) or upstox_data.get(key)
        if raw:
            enriched.append(enrich_instrument(inst, raw))
            log.info(f"  ✓ {inst['id']} [Upstox]: {raw['price']:,.2f} ({raw['change_pct']:+.2f}%)")
        else:
            # Fallback to Yahoo Finance
            log.warning(f"  ⚠ {inst['id']} Upstox failed — falling back to Yahoo Finance")
            yahoo_sym = {"NSE": "^NSEI", "BSE": "^BSESN"}.get(inst["id"])
            if yahoo_sym:
                raw = fetch_yahoo_quote(yahoo_sym)
                if raw:
                    raw["source"] = "Yahoo Finance (fallback)"
                    enriched.append(enrich_instrument(inst, raw))
                    log.info(f"  ✓ {inst['id']} [Yahoo fallback]: {raw['price']:,.2f}")
                else:
                    failed.append(inst["id"])
            else:
                failed.append(inst["id"])
        time.sleep(0.3)

    # ── 1b. Yahoo Finance — global indices + commodities ──
    yahoo_instruments = [i for i in INSTRUMENTS if "yahoo" in i]
    log.info(f"Fetching {len(yahoo_instruments)} instruments from Yahoo Finance...")
    for inst in yahoo_instruments:
        raw = fetch_yahoo_quote(inst["yahoo"])
        if raw:
            enriched.append(enrich_instrument(inst, raw))
            log.info(f"  ✓ {inst['id']}: {raw['price']:.2f} ({raw['change_pct']:+.2f}%)")
        else:
            failed.append(inst["id"])
            log.warning(f"  ✗ {inst['id']}: fetch failed")
        time.sleep(0.5)

    # ── 1c. CoinGecko — all crypto in one call ──
    crypto_instruments = [i for i in INSTRUMENTS if "coingecko" in i]
    coin_ids = [i["coingecko"] for i in crypto_instruments]
    log.info(f"Fetching {len(crypto_instruments)} crypto from CoinGecko (1 batch call)...")
    crypto_data = fetch_coingecko_batch(coin_ids)
    for inst in crypto_instruments:
        raw = crypto_data.get(inst["coingecko"])
        if raw:
            enriched.append(enrich_instrument(inst, raw))
            log.info(f"  ✓ {inst['id']}: {raw['price']:.4f} ({raw['change_pct']:+.2f}%)")
        else:
            failed.append(inst["id"])
            log.warning(f"  ✗ {inst['id']}: fetch failed")

    log.info(f"Fetched {len(enriched)}/{len(INSTRUMENTS)} instruments successfully")
    if not enriched:
        log.error("No data fetched. Aborting.")
        sys.exit(1)

    # ── 2. Claude batch AI analysis (1 API call) ──
    try:
        ai_results = call_claude_batch(enriched)
        log.info(f"  ✓ Claude analysis complete for {len(ai_results)} instruments")
    except Exception as e:
        log.error(f"Claude API failed: {e} — using local fallback")
        ai_results = {
            d["id"]: {
                "bias":            d["trend"],
                "summary":         f"{d['name']} at {d['price_fmt']} {d['currency']}.",
                "key_level":       format_price(d["pivots"]["PP"], d["id"]),
                "key_level_label": "Pivot",
                "outlook":         "Watch pivot levels for directional cues next session.",
                "risk_note":       "Confirm moves with volume before acting.",
            }
            for d in enriched
        }

    # ── 3. Send to Telegram ──
    log.info("Sending to Telegram @dvr_market_snippet...")

    # Header
    header = (
        f"📊 *AlphaEdge — Daily Market Intelligence*\n"
        f"🗓 _{date_str}_\n\n"
        f"Good morning! Today's snapshots across *11 instruments* — "
        f"NSE, BSE, Global Indices, Commodities & Crypto.\n\n"
        f"_Powered by AlphaEdge Financial Intelligence_ 🚀"
    )
    send_telegram(header, TELEGRAM_CHANNEL)
    time.sleep(2)

    # Snippets in original order
    enriched_map = {d["id"]: d for d in enriched}
    sent = 0

    for inst in INSTRUMENTS:
        iid = inst["id"]
        if iid not in enriched_map:
            log.warning(f"Skipping {iid} — no data available")
            continue
        d   = enriched_map[iid]
        ai  = ai_results.get(iid, {})
        msg = build_snippet(d, ai)
        if send_telegram(msg, TELEGRAM_CHANNEL):
            sent += 1
            log.info(f"  ✓ {iid} sent")
        else:
            log.error(f"  ✗ {iid} failed")
        time.sleep(2)

    # ── 4. Generate market image ──
    image_url = generate_market_image(enriched, ai_results, date_str)
    if image_url:
        caption = (
            f"📊 *AlphaEdge Daily Market Dashboard*\n"
            f"🗓 _{date_str}_\n"
            f"_Generated by Gemini AI • AlphaEdge_"
        )
        if send_telegram_photo(image_url, caption, TELEGRAM_CHANNEL):
            log.info("  ✓ Market image sent to Telegram")
        else:
            log.warning("  ⚠ Image generated but failed to send to Telegram")
    else:
        log.warning("  ⚠ Image generation skipped")

    # Footer
    footer = (
        f"✅ *Snapshot Complete*\n"
        f"`{sent}/{len(enriched)}` snippets delivered\n"
        f"⏱ {now_ist.strftime('%I:%M %p IST')}\n\n"
        f"_NSE/BSE data via Upstox • Crypto via CoinGecko • Analysis by Claude AI • Images by Gemini_\n"
        f"_AlphaEdge • alphaedge.ai_"
    )
    send_telegram(footer, TELEGRAM_CHANNEL)

    log.info(f"Done — {sent}/{len(enriched)} sent. Failed: {failed or 'none'}")


if __name__ == "__main__":
    main()
