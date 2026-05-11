# Repository Guidelines

## Project Structure & Module Organization

This repository contains two root-level script systems. AlphaEdge market intelligence is the primary app: `collector.py` fetches Upstox/Yahoo Finance data, `market_engine.py` and `market_analysis_v*.py` hold analysis logic, `alphaedge_db.py` manages SQLite storage, and `api_server.py` serves the FastAPI API and dashboard. Static dashboard files live in `frontend/` (`dashboard.html`, `app.js`, `style.css`). Exa event-search scripts live in `exa_ai_search.py` and `exa_ai_agents.py`. Runtime artifacts include `*.db`, `logs/`, `*_report.txt`, and `ai_events_results.json`; do not treat these as source unless the task is explicitly data-related. `everything-claude-code/` is a separate embedded project/reference tree.

## Build, Test, and Development Commands

Install root dependencies as needed:

```bash
python3 -m pip install fastapi uvicorn[standard] requests rich exa-py
```

Run the collector once with `python3 collector.py`; run continuously with `python3 collector.py --loop --interval 5`. Start the API and dashboard with `python3 api_server.py`, then open `http://localhost:8765`. Generate the legacy report with `python3 market_analysis_v3.py`, send it through Telegram with `python3 report_and_send.py`, or run stdout-only analysis with `python3 run_analysis_headless.py`. Run Exa search with `EXA_API_KEY=<key> python3 exa_ai_search.py`.

## Coding Style & Naming Conventions

Use Python 3, 4-space indentation, `snake_case` for functions/variables, and uppercase constants for configuration such as symbol maps. Keep scripts executable from the repository root and preserve simple module imports (`import alphaedge_db as db`). Prefer small helper functions around network calls and database operations. Frontend code uses plain HTML/CSS/JavaScript; keep selectors and filenames descriptive.

## Testing Guidelines

There is no root test suite yet. For changes, run the specific script you touched and verify the expected API endpoint or output file. For API changes, check `GET /api/latest`, `GET /api/symbols`, and one `GET /api/history?sym=NIFTY&days=30` request after `collector.py` has populated `alphaedge.db`. If adding tests, place them under `tests/` as `test_*.py` and keep external API calls mocked.

## Commit & Pull Request Guidelines

Recent commits use Conventional Commits, especially `feat: ...`; follow that pattern (`fix: handle empty option chain`, `docs: add contributor guide`). PRs should describe the user-visible change, list commands run, mention required tokens or environment variables, and include screenshots for dashboard UI changes.

## Security & Configuration Tips

Never add new secrets to source. Use environment variables for `EXA_API_KEY`, Telegram credentials, and rotated market-data tokens. Avoid committing regenerated `*.db`, logs, caches, or report outputs unless the change intentionally updates sample data.
