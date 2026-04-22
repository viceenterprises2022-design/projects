from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from daily_market_report.models.snapshot import AssetConfig, AssetSnapshot, QuotePayload
from daily_market_report.tools.cache import DiskCache
from daily_market_report.tools.providers.google_finance import fetch_google_finance
from daily_market_report.tools.providers.yahoo import fetch_yahoo, yahoo_history_for_pivots
from daily_market_report.tools.technicals import build_technicals_from_yahoo_df
from daily_market_report.tools.validate import relative_pct_diff, validate_quote


def _cache_key(provider: str, *parts: str) -> str:
    return provider + "|" + "|".join(parts)


def merge_quotes_for_asset(
    asset: AssetConfig,
    cache: DiskCache | None,
    cross_check_enabled: bool,
) -> tuple[
    QuotePayload | None,
    QuotePayload | None,
    str,
    bool,
    str | None,
    list[float],
]:
    """
    Returns (display_quote, other_quote, display_source, disagreement, cross_note, yahoo_sparkline_series).
    other_quote is the alternate venue when available (e.g. Google when Yahoo is displayed).
    """
    ykey = _cache_key("yahoo", asset.yahoo_symbol)
    yq: QuotePayload
    y_series: list[float]

    if cache and (cached := cache.get(ykey)):
        yq = QuotePayload.model_validate(cached["quote"])
        y_series = list(cached.get("series") or [])
    else:
        yq, y_series = fetch_yahoo(asset.yahoo_symbol)
        if cache:
            cache.set(
                ykey,
                {"quote": yq.model_dump(mode="json"), "series": y_series},
            )

    y_ok = validate_quote(yq)
    gq: QuotePayload | None = None
    need_google = (not y_ok) or cross_check_enabled
    gkey = _cache_key("google", asset.google_finance_quote)

    if need_google:
        if cache and (gcached := cache.get(gkey)):
            gq = QuotePayload.model_validate(gcached)
        else:
            gq = fetch_google_finance(asset.google_finance_quote)
            if cache and gq:
                cache.set(gkey, gq.model_dump(mode="json"))

    g_ok = validate_quote(gq)
    disagreement = False
    cross_note: str | None = None

    if y_ok and g_ok and yq and gq and yq.last is not None and gq.last is not None:
        diff = relative_pct_diff(yq.last, gq.last)
        if diff > asset.price_divergence_pct:
            disagreement = True
            cross_note = (
                f"Yahoo vs Google spot differ by {diff:.2f}% "
                f"(threshold {asset.price_divergence_pct}%) — verify before trading."
            )

    if y_ok:
        return yq, gq if g_ok else None, "yahoo", disagreement, cross_note, y_series
    if g_ok and gq:
        return gq, yq, "google_finance", False, cross_note, y_series
    return None, gq or yq, "", False, cross_note, y_series


def build_asset_snapshot(
    asset: AssetConfig,
    cache: DiskCache | None,
    cross_check_enabled: bool,
) -> AssetSnapshot:
    display_q, other_q, display_src, disagreement, cross_note, y_series = merge_quotes_for_asset(
        asset, cache, cross_check_enabled
    )
    snap = AssetSnapshot(
        asset_id=asset.id,
        display_name=asset.display_name,
        quote=display_q,
        backup_quote=other_q,
        display_source=display_src,
        quote_disagreement=disagreement,
        cross_check_note=cross_note,
    )
    sources: list[str] = []
    if display_q:
        sources.append(display_q.source)
    if other_q and other_q.source not in sources:
        sources.append(other_q.source)
    snap.data_sources = sources

    if snap.quote is None:
        snap.data_unavailable = True
        return snap

    y_hist = yahoo_history_for_pivots(asset.yahoo_symbol)
    snap.technicals = build_technicals_from_yahoo_df(y_hist, snap.quote.last)
    if not snap.technicals.sparkline_series and y_series:
        snap.technicals.sparkline_series = y_series[-6:]

    return snap


def collect_all_assets(
    assets: list[AssetConfig],
    cache_dir: Path,
    cache_ttl: int,
    cross_check_enabled: bool,
    max_workers: int = 4,
) -> list[AssetSnapshot]:
    cache = DiskCache(cache_dir, ttl_seconds=cache_ttl)
    by_id: dict[str, AssetSnapshot] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(build_asset_snapshot, a, cache, cross_check_enabled): a.id for a in assets}
        for fut in as_completed(futs):
            sid = futs[fut]
            try:
                by_id[sid] = fut.result()
            except Exception as exn:  # noqa: BLE001
                by_id[sid] = AssetSnapshot(
                    asset_id=sid,
                    display_name=sid,
                    data_unavailable=True,
                    narrative_error=str(exn),
                )
    return [by_id[a.id] for a in assets if a.id in by_id]


def evidence_packet(assets: list[AssetSnapshot]) -> str:
    rows = []
    for a in assets:
        rows.append(
            {
                "asset_id": a.asset_id,
                "display_name": a.display_name,
                "data_unavailable": a.data_unavailable,
                "quote": a.quote.model_dump(mode="json") if a.quote else None,
                "backup_quote": a.backup_quote.model_dump(mode="json") if a.backup_quote else None,
                "display_source": a.display_source,
                "quote_disagreement": a.quote_disagreement,
                "cross_check_note": a.cross_check_note,
                "technicals": a.technicals.model_dump(mode="json"),
                "news_candidates": [n.model_dump(mode="json") for n in a.news_candidates[:25]],
            }
        )
    return json.dumps(rows, indent=2)
