#!/usr/bin/env bash
set -euo pipefail

# Health OS OpenClaw installer (single machine)
# Usage:
#   ./install.sh --workspace /path/to/openclaw/workspace [--openai-api-key sk-...] [--model openai/gpt-5.4]

WORKSPACE=""
OPENAI_API_KEY=""
MODEL="openai/gpt-5.4"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace)
      WORKSPACE="$2"; shift 2;;
    --openai-api-key)
      OPENAI_API_KEY="$2"; shift 2;;
    --model)
      MODEL="$2"; shift 2;;
    -h|--help)
      sed -n '1,120p' "$0"; exit 0;;
    *)
      echo "Unknown arg: $1" >&2; exit 2;;
  esac
done

if [[ -z "$WORKSPACE" ]]; then
  # Heuristic: if the current directory contains skills/ and openclaw state folder nearby.
  if [[ -d "./skills" && -d "./state" ]]; then
    WORKSPACE="$(pwd)"
  else
    echo "Error: --workspace is required (path to OpenClaw workspace root)." >&2
    exit 2
  fi
fi

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$WORKSPACE/skills" "$WORKSPACE/health-os"

# Copy skill (overwrites existing files with the packaged version)
rm -rf "$WORKSPACE/skills/health-os"
cp -R "$SRC_DIR/skills/health-os" "$WORKSPACE/skills/health-os"

# Copy health-os templates + structure
rm -rf "$WORKSPACE/health-os"
cp -R "$SRC_DIR/health-os" "$WORKSPACE/health-os"

echo "Installed files into: $WORKSPACE"

if command -v openclaw >/dev/null 2>&1; then
  if [[ -n "$OPENAI_API_KEY" ]]; then
    echo "Configuring OpenAI via OpenClaw onboard..."
    OPENAI_API_KEY="$OPENAI_API_KEY" openclaw onboard --openai-api-key "$OPENAI_API_KEY" >/dev/null
    echo "Setting default model to: $MODEL"
    openclaw config set agents.defaults.model.primary "$MODEL" || true
  else
    echo "OpenClaw detected. To configure OpenAI, run one of:"
    echo "  openclaw onboard --auth-choice openai-api-key"
    echo "  openclaw onboard --openai-api-key \"\$OPENAI_API_KEY\""
  fi

  echo "If needed, restart the gateway:" 
  echo "  openclaw gateway restart"
else
  echo "Note: openclaw CLI not found on PATH. Install/configure OpenClaw, then restart." >&2
fi

