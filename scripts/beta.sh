#!/usr/bin/env bash
# Friends beta from this laptop (P2B-12) while no server exists (DECISIONS.md 2026-10-28):
# the Cloudflare quick tunnel first, then the HaBorer server with BORER_PUBLIC_URL set to
# the tunnel's address (link previews need it), both as user services (scripts/detach.sh).
#   scripts/beta.sh                 start; a running tunnel is reused, so its links keep working
#   scripts/beta.sh restart-tunnel  new tunnel address: every link sent so far stops working
#   scripts/beta.sh status          what runs, the address, the counters command
#   scripts/beta.sh stop            stop server and tunnel (that ends every link)
set -euo pipefail
cd "$(dirname "$0")/.."
port="${BORER_PORT:-8000}" metrics="${TUNNEL_METRICS:-127.0.0.1:20241}"
counters="cd api && PYTHONPATH=src:../sim/src uv run python -m borer_api.admin counters"

# Every local curl has a timeout: under WSL mirrored networking a closed port can hang.
tunnel_url() {  # the running quick tunnel's https address, or nothing
  curl -sf -m 3 "http://$metrics/quicktunnel" | grep -o '[a-z0-9-]*\.trycloudflare\.com' \
    | head -1 | sed 's#^#https://#' || true
}

warn_links() {
  echo "WARNING: a new tunnel gives a new address. Every link sent so far (A's and B's"
  echo "  personal links, public cards, WhatsApp previews) stops working. Keep this tunnel"
  echo "  running for the whole beta; 'scripts/beta.sh' reuses it."
}

start_tunnel() {
  local out
  out=$(scripts/tunnel.sh) || { echo "$out" >&2; exit 1; }
  url=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' <<<"$out" | head -1)
  [ -n "$url" ] || { echo "No tunnel address in: $out" >&2; exit 1; }
}

start_server() {  # (re)start the server for $url; cases and links survive a server restart
  systemctl --user stop haborer 2>/dev/null || true
  mkdir -p api/data
  scripts/detach.sh haborer api/data/server.log env BORER_PUBLIC_URL="$url" \
    scripts/run_local.sh > /dev/null
  echo "Loading the fly brain..."
  for _ in $(seq 180); do
    if curl -sf -m 3 -o /dev/null "http://127.0.0.1:$port/"; then return 0; fi
    if ! systemctl --user is-active --quiet haborer; then break; fi
    sleep 1
  done
  echo "The server did not come up; last lines of api/data/server.log:" >&2
  tail -n 20 api/data/server.log >&2
  exit 1
}

case "${1:-start}" in
  stop)
    systemctl --user stop haborer haborer-tunnel 2>/dev/null || true
    echo "Stopped. Cases stay in api/data/cases.sqlite3 (7 days), but their links are dead:"
    echo "  the next tunnel has a new address."
    exit 0 ;;
  status)
    for u in haborer-tunnel haborer; do echo "$u: $(systemctl --user is-active "$u" || true)"; done
    echo "address: $(tunnel_url)"
    echo "counters: $counters"
    exit 0 ;;
  restart-tunnel)
    warn_links
    read -r -p "Type yes to get a new address: " answer
    [ "$answer" = yes ] || { echo "Nothing changed."; exit 1; }
    start_tunnel ;;
  start)
    url=""
    if systemctl --user is-active --quiet haborer-tunnel; then url=$(tunnel_url); fi
    if [ -n "$url" ]; then
      echo "Reusing the running tunnel: $url"
    else
      start_tunnel
    fi ;;
  *) sed -n '2,8p' "$0" >&2; exit 2 ;;
esac

start_server
cat <<EOF

HaBorer beta is up: $url
  Open a case from this address (never localhost): links and previews use it.
EOF
warn_links
cat <<EOF
  Keep the laptop on AC power, lid open and screen on: Modern Standby slows WSL ~8x.
  Anyone with the address can use the app while it runs.
  Logs: api/data/server.log, scripts/tunnel.sh log
  Counters: $counters
  Stop: scripts/beta.sh stop
EOF
