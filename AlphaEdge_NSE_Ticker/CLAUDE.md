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

**`DataFetcher`** — thread-safe data layer:
- `_idx_px` dict caches live index prices from `_fetch_quotes()`; must be populated before `_fetch_options()` runs (called sequentially in `refresh()`)
- `_expiry_cache` dict caches resolved expiry date per instrument key; reused until the date passes
- `_fetch_quotes()` — single batched `GET /v2/market-quote/quotes` call with all index instrument keys comma-joined. Response keys use `:` not `|` — converted via `.replace("|", ":")`
- `_resolve_expiry(ikey)` — probes up to 8 days forward (`date.today() + timedelta(days=d)`) until the option/chain endpoint returns data; caches the result. No manual weekday config needed.
- `_fetch_options()` — one `GET /v2/option/chain` call per configured index using the resolved expiry. ATM = `round(curr_price / step) * step`. Shows ATM ± `strikes_around` strikes for both CE and PE. Items marked `"atm": True` when `strike == atm`. Results sorted: NIFTY → BNKN → SENSEX, then ascending strike, CE before PE.
- `refresh()` — called from daemon threads; writes atomically under `_lock`. Guards against empty token before making any HTTP call.

**`TickerBanner`** — tkinter GUI:
- Canvas-based scrolling: `_segments = [[canvas_id, virtual_init_x, width]]`. `_scroll_loop()` runs at ~60fps via `root.after(16)`, advancing `_offset` and wrapping items when `vx + w < 0` by incrementing `init_x` by `_content_w + screen_w`
- `_rebuild()` cancels any pending scroll loop before rebuilding canvas items; must be called via `root.after(0, ...)` from background threads
- Config persisted to `~/.alphaedge_ticker.json`; merged over `DEFAULT_CONFIG` at startup; nested dicts (`indices`, `option_chains`) loaded verbatim from saved file to allow customization

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
