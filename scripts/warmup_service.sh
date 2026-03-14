#!/usr/bin/env bash
set -euo pipefail

# 后台预热服务 - 启动当前仓库内的 warmup daemon
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OPENCLAW_HOME_DIR="${OPENCLAW_HOME:-$HOME/.openclaw}"
OPENCLAW_WORKSPACE_DIR="${OPENCLAW_WORKSPACE:-${OPENCLAW_HOME_DIR}/workspace}"
SCRIPT_PATH="${NEXUS_WARMUP_SCRIPT:-${ROOT_DIR}/scripts/warmup_daemon.py}"
LOG_PATH="${NEXUS_WARMUP_LOG:-${OPENCLAW_WORKSPACE_DIR}/logs/nexus_warmup.log}"

PYTHON_BIN=""
if [[ -n "${NEXUS_PYTHON_PATH:-}" && -x "${NEXUS_PYTHON_PATH}" ]]; then
  PYTHON_BIN="${NEXUS_PYTHON_PATH}"
elif [[ -x "${ROOT_DIR}/.venv-3.13/bin/python" ]]; then
  PYTHON_BIN="${ROOT_DIR}/.venv-3.13/bin/python"
elif [[ -x "${OPENCLAW_WORKSPACE_DIR}/.venv-nexus/bin/python3" ]]; then
  PYTHON_BIN="${OPENCLAW_WORKSPACE_DIR}/.venv-nexus/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  echo "no python runtime found"
  exit 1
fi

mkdir -p "$(dirname "${LOG_PATH}")"
export DEEPSEA_NEXUS_ROOT="${DEEPSEA_NEXUS_ROOT:-${ROOT_DIR}}"
export OPENCLAW_WORKSPACE="${OPENCLAW_WORKSPACE_DIR}"

echo "$(date): 启动预热服务 ${SCRIPT_PATH}" >> "${LOG_PATH}"
exec "${PYTHON_BIN}" "${SCRIPT_PATH}" >> "${LOG_PATH}" 2>&1
