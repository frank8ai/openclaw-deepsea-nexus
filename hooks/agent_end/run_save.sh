#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OPENCLAW_HOME_DIR="${OPENCLAW_HOME:-$HOME/.openclaw}"
OPENCLAW_WORKSPACE_DIR="${OPENCLAW_WORKSPACE:-${OPENCLAW_HOME_DIR}/workspace}"

PYTHON_BIN=""
if [[ -n "${NEXUS_PYTHON_PATH:-}" && -x "${NEXUS_PYTHON_PATH}" ]]; then
  PYTHON_BIN="${NEXUS_PYTHON_PATH}"
elif [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
  PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
elif [[ -x "${ROOT_DIR}/.venv-3.13/bin/python" ]]; then
  PYTHON_BIN="${ROOT_DIR}/.venv-3.13/bin/python"
elif [[ -x "${OPENCLAW_WORKSPACE_DIR}/.venv-nexus/bin/python3" ]]; then
  PYTHON_BIN="${OPENCLAW_WORKSPACE_DIR}/.venv-nexus/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  exit 0
fi

export OPENCLAW_HOME="${OPENCLAW_HOME_DIR}"
export OPENCLAW_WORKSPACE="${OPENCLAW_WORKSPACE_DIR}"

HOOK_SCRIPT="${ROOT_DIR}/hooks/post-response/auto_save_summary.py"
if [[ ! -f "${HOOK_SCRIPT}" ]]; then
  exit 0
fi

# Best-effort hook wrapper for current runtime; do not block host flow.
"${PYTHON_BIN}" "${HOOK_SCRIPT}" >/dev/null 2>&1 || true
exit 0
