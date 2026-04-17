#!/usr/bin/env bash
# TARS v3.1 — install authorship-enforcement git hooks into .git/hooks/.
# Idempotent. Safe to re-run. Run from the repo root.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SRC_DIR="$REPO_ROOT/scripts/githooks"
DEST_DIR="$REPO_ROOT/.git/hooks"

if [ ! -d "$DEST_DIR" ]; then
  echo "ERROR: $DEST_DIR not found. Is this a git working tree?" >&2
  exit 2
fi

for hook in prepare-commit-msg pre-push; do
  src="$SRC_DIR/$hook"
  dst="$DEST_DIR/$hook"
  if [ ! -f "$src" ]; then
    echo "ERROR: missing source hook $src" >&2
    exit 2
  fi
  cp "$src" "$dst"
  chmod +x "$dst"
  echo "installed: $dst"
done

echo "git hooks installed."
