# 🤖 YouTube → NotebookLM

> Section group: **🚀 Script Index**

*Monitors YouTube channels for new videos, ingests each into NotebookLM, and delivers reports to Slack via Block Kit.*

| Script | Description |
|:--- |:--- |
| `youtube_to_notebooklm.py` | **Pipeline**. Checks tracked YouTube channels for videos published ≤24h ago, uploads each to a standalone NotebookLM notebook, generates `briefing-doc` report + mind-map, converts mind-map JSON to indented text tree, and sends a structured **Block Kit** Slack message. Safely deletes the notebook after successful Slack delivery. |
| `youtube_channels.json` | **Config**. JSON array of YouTube channel @handles to monitor. |

**Channels tracked (default):** `@DavidOndrej`, `@AkshatZayn`, `@TheNextNewThingAI`, `@LewisWJackson`

**CLI channel management:**
```bash
python3 youtube_to_notebooklm.py --add-channel @NewChannel
python3 youtube_to_notebooklm.py --remove-channel @OldChannel
python3 youtube_to_notebooklm.py --list-channels
```

**Slack output format (Block Kit):**
1. **Header** with pipeline name
2. **Fields** — channel handle + NotebookLM notebook link
3. **Video link**
4. **Divider**
5. **Mind-map** (indented text tree, ≤25 lines, in code block)
6. **Divider**
7. **Report** (first ~2,500 chars; remainder in continuation messages)

**Cron (already installed):**
```
30 11 * * * cd /path/to/scripts && python3 youtube_to_notebooklm.py >> logs/youtube_nlm_cron.log 2>&1
```

**Notebook safety:** Notebooks are deleted ONLY after successful Slack delivery. Deletion is regex-gated (`^[a-zA-Z0-9][a-zA-Z0-9_-]{19,}$`) and `_delete_notebook()` is the sole function authorized to call `notebooklm delete`.

---
