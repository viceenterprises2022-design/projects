import os
import aiohttp
import logging
from typing import Optional, Any
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class TelegramClient:
    """
    Fresh Telegram Integration Client.
    Handles sending formatted messages and documents to Telegram.
    """
    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        load_dotenv()
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.base_url = f"https://api.telegram.org/bot{self.token}" if self.token else None

    @property
    def is_configured(self) -> bool:
        return bool(self.token and self.chat_id)

    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a text message to the configured chat."""
        if not self.is_configured:
            logger.warning("Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")
            return False

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Telegram error {response.status}: {error_text}")
                        return False
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    async def send_report(self, ticker: str, report_data: dict):
        """Formats and sends a trading report."""
        header = f"🚀 <b>Trading Analysis: {ticker}</b>\n"
        header += "━━━━━━━━━━━━━━━━━━━━━\n"
        
        # Simple formatting for the report
        body = ""
        for section, data in report_data.items():
            if section == "ticker": continue
            body += f"\n📊 <b>{section.upper()}</b>\n"
            if isinstance(data, dict):
                # Extract summary if available, else first few keys
                summary = data.get("summary") or data.get("analysis")
                if summary:
                    body += f"{summary}\n"
                else:
                    for k, v in list(data.items())[:3]:
                        body += f"• {k}: <code>{v}</code>\n"
            else:
                body += f"{str(data)[:200]}...\n"

        footer = "\n━━━━━━━━━━━━━━━━━━━━━\n"
        footer += f"🕒 {os.popen('date').read().strip()}"

        full_message = header + body + footer
        return await self.send_message(full_message)
