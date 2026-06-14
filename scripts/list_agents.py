import json

with open("agents.json") as f:
    agents = json.load(f)

print("=== AGENTS STATUS ===")
for a in agents:
    print(f"Agent: {a['name']} | Status: {a['status']} | Runtime Mode: {a['runtime_mode']}")
