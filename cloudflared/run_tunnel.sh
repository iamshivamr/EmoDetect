#!/usr/bin/env bash
# Run the Cloudflare named tunnel. Start Jupyter + dashboard locally first.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="${ROOT}/cloudflared/config.yml"

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "cloudflared not found. macOS: brew install cloudflared"
  exit 1
fi

if [[ ! -f "${CONFIG}" ]]; then
  echo "Missing ${CONFIG}"
  echo "  cp ${ROOT}/cloudflared/config.yml.example ${ROOT}/cloudflared/config.yml"
  echo "  Edit tunnel name, credentials-file path, and hostnames."
  exit 1
fi

exec cloudflared tunnel --config "${CONFIG}" run
