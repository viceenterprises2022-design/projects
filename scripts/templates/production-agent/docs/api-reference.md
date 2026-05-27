# API Documentation

## Chat Endpoint
`POST /api/chat`
Payload:
```json
{
  "session_id": "test-session",
  "query": "Hello world"
}
```

Response:
```json
{
  "session_id": "test-session",
  "output": "Answer content...",
  "reasoning_trace": ["Plan step", "Act step"],
  "tools_executed": [],
  "cost": 0.001,
  "latency_ms": 150.0
}
```

## Health check
`GET /health`
Returns gateway status and active security modes.
