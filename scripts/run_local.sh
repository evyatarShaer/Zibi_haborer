#!/usr/bin/env bash
# Phase 2A local server (SPEC §14): HaBorer on this PC, reachable from phones on the same
# Wi-Fi (WSL mirrored networking). Ctrl+C stops it. Port: BORER_PORT (default 8000).
set -euo pipefail
cd "$(dirname "$0")/../api"
port="${BORER_PORT:-8000}"
echo "HaBorer: http://localhost:$port  (phone: http://$(hostname -I | awk '{print $1}'):$port)"
echo "Loading the fly brain (two workers)..."
PYTHONPATH=src:../sim/src exec uv run python -m borer_api
