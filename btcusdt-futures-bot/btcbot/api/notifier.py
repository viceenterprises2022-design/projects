from __future__ import annotations

import json
import urllib.request


class SlackNotifier:
    def __init__(self, webhook_url: str = "", username: str = "AlphaEdge BTC Bot"):
        self.webhook_url = webhook_url
        self.username = username

    @property
    def enabled(self) -> bool:
        return bool(self.webhook_url)

    def send(self, title: str, text: str) -> bool:
        message = f"*{title}*\n{text}"
        if not self.enabled:
            print(message)
            return False
        payload = json.dumps({"text": message, "username": self.username}).encode("utf-8")
        req = urllib.request.Request(
            self.webhook_url,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "btcusdt-futures-bot/0.1"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return 200 <= resp.status < 300

