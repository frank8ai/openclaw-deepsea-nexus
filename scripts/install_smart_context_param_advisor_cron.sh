#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OPENCLAW_HOME="${OPENCLAW_HOME:-$HOME/.openclaw}"
WORKSPACE_ROOT="${OPENCLAW_WORKSPACE:-${OPENCLAW_HOME}/workspace}"
LOG_DIR="${WORKSPACE_ROOT}/logs"
BEGIN_MARKER="# BEGIN smart-context-param-advisor"
END_MARKER="# END smart-context-param-advisor"

PYTHON_BIN=""
if [[ -n "${NEXUS_PYTHON_PATH:-}" && -x "${NEXUS_PYTHON_PATH}" ]]; then
  PYTHON_BIN="${NEXUS_PYTHON_PATH}"
elif [[ -x "${ROOT_DIR}/.venv-3.13/bin/python" ]]; then
  PYTHON_BIN="${ROOT_DIR}/.venv-3.13/bin/python"
elif [[ -x "${WORKSPACE_ROOT}/.venv-nexus/bin/python3" ]]; then
  PYTHON_BIN="${WORKSPACE_ROOT}/.venv-nexus/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  echo "no python runtime found"
  exit 1
fi

mkdir -p "${LOG_DIR}"
JOB_LINE="20 9 * * * cd ${ROOT_DIR} && ${PYTHON_BIN} scripts/smart_context_param_advisor.py --lookback-hours 72 --min-events 4 >> ${LOG_DIR}/smart_context_param_advisor.cron.log 2>&1"

tmp_current="$(mktemp)"
tmp_new="$(mktemp)"

if crontab -l >"${tmp_current}" 2>/dev/null; then
  :
else
  : >"${tmp_current}"
fi

sed "/${BEGIN_MARKER}/,/${END_MARKER}/d" "${tmp_current}" >"${tmp_new}"

{
  cat "${tmp_new}"
  echo "${BEGIN_MARKER}"
  echo "${JOB_LINE}"
  echo "${END_MARKER}"
} | crontab -

rm -f "${tmp_current}" "${tmp_new}"
echo "[ok] installed daily smart-context advisor cron"
