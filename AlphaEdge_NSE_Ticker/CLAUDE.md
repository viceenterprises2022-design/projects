# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependency (requests only — no yfinance)
pip install requests

# Ubuntu: also need tkinter
sudo apt install python3-tk

# Run
python alphaedge_ticker.py

# Platform launchers (handle dep install automatically)
bash launch_ubuntu.sh
bash launch_macos.sh
launch_windows.bat
```

## First-run setup

`DEFAULT_CONFIG` in the source has a hardcoded fallback `upstox_token`. Override it by setting `upstox_token` in `~/.alphaedge_ticker.json`. Config file is auto-created with defaults on first `_load_cfg()`. The ticker shows a warning banner and skips all API calls if the resolved token is empty.

## Architecture

Single-file app (`alphaedge_ticker.py`). Two classes plus module-level helpers.

**Module-level helpers** — pure functions, no side effects:
- `_oi_str(oi)` — formats OI as Cr/L/K
- `_pct(curr, prev)` — safe percentage change
- `_f(val)` — safe `float()` with default 0.0

**`ROW_DEFS`** — module-level list defining the three rows (top→bottom): NIFTY (step 50, ±6 strikes = ±300 pts), BNKN (step 100, ±3 strikes = ±300 pts), SENSEX (step 100, ±3 strikes = ±300 pts). Changing `strikes_around` here controls option depth for all rows.

**`DataFetcher`** — thread-safe data layer:
- `_snapshot` dict (`ikey → [items]`) swapped atomically under `_lock` at end of `refresh()`; `get()` returns a shallow copy
- `_idx_px` dict caches live index prices; populated by `_fetch_quotes(out)` before `_fetch_options(out)` runs (sequential in `refresh()`)
- `_expiry_cache` dict caches resolved expiry per ikey; reused until date passes
- `_fetch_quotes(out)` — single batched `GET /v2/market-quote/quotes`; writes INDEX items into `out[ikey]`
- `_resolve_expiry(ikey)` — probes up to 8 days forward until option/chain returns data
- `_fetch_options(out)` — one `GET /v2/option/chain` call per row; ATM = `round(curr/step)*step`; appends CE/PE items sorted by ascending strike then kind; `"atm": True` when `strike == atm`
- `refresh()` builds a fresh `out` dict, calls both fetchers, then swaps `_snapshot` under lock

**`TickerBanner`** — three-row tkinter GUI:
- Window height = `height × 3`; three `tk.Frame` rows packed top→bottom
- Each row: badge label (index name, distinct colour) + canvas + timestamp label (last row only)
- `_rows` list of dicts: `{ikey, canvas, ts_lbl, segments, offset, content_w, after_id}`
- Per-row scroll: `_scroll_row(row)` runs at ~60fps via `root.after(16, lambda r=row: ...)`, advancing `row["offset"]` and wrapping segments when `vx + w < 0` by incrementing `seg[1]` by `content_w + screen_w`
- `_rebuild_row(row, items)` cancels the row's `after_id` before rebuilding; called via `root.after(0, ...)` from background threads
- Config persisted to `~/.alphaedge_ticker.json`; flat merge over `DEFAULT_CONFIG` at startup (no nested dict special-casing)

## Upstox API endpoints used

| Endpoint | Purpose |
|----------|---------|
| `GET /v2/market-quote/quotes?instrument_key=A,B,C` | Batch index quotes |
| `GET /v2/option/chain?instrument_key=X&expiry_date=YYYY-MM-DD` | Option chain per index (also used for expiry probing) |

Auth header: `Authorization: Bearer <token>`

## Key instrument key format

- NSE indices: `NSE_INDEX|Nifty 50`, `NSE_INDEX|Nifty Bank`
- BSE indices: `BSE_INDEX|SENSEX`
- NSE equities: `NSE_EQ|RELIANCE`, `NSE_EQ|TCS`
- Options are identified by the underlying index key; Upstox returns the chain including CE/PE market data per strike

## Display colour coding

| Colour | Meaning |
|--------|---------|
| Gold `#ffd54f` | Index labels |
| Muted green `#a5d6a7` | OTM/ITM call labels |
| Bright green `#69f0ae` | ATM call labels |
| Muted rose `#ef9a9a` | OTM/ITM put labels |
| Bright red `#ff5252` | ATM put labels |

ATM strikes also append ` ◉` to the label text.
