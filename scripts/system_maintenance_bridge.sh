#!/usr/bin/env bash
set -euo pipefail

# Bridge script: run OpenClaw system maintenance steps under the deepsea-nexus nightly pipeline.
# This keeps a single orchestration source (deepsea-nexus cron) while maintenance logic lives in workspace-codex-cli.

OPENCLAW_HOME_DIR="${OPENCLAW_HOME:-$HOME/.openclaw}"
TARGET_DIR="${NEXUS_SYSTEM_MAINTENANCE_TARGET:-${OPENCLAW_HOME_DIR}/workspace-codex-cli}"

if [ ! -d "$TARGET_DIR" ]; then
  echo "ERROR: missing $TARGET_DIR" >&2
  exit 1
fi

cd "$TARGET_DIR"

if [ -x "scripts/maintenance.sh" ]; then
  bash scripts/maintenance.sh
fi

if [ -x "scripts/cognition-daily.sh" ]; then
  bash scripts/cognition-daily.sh
fi
