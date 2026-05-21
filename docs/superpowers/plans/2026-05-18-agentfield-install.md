# Agentfield Installation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Install Agentfield.ai CLI (`af`) globally on the system.

**Architecture:** Execute official installation script via curl pipe to bash.

**Tech Stack:** Bash, Curl.

---

### Task 1: Pre-installation Verification (Failing State)

**Files:**
- Modify: N/A (Global binary)

- [ ] **Step 1: Check if `af` already exists**

Run: `af --version`
Expected: FAIL with "command not found"

### Task 2: Execute Installation Script

**Files:**
- Modify: Global system binaries

- [ ] **Step 1: Run installation command**

Run: `curl -fsSL https://agentfield.ai/install.sh | bash`
Expected: Installation logs showing success.

- [ ] **Step 2: Commit (Note: Not repo changes, but system state change)**
Actually, no files to commit in repo yet.

### Task 3: Post-installation Verification (Passing State)

**Files:**
- Modify: N/A

- [ ] **Step 1: Verify `af` version**

Run: `af --version`
Expected: Version output (e.g., `af version 0.1.0`)

### Task 4: Documentation & Cleanup

**Files:**
- Modify: `GEMINI.md`
- Delete: `TODO.md`

- [ ] **Step 1: Update GEMINI.md with new tool info**

```markdown
## Tools
- **Agentfield CLI (`af`):** Installed 2026-05-18.
```

- [ ] **Step 2: Remove temporary TODO.md**

Run: `rm TODO.md`

- [ ] **Step 3: Commit documentation changes**

```bash
git add GEMINI.md docs/superpowers/specs/ docs/superpowers/plans/
git commit -m "docs: install agentfield and update project docs"
