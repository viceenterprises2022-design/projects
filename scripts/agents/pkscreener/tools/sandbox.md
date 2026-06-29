# Sandbox Pattern

PKScreener runs shell commands (pkscreenercli.py) via PTY subprocess. To
prevent orphan processes and OOM kills:

- **flock lockfile** (`/tmp/pkscreener_runner.lock`): prevents overlapping runs
  from cron piling up orphan processes (May 2026 fix).
- **Process group isolation** (`start_new_session=True` + `os.killpg`): all
  children live in their own session; cleanup kills the group, not just the
  leader.
- **Address space limit** (`RLIMIT_AS=4GB`): runaway scans hit the wall before
  the host OOMs.
- **Startup cleanup** (`kill_orphan_pkscreener`): stale processes from previous
  crashes are reaped before each run.

If you migrate to Docker, remove the `resource.setrlimit` call and use
`docker run --memory=4g --memory-swap=4g` instead.
