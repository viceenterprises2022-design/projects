from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any


class DiskCache:
    def __init__(self, directory: Path, ttl_seconds: int = 900) -> None:
        self.directory = directory
        self.ttl_seconds = ttl_seconds
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        h = hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]
        return self.directory / f"{h}.json"

    def get(self, key: str) -> Any | None:
        p = self._path(key)
        if not p.exists():
            return None
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        if time.time() - payload.get("ts", 0) > self.ttl_seconds:
            return None
        return payload.get("data")

    def set(self, key: str, data: Any) -> None:
        p = self._path(key)
        payload = {"ts": time.time(), "data": data}
        p.write_text(json.dumps(payload, default=str), encoding="utf-8")
