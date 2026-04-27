#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/home/vreddy1/Desktop/Projects"
BRANCH="main"

cd "$REPO_DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository: $REPO_DIR" >&2
  exit 1
fi

git add -A

if git diff --cached --quiet; then
  exit 0
fi

timestamp="$(date '+%Y-%m-%d %H:%M:%S %Z')"
git commit -m "Auto-sync changes: $timestamp"

if git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
  git pull --rebase --autostash origin "$BRANCH"
fi

git push -u origin "$BRANCH"
