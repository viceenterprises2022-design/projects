# 🎓 Arxiv → NotebookLM

> Section group: **🚀 Script Index**

*Monitors academic research across 10 disciplines, selects the latest candidate, processes via NotebookLM, and delivers briefings + mind-maps to Slack.*

| Script | Description |
|:--- |:--- |
| `arxiv_to_notebooklm.py` | **Research Pipeline**. Scrapes 10 category recent pages sequentially with custom browser headers, selects a priority-based candidates paper, downloads and sanitizes PDF, uploads to a new NotebookLM notebook, generates briefing-doc report + mind-map, formats Block Kit Slack message, and deletes the notebook. Daily cron trigger with 48-hour success lock for self-healing. |
| `arxiv_to_notebooklm_state.json` | **State**. Tracks success timestamps and list of processed paper IDs. |

**Disciplines Scraped:** Physics (`quant-ph`, `physics.space-ph`), Mathematics (`math`), Computer Science (`cs.AI`, `cs`, `cs.NE`, `cs.RO`, `cs.CR`), Quantitative Finance (`q-fin`), Economics (`econ`).

**Priority Queue:** `cs.AI` > `cs` > `cs.NE` > `cs.RO` > `cs.CR` > `quant-ph` > `physics.space-ph` > `math` > `q-fin` > `econ`

**Run Command:**
```bash
# Dry run candidate evaluation
python3 arxiv_to_notebooklm.py --dry-run

# Force immediate execution bypassing 48h cooldown lock
python3 arxiv_to_notebooklm.py --force
```

**Cron (already installed, daily trigger at 8:30 AM IST):**
```
30 8 * * * cd /home/vreddy1/Desktop/Projects/scripts && /home/vreddy1/Desktop/Projects/scripts/venv/bin/python arxiv_to_notebooklm.py >> logs/arxiv_nlm_cron.log 2>&1
```

---
