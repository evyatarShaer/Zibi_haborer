#!/usr/bin/env bash
# Phase 2A local server (SPEC §14): HaBorer on this PC. Ctrl+C stops it. Port: BORER_PORT
# (default 8000). Phones reach it through scripts/tunnel.sh (LAN access to WSL timed out).
set -euo pipefail
cd "$(dirname "$0")/../api"
port="${BORER_PORT:-8000}"
echo "HaBorer: http://localhost:$port  (phone: scripts/tunnel.sh)"
echo "Loading the fly brain (two workers)..."
PYTHONPATH=src:../sim/src exec uv run python -m borer_api
