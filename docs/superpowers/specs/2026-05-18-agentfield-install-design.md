# Agentfield Installation Design

**Date:** 2026-05-18
**Status:** Approved

## Purpose
Install Agentfield.ai CLI (`af`) globally on the system as requested by the user.

## Architecture
- **Source:** https://agentfield.ai/install.sh
- **Method:** `curl` pipe to `bash`
- **Scope:** Global system installation

## Components
1. **Installer:** Official Agentfield install script.
2. **Binary:** `af` executable placed in system path (usually `/usr/local/bin` or `~/bin`).

## Verification
- Run `af --version` to confirm successful installation.

## Safety & Constraints
- User explicitly requested "Direct (Fast)" execution without prior script inspection.
- System is Linux.

## Testing
- Command execution check.
- Binary availability check.
