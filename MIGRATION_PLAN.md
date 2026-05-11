# Migration & Sync Index: Ubuntu (Home) <-> MacBook Pro (Mobile)

## 0. Dual-Machine Philosophy
Ubuntu remains the **Permanent Home Desktop/Server**. 
MacBook Pro is the **Mobile Workstation**.
Goal: Seamless transition and environment parity.

## 1. Synchronization Strategy (T-Minus 7 Days to Execution)

### Code & Projects
- **Method:** Git-first. 
- **Action:** Ensure all subdirectories in `~/Desktop/Projects` have remotes.
- **Tools:** Use `git-autosync.sh` (found in scripts) to keep machines aligned.

### Environment Parity
- **Python:** Mirror versions (3.13) and venvs.
- **Node:** Use `nvm` on both to sync versions.
- **CLI Tools:** Gemini CLI, Docker, and `graphify` must be on both.

### Config & Dotfiles
- **Core:** SSH keys (`~/.ssh`), Git config, Bash/Zsh profiles.
- **Sync:** Create a private `dotfiles` repo to manage shared aliases/functions.

### Secrets & Persistence
- **Secrets:** Keep `.env` files in a secure shared vault or manual sync.
- **Database:** `alphaedge.db` and other SQLite files require a sync strategy (Cloud or Remote DB).

## 2. Remote Access
- **Scenario:** Access Ubuntu power/data from MacBook while traveling.
- **Method:** SSH / Tailscale for secure remote terminal access.

## 3. Tool Inventory (Snapshots taken May 10, 2026)
- See `ubuntu_pip_inventory.txt`
- See `ubuntu_npm_inventory.txt`
