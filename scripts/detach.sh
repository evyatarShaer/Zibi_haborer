#!/usr/bin/env bash
# Runs a long job as a systemd user service, so it survives Claude Code /exit
# and the terminal closing. setsid/nohup/tmux are NOT enough under WSL: they
# stay in the terminal's /init session (cgroup /non-systemd), which kills them.
# Needs: systemd=true in /etc/wsl.conf, `loginctl enable-linger $USER` (done).
# Usage: scripts/detach.sh <unit> <log> <command...>   (runs in the current dir)
# Check: systemctl --user status <unit>; tail <log>.  Stop: systemctl --user stop <unit>
set -euo pipefail
unit=$1 log=$(realpath -m "$2"); shift 2
systemd-run --user --unit="$unit" --collect --same-dir -E PATH="$PATH" \
  -p StandardOutput=append:"$log" -p StandardError=append:"$log" "$@"
