#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OPENCLAW_HOME_DIR="${OPENCLAW_HOME:-$HOME/.openclaw}"
OPENCLAW_WORKSPACE_DIR="${OPENCLAW_WORKSPACE:-${OPENCLAW_HOME_DIR}/workspace}"

PYTHON_BIN="${NEXUS_PYTHON_PATH:-}"
if [[ -n "${PYTHON_BIN}" && -x "${PYTHON_BIN}" ]]; then
  :
elif [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
  PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
elif [[ -x "${ROOT_DIR}/.venv-3.13/bin/python" ]]; then
  PYTHON_BIN="${ROOT_DIR}/.venv-3.13/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  echo "python3 not found" >&2
  exit 1
fi

export OPENCLAW_HOME="${OPENCLAW_HOME_DIR}"
export OPENCLAW_WORKSPACE="${OPENCLAW_WORKSPACE_DIR}"

HOOK_SCRIPT="${ROOT_DIR}/hooks/post-response/auto_save_summary.py"
if [[ ! -f "${HOOK_SCRIPT}" ]]; then
  exit 0
fi

exec "${PYTHON_BIN}" "${HOOK_SCRIPT}"
