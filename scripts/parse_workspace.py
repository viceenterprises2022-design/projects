import json

with open("projects.json") as f:
    projects = json.load(f)
with open("issues.json") as f:
    issues_data = json.load(f)
with open("agents.json") as f:
    agents = json.load(f)

issues = issues_data.get("issues", [])
project_map = {p["id"]: p for p in projects}
agent_map = {a["id"]: a for a in agents}

print("=== ALL ISSUES UPDATED OR CREATED TODAY (2026-06-14) ===")
today_issues = []
for i in issues:
    created_at = i.get("created_at", "")
    updated_at = i.get("updated_at", "")
    if created_at.startswith("2026-06-14") or updated_at.startswith("2026-06-14"):
        today_issues.append(i)

for i in today_issues:
    proj_id = i.get("project_id")
    proj_title = project_map.get(proj_id, {}).get("title") if proj_id else "None"
    assignee_id = i.get("assignee_id")
    assignee_name = agent_map.get(assignee_id, {}).get("name") if assignee_id else "Unassigned"
    print(f"Key: {i.get('identifier')} | Title: {i['title']} | Status: {i['status']} | Project: {proj_title} | Assignee: {assignee_name}")
    print(f"  Created: {i.get('created_at')} | Updated: {i.get('updated_at')}")
