"""
AlphaCopy - Notification System
Sends trade alerts via Telegram and/or Discord.
"""
import logging
from typing import Optional
import aiohttp

logger = logging.getLogger(__name__)


class Notifier:
    def __init__(self, telegram_token: str = "", telegram_chat_id: str = "",
                 discord_webhook: str = ""):
        self.tg_token    = telegram_token
        self.tg_chat_id  = telegram_chat_id
        self.disc_webhook = discord_webhook

    async def send(self, message: str) -> None:
        """Send notification to all configured channels."""
        logger.info(f"[NOTIFY] {message}")
        if self.tg_token and self.tg_chat_id:
            await self._send_telegram(message)
        if self.disc_webhook:
            await self._send_discord(message)

    async def _send_telegram(self, text: str) -> None:
        url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
        payload = {"chat_id": self.tg_chat_id, "text": text, "parse_mode": "HTML"}
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(url, json=payload) as r:
                    if r.status != 200:
                        logger.warning(f"Telegram error: {r.status}")
        except Exception as e:
            logger.warning(f"Telegram send failed: {e}")

    async def _send_discord(self, text: str) -> None:
        try:
            async with aiohttp.ClientSession() as s:
                await s.post(self.disc_webhook, json={"content": text})
        except Exception as e:
            logger.warning(f"Discord send failed: {e}")
