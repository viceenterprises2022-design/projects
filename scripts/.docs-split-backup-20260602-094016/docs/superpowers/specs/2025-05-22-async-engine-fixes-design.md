# Design Doc: Asynchronous Data Engine Fixes

## Problem
`market_engine.py` lacks error handling for network requests and JSON parsing. It also performs JSON parsing sequentially instead of in parallel. Docstrings are missing.

## Proposed Changes

### 1. Robust Error Handling
- Wrap `session.get` calls in `try/except` to catch `aiohttp.ClientError`.
- Wrap `r.json()` calls in `try/except` to catch `ValueError` (malformed JSON).

### 2. Parallel JSON Parsing
- Use `asyncio.gather(r1.json(), r2.json())` instead of sequential `await`.

### 3. Documentation
- Add Google-style docstrings to `MarketEngine` class and all methods (`__init__`, `fetch_binance`, `fetch_all`).

## Verification Plan
- Run `python3 test_fetch.py` to ensure core functionality is preserved.
- Add a mock error test if possible, or verify manual failure handling.
