# CLAUDE.md — VC & Seed Fund Daily Deep Dive Pipeline

## Mission

Automates daily venture capital and seed fund investment deep dives across Asia, US, Europe, and Africa to extract sectors, rounds, and financials (ARR, CAGR, Profit/Loss) for strategic market intelligence.

External callers should hit `vc-deepdive.deep_dive_vc` first.

## Architecture at a glance

- **Pattern(s):** Parallel Hunters + Reasoner Composition Cascade
- **Topology:** One AgentField node (`vc-deepdive`) with 5 reasoners and a helper package
- **Entry reasoner:** `deep_dive_vc` — orchestrates the intake, parallel regional research, and synthesis
- **Internal reasoners:**
  - `intake_router` (`.ai()`): Validates and plans region mapping.
  - `regional_researcher` (`.ai()`): Conducts research per region, extracts candidate deals from Exa search text, and parallel dispatches deal analysts.
  - `deal_analyzer` (`.ai()`): Analyzes a specific deal and calls metric estimator.
  - `metric_estimator` (`.ai()`): Forensic financial analysis extracting ARR, Profit, CAGR.
  - `report_synthesizer` (`.ai()`): Formats consolidated deals sector-wise and generates final markdown report.
- **Inter-reasoner traffic:** All internal calls go through `app.call("vc-deepdive.X", ...)`. Never direct HTTP.

## Why this architecture (not a chain)

Decomposes the market intelligence problem into regional specialists running in parallel, avoiding context window limits and reducing cognitive load. Each deal is isolated and analyzed independently down to forensic financials, ensuring that high-yield parallel tasks run concurrently. Final report synthesis converts structured metrics into clear prose for LLM reasoning.

## Primitive selection rules (binding)

- `.ai()` is used at all cognitive gates (`intake_router`, `regional_researcher`, `deal_analyzer`, `metric_estimator`, `report_synthesizer`).
- Every `.ai()` has structured schemas derived from type hints with a `confident: bool` field and deterministic safe default fallbacks in `helpers.py`.
- Deterministic search logic and prose formatting live in plain helper functions inside `reasoners/helpers.py`.

## Data-flow rules

- Structured Pydantic schemas are serialized to dicts when crossing the `app.call` boundary.
- Natural-language strings and prose summaries (via `render_deals_prose`) are used between specialists and the final synthesizer to preserve semantic richness and keep token footprints small.

## Model selection

- Default model: `google/gemini-1.5-pro` via `AI_MODEL` env.
- The entry reasoner accepts an OPTIONAL `model` parameter in the request body. When present, it propagates to all child reasoners via `app.call(..., model=model)`.
- Provider keys: `GOOGLE_API_KEY` is currently set.

## Runtime contract

- Local runtime is `docker-compose.yml` in this directory.
- One container: `agentfield/control-plane:latest` (local mode, SQLite/BoltDB).
- One container: this Python agent node, built from `Dockerfile`.
- The agent node depends on the control plane being healthy before it boots.
- Default ports: control plane `8080`, agent node `8001`.

## Delivery contract — every change must preserve

- ✅ A runnable `docker compose up --build`
- ✅ A valid `.env.example` listing all required keys
- ✅ A `README.md` with the exact verification ladder (health → nodes → capabilities → execute)
- ✅ The canonical curl smoke test in the README — body shape `{"input": {...kwargs...}}`, returns a real reasoned answer not a stub
- ✅ This `CLAUDE.md`

## Validation commands (run after every change)

```bash
python3 -m py_compile main.py reasoners/*.py
docker compose config > /dev/null
docker compose up --build -d
sleep 8
curl -fsS http://localhost:8080/api/v1/health
curl -fsS http://localhost:8080/api/v1/nodes | jq '.[].node_id'
curl -fsS http://localhost:8080/api/v1/discovery/capabilities | jq '.capabilities[] | select(.agent_id=="vc-deepdive")'
# Canonical execution test:
EXEC_ID=$(curl -sS -X POST http://localhost:8080/api/v1/execute/async/vc-deepdive.deep_dive_vc \
  -H 'Content-Type: application/json' \
  -d '{"input": {"regions": ["asia", "us"]}}' | jq -r '.execution_id')
curl -sS http://localhost:8080/api/v1/executions/$EXEC_ID
docker compose down
```

## Anti-patterns (reject these)

- ❌ Direct HTTP between reasoners. All internal traffic uses `app.call`.
- ❌ Hardcoding `node_id` in `app.call`. Always use `f"{app.node_id}.X"`.
- ❌ Hardcoding the model. Always read from env (`AI_MODEL`) and accept a per-request override.
- ❌ Removing the `confident` field from a `.ai()` schema without replacing the validation check.
- ❌ Passing un-serialized Pydantic instances directly across boundary calls.

## Extension points (where to safely add work)

- **Add a new region:** Add the new region string to the intake router validation list and search query.
- **Add custom search filters:** Modify `search_deals_exa` in `helpers.py` to target specific dates, domain blocks, or advanced search terms.
- **Inject custom financial databases:** Extend `metric_estimator` to query local SQLite databases (e.g. `alphaedge.db`) for known companies before falling back to LLM estimation.

## Owner

This system was scaffolded by the `agentfield-multi-reasoner-builder` skill. To rebuild, run that skill again. To extend, follow this CLAUDE.md.
