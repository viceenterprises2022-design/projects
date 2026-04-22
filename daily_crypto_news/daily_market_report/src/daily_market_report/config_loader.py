from __future__ import annotations

from pathlib import Path

import yaml

from daily_market_report.models.snapshot import AssetConfig


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_asset_configs(path: Path | None = None) -> tuple[list[AssetConfig], dict]:
    root = project_root()
    cfg_path = path or (root / "config" / "assets.yaml")
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    defaults = raw.get("defaults") or {}
    div = float(defaults.get("price_divergence_pct", 0.75))
    out: list[AssetConfig] = []
    for row in raw.get("assets", []):
        ac = AssetConfig(
            id=row["id"],
            display_name=row["display_name"],
            yahoo_symbol=row["yahoo_symbol"],
            google_finance_quote=row["google_finance_quote"],
            timezone=row.get("timezone") or defaults.get("timezone") or "UTC",
            news_keywords=list(row.get("news_keywords") or []),
            rss_feeds=list(row.get("rss_feeds") or []),
            price_divergence_pct=float(row.get("price_divergence_pct", div)),
        )
        out.append(ac)
    meta = {
        "cross_check_enabled": bool(defaults.get("cross_check_enabled", True)),
        "cache_ttl_seconds": int(defaults.get("cache_ttl_seconds", 900)),
    }
    return out, meta
