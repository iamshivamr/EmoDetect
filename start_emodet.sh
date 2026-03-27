#!/usr/bin/env bash
# Start EmoDetect: Jupyter Lab :8888, dashboard :8765, optional Cloudflare tunnel.
#
#   ./start_emodet.sh              # all services (tunnel needs cloudflared/config.yml)
#   ./start_emodet.sh --no-tunnel  # local only
#   ./start_emodet.sh stop         # stop processes started via this script (see logs/*.pid)
#
# Logs: logs/jupyter.log, logs/dashboard.log, logs/tunnel.log

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="${ROOT}/venv"
LOGDIR="${ROOT}/logs"
RUN_TUNNEL=1

usage() {
  cat <<'EOF'
Usage:
  start_emodet.sh              Start Jupyter Lab, dashboard, and Cloudflare tunnel
  start_emodet.sh --no-tunnel  Same without cloudflared
  start_emodet.sh stop         Stop services using PID files in logs/
  start_emodet.sh -h|--help    Show this help
EOF
}

stop_services() {
  local any=0
  for name in jupyter dashboard tunnel; do
    local f="${LOGDIR}/${name}.pid"
    if [[ -f "$f" ]]; then
      local pid
      pid="$(tr -d ' \n' <"$f" || true)"
      if [[ -n "${pid:-}" ]] && kill -0 "$pid" 2>/dev/null; then
        echo "Stopping ${name} (PID ${pid})"
        kill "$pid" 2>/dev/null || true
        any=1
      fi
      rm -f "$f"
    fi
  done
  if [[ "$any" -eq 0 ]]; then
    echo "No PID files found in ${LOGDIR} (nothing to stop)."
  fi
  exit 0
}

# Parse args (simple)
ARGS=()
for arg in "$@"; do
  case "$arg" in
    -h|--help)
      usage
      exit 0
      ;;
    --no-tunnel)
      RUN_TUNNEL=0
      ;;
    stop)
      ARGS+=("$arg")
      ;;
    *)
      echo "Unknown option: $arg" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ "${ARGS[0]:-}" == "stop" ]]; then
  mkdir -p "$LOGDIR"
  stop_services
fi

if [[ ! -d "$VENV" ]]; then
  echo "Missing venv at ${VENV}" >&2
  exit 1
fi

port_listening() {
  local port=$1
  lsof -i ":${port}" -sTCP:LISTEN -P >/dev/null 2>&1
}

mkdir -p "$LOGDIR"

if port_listening 8888; then
  echo "Port 8888 is already in use (Jupyter?). Stop it or run: $0 stop" >&2
  exit 1
fi
if port_listening 8765; then
  echo "Port 8765 is already in use (dashboard?). Stop it or run: $0 stop" >&2
  exit 1
fi

export PATH="${VENV}/bin:${PATH}"

echo "Starting Jupyter Lab → ${LOGDIR}/jupyter.log"
"${VENV}/bin/jupyter" lab --no-browser --ip=127.0.0.1 --port=8888 >>"${LOGDIR}/jupyter.log" 2>&1 &
echo $! >"${LOGDIR}/jupyter.pid"

echo "Starting dashboard → ${LOGDIR}/dashboard.log"
"${VENV}/bin/python" "${ROOT}/run_dashboard.py" >>"${LOGDIR}/dashboard.log" 2>&1 &
echo $! >"${LOGDIR}/dashboard.pid"

if [[ "$RUN_TUNNEL" -eq 1 ]]; then
  if ! command -v cloudflared >/dev/null 2>&1; then
    echo "cloudflared not found; skipping tunnel. Install: brew install cloudflared" >&2
    echo "  (Dashboard + Jupyter are running locally.)" >&2
  elif [[ ! -f "${ROOT}/cloudflared/config.yml" ]]; then
    echo "Missing cloudflared/config.yml; skipping tunnel. See cloudflared/SETUP.txt" >&2
  else
    echo "Starting Cloudflare tunnel → ${LOGDIR}/tunnel.log"
    bash "${ROOT}/cloudflared/run_tunnel.sh" >>"${LOGDIR}/tunnel.log" 2>&1 &
    echo $! >"${LOGDIR}/tunnel.pid"
  fi
fi

cat <<EOF

Running:
  Jupyter:   http://127.0.0.1:8888   (token in ${LOGDIR}/jupyter.log if needed)
  Dashboard: http://127.0.0.1:8765
  Stop:      ${ROOT}/start_emodet.sh stop
EOF
