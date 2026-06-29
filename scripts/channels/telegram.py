"""Telegram messaging — shared library for all scripts.

Import:
  from channels.telegram import send_text, send_file

Uses TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from environment.
"""
import os
import re

import requests

TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN",
    "8770565112:AAGy9q-BMWsgvU4RQUQDyeNXa282Vme9uG4",
)
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7246234100")


def detect_format(text):
    """Detect if text is HTML or Markdown."""
    has_markdown = False
    if re.search(r"^\s*(?:#+\s|\-\s|\*\s|\+\s|\d+\.\s|\|.*?\|)", text, re.M):
        has_markdown = True
    elif re.search(r"\*\*.*?\*\*|__.*?__|\[.*?\]\(.*?\)", text):
        has_markdown = True

    if has_markdown:
        return "markdown"
    if re.search(r"<[a-z/]+[^>]*>", text, re.I):
        return "html"
    return "html"


def is_raw_report(text):
    patterns = [
        r"✅\s*Header:",
        r"📰\s*News:",
        r"🌍\s*Macros:",
        r"📊\s*Crypto:",
        r"🧠\s*Market\s*Intel:",
        r"🎖️\s*Footer:"
    ]
    count = sum(1 for p in patterns if re.search(p, text, re.I))
    return count >= 3


def auto_format_content(text):
    pattern = r"(✅\s*Header:|📰\s*News:|🌍\s*Macros:|📊\s*Crypto:|🧠\s*Market\s*Intel:|🎖️\s*Footer:)"
    parts = re.split(pattern, text)
    formatted_blocks = []
    current_key = None
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if re.match(pattern, part):
            current_key = part
        else:
            formatted_blocks.append((current_key or "", part))

    output = []
    for key, content in formatted_blocks:
        key_clean = key.replace(":", "").strip()
        emoji_match = re.match(r"^([^\w\s\(\)]+)\s*(.*)$", key_clean)
        if emoji_match:
            emoji = emoji_match.group(1).strip()
            sec_name = emoji_match.group(2).strip()
        else:
            emoji = ""
            sec_name = key_clean

        sec_name_lower = sec_name.lower()

        if sec_name_lower == "header":
            output.append(f"# {emoji} {content}\n")
        elif sec_name_lower == "news":
            news_title = "News & Highlights"
            content_rest = content
            m_title = re.match(r"^(.*?)(?=\b1\.\s)", content)
            if m_title:
                news_title = m_title.group(1).strip()
                content_rest = content[m_title.end():].strip()
            output.append(f"## {emoji} {news_title}\n")
            item_pattern = r"(\b\d+\.\s|•\s*Why\s+it\s+matters:)"
            sub_parts = re.split(item_pattern, content_rest)
            curr_item_num = None
            curr_is_why = False
            for sp in sub_parts:
                sp = sp.strip()
                if not sp:
                    continue
                m_num = re.match(r"^(\d+)\.\s*$", sp)
                if m_num:
                    curr_item_num = m_num.group(1)
                    curr_is_why = False
                elif sp.startswith("•") and "why it matters" in sp.lower():
                    curr_is_why = True
                else:
                    if curr_item_num and not curr_is_why:
                        output.append(f"{curr_item_num}. **{sp}**")
                    elif curr_is_why:
                        output.append(f"   - *Why it matters:* {sp}\n")
        elif sec_name_lower == "macros":
            output.append(f"## {emoji} {sec_name}\n")
            table_rows = ["| Asset | Value | Details |", "|:---|---:|:---|"]
            macro_items = [item.strip() for item in content.split("•") if item.strip()]
            for item in macro_items:
                if ":" not in item:
                    continue
                m_macro = re.match(r"^([^:]+):\s*([^\(]+)(?:\((.*)\))?$", item)
                if m_macro:
                    asset = m_macro.group(1).strip()
                    val = m_macro.group(2).strip()
                    notes = m_macro.group(3).strip() if m_macro.group(3) else ""
                    table_rows.append(f"| **{asset}** | {val} | {notes} |")
                else:
                    table_rows.append(f"| {item} | | |")
            output.append("\n".join(table_rows))
            output.append("")
        elif sec_name_lower == "crypto":
            output.append(f"## {emoji} {sec_name}\n")
            table_rows = ["| Coin | Price | Change |", "|:---|---:|---:|"]
            crypto_items = [item.strip() for item in content.split("•") if item.strip()]
            for item in crypto_items:
                if ":" not in item:
                    continue
                m_crypto = re.match(r"^([^:]+):\s*([^\(]+)(?:\((.*)\))?$", item)
                if m_crypto:
                    coin = m_crypto.group(1).strip()
                    price = m_crypto.group(2).strip()
                    change = m_crypto.group(3).strip() if m_crypto.group(3) else ""
                    table_rows.append(f"| **{coin}** | {price} | {change} |")
                else:
                    table_rows.append(f"| {item} | | |")
            output.append("\n".join(table_rows))
            output.append("")
        elif sec_name_lower == "market intel":
            output.append(f"## {emoji} {sec_name}\n")
            table_rows = ["| Index | Spot | Signal | Details |", "|:---|---:|:---|:---|"]
            intel_items = [item.strip() for item in content.split("•") if item.strip()]
            for item in intel_items:
                if "|" not in item:
                    continue
                parts = [p.strip() for p in item.split("|")]
                if len(parts) >= 2:
                    first_part = parts[0]
                    sig = parts[1]
                    rest_details = " | ".join(parts[2:])
                    idx_name = first_part
                    spot_val = ""
                    if ": Spot " in first_part:
                        idx_name, spot_val = first_part.split(": Spot ", 1)
                    elif " Spot " in first_part:
                        idx_name, spot_val = first_part.split(" Spot ", 1)
                    table_rows.append(f"| **{idx_name}** | {spot_val} | **{sig}** | {rest_details} |")
                else:
                    table_rows.append(f"| {item} | | | |")
            output.append("\n".join(table_rows))
            output.append("")
        elif sec_name_lower == "footer":
            output.append("<details><summary>ℹ️ Metadata & Attribution</summary>")
            output.append(content)
            output.append("</details>\n")
        else:
            if sec_name:
                output.append(f"## {emoji} {sec_name}\n")
            output.append(content)
            output.append("")

    return "\n".join(output)


