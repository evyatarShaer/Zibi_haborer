#!/usr/bin/env bash
# Claude Code Stop hook: don't let a turn end with uncommitted changes.
input=$(cat)
case "$input" in
  *'"stop_hook_active":true'*|*'"stop_hook_active": true'*) exit 0 ;;
esac
cd "$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
if [ -n "$(git status --porcelain)" ]; then
  echo "Uncommitted changes. Commit them (one logical step per commit) and push before finishing:" >&2
  git status --short >&2
  exit 2
fi
