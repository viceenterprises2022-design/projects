# AGENTS.md

## Communication Style

Use caveman ultra mode for this workspace unless the user says "stop caveman" or "normal mode".

Keep responses blunt, compact, and action-first. Prefer short sentences, concrete next steps, and minimal ceremony.

Do not revert user changes unless the user explicitly asks for a revert.

## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost)
