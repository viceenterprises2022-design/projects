---
type: "query"
date: "2026-05-20T15:15:45.908674+00:00"
question: "Why does main() connect Community 2 to Community 1, Community 3, Community 5, Community 7, Community 8, Community 10, Community 12, Community 14, Community 21?"
contributor: "graphify"
source_nodes: ["main_main"]
---

# Q: Why does main() connect Community 2 to Community 1, Community 3, Community 5, Community 7, Community 8, Community 10, Community 12, Community 14, Community 21?

## Answer

Node main_main in everything-claude-code/ecc2/src/main.rs (L1310) is the central orchestration entry point of the Rust engine. It initializes runtime, parses CLI args, bootstraps managers, loads configs/profiles, and spawns the coordination loop. This links the core session managers (Community 2) with CLI worktree policies (Community 1/3), configs (Community 7/12), compliance rules (Community 21), AST parsing (Community 5), and GUI/views (Community 8).

## Source Nodes

- main_main