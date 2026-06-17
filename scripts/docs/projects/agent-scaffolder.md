---
type: Utility
title: Agent Scaffolder
description: Automated tool for scaffolding production-ready agents using template presets.
tags: [agents, templates, automation]
timestamp: 2026-06-17T23:30:00Z
---

# 🛠️ Agent Scaffolder

> Section group: **🚀 Script Index**


| Script | Description |
|:--- |:--- |
| `scaffold_agent.py` | **Production Agent Scaffolder**. Copies `templates/production-agent/` to a new directory, substitutes `{{AGENT_NAME}}` placeholders in all files, and initialises a git repo. |

```bash
python3 scaffold_agent.py --name "Market Assistant"
python3 scaffold_agent.py --name "My Bot" --dest /path/to/dest
```

---
