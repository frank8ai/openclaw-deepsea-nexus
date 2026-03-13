#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${NEXUS_PYTHON_PATH:-python3}"
MODE="${1:---install}"

CURRENT_BLOCK_ID="deepsea-nexus-smart-context-v5"
LEGACY_BLOCK_ID="deepsea-nexus-v4.4.0"
BEGIN_MARK="# BEGIN ${CURRENT_BLOCK_ID}"
END_MARK="# END ${CURRENT_BLOCK_ID}"
LEGACY_BEGIN_MARK="# BEGIN ${LEGACY_BLOCK_ID}"
LEGACY_END_MARK="# END ${LEGACY_BLOCK_ID}"

CRON_BLOCK=$(cat <<CRON
${BEGIN_MARK}
# Smart Context report-only digests (safe mode)
0 8 * * * cd ${ROOT_DIR} && ${PYTHON_BIN} scripts/smart_context_digest.py --mode morning >/tmp/deepsea_nexus_digest_morning.log 2>&1
30 11 * * * cd ${ROOT_DIR} && ${PYTHON_BIN} scripts/smart_context_digest.py --mode progress >/tmp/deepsea_nexus_digest_progress_1130.log 2>&1
30 17 * * * cd ${ROOT_DIR} && ${PYTHON_BIN} scripts/smart_context_digest.py --mode progress >/tmp/deepsea_nexus_digest_progress_1730.log 2>&1
0 3 * * * cd ${ROOT_DIR} && ${PYTHON_BIN} scripts/smart_context_digest.py --mode nightly >/tmp/deepsea_nexus_digest_nightly.log 2>&1
10 3 * * * cd ${ROOT_DIR} && ${PYTHON_BIN} scripts/flush_summaries.py >/tmp/deepsea_nexus_flush_summaries.log 2>&1
${END_MARK}
CRON
)

existing="$(crontab -l 2>/dev/null || true)"

strip_block() {
  local begin_mark="$1"
  local end_mark="$2"
  awk -v begin="$begin_mark" -v end="$end_mark" '
    $0==begin {skip=1; next}
    $0==end {skip=0; next}
    skip==0 {print}
  '
}

cleaned="$(printf '%s\n' "$existing" \
  | strip_block "$LEGACY_BEGIN_MARK" "$LEGACY_END_MARK" \
  | strip_block "$BEGIN_MARK" "$END_MARK")"

if [[ "$MODE" == "--remove" ]]; then
  printf '%s\n' "$cleaned" | crontab -
  echo "[cron] removed ${CURRENT_BLOCK_ID} block(s)"
  exit 0
fi

# install (default)
new_cron="$cleaned"
if [[ -n "$new_cron" ]]; then
  new_cron+=$'\n'
fi
new_cron+="$CRON_BLOCK"

printf '%s\n' "$new_cron" | crontab -
echo "[cron] installed ${CURRENT_BLOCK_ID} block"
crontab -l | sed -n "/${CURRENT_BLOCK_ID}/,+8p"
