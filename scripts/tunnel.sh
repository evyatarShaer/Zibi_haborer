#!/usr/bin/env bash
# Phone play-testing (Phase 2A): a Cloudflare quick tunnel to the local server. Free, no
# account; a random https://*.trycloudflare.com URL, new on every start; anyone with the
# URL can open the app while it runs. LAN access to WSL timed out even with the Hyper-V
# firewall open (DECISIONS.md 2026-10-25). Runs detached as unit haborer-tunnel and prints
# the URL. Stop: systemctl --user stop haborer-tunnel. Binary: CLOUDFLARED (default: PATH).
set -euo pipefail
cd "$(dirname "$0")/.."
bin=$(command -v "${CLOUDFLARED:-cloudflared}") || {
  echo "cloudflared not found: install it in WSL or set CLOUDFLARED=/path/to/cloudflared" >&2
  exit 1
}
port="${BORER_PORT:-8000}" unit=haborer-tunnel log=api/data/tunnel.log
mkdir -p api/data
systemctl --user stop "$unit" 2>/dev/null || true
: > "$log"
scripts/detach.sh "$unit" "$log" "$bin" tunnel --url "http://localhost:$port" > /dev/null
for _ in $(seq 60); do
  if url=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$log" | head -1) && [ -n "$url" ]; then
    echo "Open on the phone: $url"
    exit 0
  fi
  sleep 1
done
echo "No tunnel URL after 60 s; see $log" >&2
exit 1
