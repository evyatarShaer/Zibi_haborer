#!/usr/bin/env bash
# Fails if any code file in the repo is longer than MAX_LINES (default 200).
# Used by .githooks/pre-commit and the Claude Code PostToolUse hook.
# Exit 2 so Claude Code feeds the message back to Claude.
set -u
MAX_LINES="${MAX_LINES:-200}"
cd "$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
fail=0
while IFS= read -r f; do
  [ -f "$f" ] || continue
  n=$(wc -l < "$f")
  if [ "$n" -gt "$MAX_LINES" ]; then
    echo "File too long: $f has $n lines (max $MAX_LINES). Split it into smaller modules." >&2
    fail=1
  fi
done < <(git ls-files -co --exclude-standard -- \
  '*.py' '*.ts' '*.tsx' '*.js' '*.jsx' '*.mjs' '*.css' '*.sql' '*.sh')
[ "$fail" -eq 0 ] || exit 2
