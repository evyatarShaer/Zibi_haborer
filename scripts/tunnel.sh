#!/usr/bin/env bash
# Phone play-testing (Phase 2A): a Cloudflare quick tunnel to the local server. Free, no
# account; a random https://*.trycloudflare.com URL, new on every start; anyone with the
# URL can open the app while it runs. LAN access to WSL timed out even with the Hyper-V
# firewall open (DECISIONS.md 2026-10-25). Runs detached as unit haborer-tunnel.
# --protocol http2 (TCP 443): QUIC (UDP 7844) is blocked on the owner's network, where a
# QUIC tunnel registers its URL but answers 530. The URL is printed only after the first
# "Registered tunnel connection" line in a fresh log, read from the metrics /quicktunnel
# endpoint. Log: api/data/tunnel.log (`scripts/tunnel.sh log` shows its tail).
# Stop: systemctl --user stop haborer-tunnel. Binary: CLOUDFLARED (default: PATH).
set -euo pipefail
cd "$(dirname "$0")/.."
unit=haborer-tunnel log=api/data/tunnel.log
if [ "${1:-}" = log ]; then exec tail -n "${2:-40}" "$log"; fi
bin=$(command -v "${CLOUDFLARED:-cloudflared}") || {
  echo "cloudflared not found: install it in WSL or set CLOUDFLARED=/path/to/cloudflared" >&2
  exit 1
}
port="${BORER_PORT:-8000}" metrics="${TUNNEL_METRICS:-127.0.0.1:20241}"
mkdir -p api/data
systemctl --user stop "$unit" 2>/dev/null || true
: > "$log"
scripts/detach.sh "$unit" "$log" "$bin" tunnel --protocol http2 --metrics "$metrics" \
  --url "http://localhost:$port" > /dev/null
for _ in $(seq 60); do
  if grep -q 'Registered tunnel connection' "$log"; then
    host=$(curl -sf "http://$metrics/quicktunnel" | grep -o '[a-z0-9-]*\.trycloudflare\.com') || true
    if [ -n "${host:-}" ]; then
      echo "Open on the phone: https://$host"
      echo "Log: $log (scripts/tunnel.sh log)"
      exit 0
    fi
  fi
  sleep 1
done
echo "No registered tunnel connection after 60 s; last lines of $log:" >&2
tail -n 20 "$log" >&2
exit 1
