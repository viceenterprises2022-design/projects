# VC & Seed Fund Daily Deep Dive Pipeline

A multi-agent, composite reasoning pipeline built on AgentField that automates daily venture capital and seed fund investment deep dives across Asia, US, Europe, and Africa. It uses Exa search to discover recent funding announcements, analyzes each deal in parallel to extract rounds, amounts, sectors, tech descriptions, and estimated financials (ARR, profit, CAGR), and consolidates them into a sector-grouped intelligence report.

## Architecture

This agent is built as a depth-5 composite reasoning cascade to maximize parallelism and avoid context-limit degradation:

- **Entry reasoner:** `vc-deepdive.deep_dive_vc` (tagged as `"entry"`)
- **Pipeline flow:**
  1. `intake_router` (Committee Router) — Validates the list of target regions.
  2. `regional_researcher` (Specialist Router) — Queries Exa to fetch news and extracts VC/startup candidates.
  3. `deal_analyzer` (Specialist Router) — Analyzes each candidate deal in parallel.
  4. `metric_estimator` (Specialist Router) — Focuses on extracting or estimating startup financials (ARR, profit, CAGR).
  5. `report_synthesizer` (Committee Router) — Synthesizes consolidated findings into a sector-grouped markdown report.

## Run

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` and configure your keys. You must provide `GOOGLE_API_KEY` (or `OPENROUTER_API_KEY`) and `EXA_API_KEY`.
3. Start the stack via Docker Compose:
   ```bash
   docker compose up --build
   ```

Wait until you see `agent registered` in the agent container logs.

## Verify (run in another terminal)

1. Check that the control plane is healthy:
   ```bash
   curl -fsS http://localhost:8080/api/v1/health | jq
   ```
2. Ensure the agent has registered and its capabilities are discoverable:
   ```bash
   curl -fsS http://localhost:8080/api/v1/discovery/capabilities \
     | jq '.capabilities[] | select(.agent_id=="vc-deepdive") | {
         agent_id,
         n_reasoners: (.reasoners | length),
         entry: [.reasoners[] | select(.tags[]? == "entry") | .id],
         all_reasoner_ids: [.reasoners[].id]
       }'
   ```

## Run a daily deep dive (smoke test)

To trigger the pipeline, invoke the entry reasoner asynchronously:

```bash
# 1. Start execution (returns an execution_id immediately)
EXEC_ID=$(curl -sS -X POST http://localhost:8080/api/v1/execute/async/vc-deepdive.deep_dive_vc \
  -H 'Content-Type: application/json' \
  -d '{
    "input": {
      "regions": ["asia", "us", "europe", "africa"],
      "model": "google/gemini-1.5-pro"
    }
  }' | jq -r '.execution_id')
echo "Execution started: $EXEC_ID"

# 2. Poll status until execution completes
while :; do
  R=$(curl -sS http://localhost:8080/api/v1/executions/$EXEC_ID)
  S=$(echo "$R" | jq -r '.status')
  case "$S" in
    succeeded)
      echo "$R" | jq -r '.result.report_md'
      break
      ;;
    failed)
      echo "Execution failed!"
      echo "$R" | jq '.'
      break
      ;;
    *)
      echo "Still running (status: $S)..."
      sleep 5
      ;;
  esac
done
```

## View Cryptographic Workflow Chain

Check the verifiable credential audit trail for the execution:

```bash
LAST_EXEC=$(curl -s http://localhost:8080/api/v1/executions | jq -r '.[0].workflow_id')
curl -s http://localhost:8080/api/v1/did/workflow/$LAST_EXEC/vc-chain | jq
```

## Stop

To stop and remove containers and local volumes:
```bash
docker compose down --volumes
```
