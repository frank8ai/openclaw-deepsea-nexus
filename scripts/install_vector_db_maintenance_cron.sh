#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SNAPSHOT_SCRIPT="${ROOT_DIR}/scripts/vector_db_snapshot.py"
HEALTH_SCRIPT="${ROOT_DIR}/scripts/vector_db_healthcheck.py"

if [[ ! -f "${SNAPSHOT_SCRIPT}" || ! -f "${HEALTH_SCRIPT}" ]]; then
  echo "missing scripts"
  exit 1
fi

PYTHON_BIN=""
if [[ -n "${NEXUS_PYTHON_PATH:-}" && -x "${NEXUS_PYTHON_PATH}" ]]; then
  PYTHON_BIN="${NEXUS_PYTHON_PATH}"
elif [[ -x "${HOME}/miniconda3/envs/openclaw-nexus/bin/python" ]]; then
  PYTHON_BIN="${HOME}/miniconda3/envs/openclaw-nexus/bin/python"
elif [[ -x "${HOME}/.openclaw/workspace/.venv-nexus/bin/python3" ]]; then
  PYTHON_BIN="${HOME}/.openclaw/workspace/.venv-nexus/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  echo "no python runtime found"
  exit 1
fi

CRON_LINE_SNAPSHOT="15 3 * * * NEXUS_VECTOR_DB=${NEXUS_VECTOR_DB:-$HOME/.openclaw/workspace/memory/.vector_db_restored} NEXUS_COLLECTION=${NEXUS_COLLECTION:-deepsea_nexus_restored} ${PYTHON_BIN} ${SNAPSHOT_SCRIPT} >> ${HOME}/.openclaw/workspace/logs/vector_db_snapshot.log 2>&1"
CRON_LINE_HEALTH="35 3 * * * NEXUS_VECTOR_DB=${NEXUS_VECTOR_DB:-$HOME/.openclaw/workspace/memory/.vector_db_restored} NEXUS_COLLECTION=${NEXUS_COLLECTION:-deepsea_nexus_restored} ${PYTHON_BIN} ${HEALTH_SCRIPT} --min-count 1 --auto-restore >> ${HOME}/.openclaw/workspace/logs/vector_db_healthcheck.log 2>&1"

MARK_BEGIN="# BEGIN deepsea-nexus-vector-db"
MARK_END="# END deepsea-nexus-vector-db"

CRONTAB_TMP="$(mktemp)"
crontab -l 2>/dev/null | sed "/${MARK_BEGIN}/,/${MARK_END}/d" > "${CRONTAB_TMP}" || true

{
  echo "${MARK_BEGIN}"
  echo "${CRON_LINE_SNAPSHOT}"
  echo "${CRON_LINE_HEALTH}"
  echo "${MARK_END}"
} >> "${CRONTAB_TMP}"

crontab "${CRONTAB_TMP}"
rm -f "${CRONTAB_TMP}"

echo "installed vector db maintenance cron block"