def send_text(text, parse_mode="HTML", mode="auto", token=None, chat_id=None):
    t = token or TOKEN
    c = chat_id or CHAT_ID
    if is_raw_report(text):
        text = auto_format_content(text)
        mode = "markdown"
    fmt = detect_format(text) if mode == "auto" else mode.lower()
    if parse_mode in ("Markdown", "MarkdownV2"):
        fmt = "markdown"

    url = f"https://api.telegram.org/bot{t}/sendRichMessage"
    payload = {"chat_id": c, "rich_message": {fmt: text}}
    try:
        r = requests.post(url, json=payload, timeout=15)
        res = r.json()
        if res.get("ok"):
            return res
    except Exception as e:
        pass

    fallback_url = f"https://api.telegram.org/bot{t}/sendMessage"
    try:
        r = requests.post(fallback_url, json={"chat_id": c, "text": text, "parse_mode": parse_mode}, timeout=15)
        return r.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}


def send_file(file_path, caption=None, token=None, chat_id=None):
    t = token or TOKEN
    c = chat_id or CHAT_ID
    if not os.path.exists(file_path):
        return {"ok": False, "error": f"File not found: {file_path}"}
    url = f"https://api.telegram.org/bot{t}/sendDocument"
    with open(file_path, "rb") as f:
        data = {"chat_id": c}
        if caption:
            data["caption"] = caption
            data["parse_mode"] = "HTML"
        try:
            r = requests.post(url, data=data, files={"document": f}, timeout=30)
            return r.json()
        except Exception as e:
            return {"ok": False, "error": str(e)}
