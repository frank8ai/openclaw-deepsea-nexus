#!/usr/bin/env bash
set -euo pipefail

BEGIN_MARKER="# BEGIN smart-context-param-advisor"
END_MARKER="# END smart-context-param-advisor"

JOB_LINE="20 9 * * * cd /Users/yizhi/.openclaw/workspace/skills/deepsea-nexus && ${NEXUS_PYTHON_PATH:-/Users/yizhi/miniconda3/envs/openclaw-nexus/bin/python} scripts/smart_context_param_advisor.py --lookback-hours 72 --min-events 4 >> /tmp/smart_context_param_advisor.cron.log 2>&1"

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
