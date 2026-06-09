# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability or credentials leak within this repository, please do NOT create a public issue. Instead, report it directly to the repository administrator.

## Credentials and Secrets Management

*   **Zero Secrets in Source Control:** No passwords, API keys, JWT bearer tokens, or sensitive credentials may be committed directly to source control.
*   **Environment Variables:** Use environment files (`.env`, `.env.local`) for environment injection.
*   **Git Hygiene:** Ensure `.gitignore` is populated with all potential credentials/state files (`.env`, `*.db`, `*.session`, `*.json` state files).

## Multi-Agent Execution Guardrails

*   **Hook Verification:** Pre-tool hooks must run validation checks against any execution commands to detect potentially hazardous commands (e.g. `rm -rf`, raw API calls modifying infrastructure, or `--no-verify` git flags).
*   **Restricted Sandboxing:** Command execution tools must operate within bounded, user-level terminals rather than root contexts wherever possible.
