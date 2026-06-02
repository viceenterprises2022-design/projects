# 🎓 Toddle → NotebookLM

> Section group: **🚀 Script Index**

*Daily sync of school subject notes from Toddle LMS to NotebookLM study guides.*

| Script | Description |
|:--- |:--- |
| `toddle_notebooklm_sync.py` | **Orchestrator** (4 phases). Inventory → Download → Convert → Upload to NotebookLM + generate study guides. State tracked in `sync_state.json`. Skips subjects with no changes since last sync. |
| `toddle_all_inventory.py` | Inventories all subject files from Toddle LMS. |
| `toddle_bulk_download.py` | Downloads new/changed Toddle files. |
| `toddle_bulk_convert.py` | Converts files to markdown in `output/text/<subject>/`. |

**Subjects tracked:** Physics, Chemistry, Mathematics, English, Biology, History, Geography, Spanish, Design, Visual Arts

```bash
venv/bin/python toddle_notebooklm_sync.py
venv/bin/python toddle_notebooklm_sync.py --skip-inventory --skip-download  # convert + upload only
```

---
