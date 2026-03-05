#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -n "${NEXUS_PYTHON_PATH:-}" && -x "${NEXUS_PYTHON_PATH}" ]]; then
  PYTHON_BIN="${NEXUS_PYTHON_PATH}"
elif [[ -x "${HOME}/.openclaw/workspace/skills/deepsea-nexus/.venv-3.13/bin/python" ]]; then
  PYTHON_BIN="${HOME}/.openclaw/workspace/skills/deepsea-nexus/.venv-3.13/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
elif [[ -x "${HOME}/miniconda3/envs/openclaw-nexus/bin/python" ]]; then
  PYTHON_BIN="${HOME}/miniconda3/envs/openclaw-nexus/bin/python"
else
  PYTHON_BIN="${NEXUS_PYTHON_PATH:-python3}"
fi

MODE="${1:---full}"
BENCH_CASES="${2:-${ROOT_DIR}/docs/memory_v5_benchmark_sample.json}"
export NEXUS_VECTOR_DB="${NEXUS_VECTOR_DB:-${HOME}/.openclaw/workspace/memory/.vector_db_restored}"
export NEXUS_COLLECTION="${NEXUS_COLLECTION:-deepsea_nexus_restored}"

echo "[deploy] Deep-Sea Nexus local deploy (v5.0.0)"
echo "[deploy] root=${ROOT_DIR}"
echo "[deploy] python=${PYTHON_BIN}"
echo "[deploy] vector_db=${NEXUS_VECTOR_DB}"
echo "[deploy] collection=${NEXUS_COLLECTION}"
echo "[deploy] benchmark_cases=${BENCH_CASES}"

cd "${ROOT_DIR}"

run_py() {
  set +e
  "${PYTHON_BIN}" "$@"
  rc=$?
  set -e
  if [[ ${rc} -eq 0 ]]; then
    return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    FALLBACK_PY="$(command -v python3)"
    if [[ "${FALLBACK_PY}" != "${PYTHON_BIN}" ]]; then
      echo "[deploy] primary python failed (rc=${rc}), fallback -> ${FALLBACK_PY}"
      "${FALLBACK_PY}" "$@"
      fb_rc=$?
      if [[ ${fb_rc} -eq 0 ]]; then
        PYTHON_BIN="${FALLBACK_PY}"
      fi
      return ${fb_rc}
    fi
  fi
  return ${rc}
}

if [[ "${MODE}" == "--quick" ]]; then
  echo "[deploy] quick mode: run memory_v5 focused tests"
  run_py tests/test_memory_v5.py -v
else
  echo "[deploy] full mode: run full test gate"
  run_py run_tests.py
fi

echo "[deploy] runtime smoke check"
run_py - <<'PY'
import json
import os
import sys

root = os.getcwd()
parent = os.path.dirname(root)
if parent not in sys.path:
    sys.path.insert(0, parent)

from deepsea_nexus import __version__ as pkg_version
from deepsea_nexus import nexus_health, nexus_init

ok = nexus_init()
if not ok:
    raise SystemExit("nexus_init failed")

health = nexus_health()
if not health.get("available"):
    raise SystemExit("nexus unavailable")
if not health.get("initialized"):
    raise SystemExit("nexus plugin not initialized")

print(
    json.dumps(
        {
            "available": bool(health.get("available")),
            "initialized": bool(health.get("initialized")),
            "documents": int(health.get("documents", 0)),
            "plugin_version": health.get("version"),
            "package_version": pkg_version,
        },
        ensure_ascii=False,
    )
)
PY

echo "[deploy] memory_v5 smoke"
run_py scripts/memory_v5_smoke.py

echo "[deploy] memory_v5 benchmark"
BENCH_JSON="$(run_py scripts/memory_v5_benchmark.py --cases "${BENCH_CASES}" --all-agents)"
echo "${BENCH_JSON}"
run_py - "${BENCH_JSON}" <<'PY'
import json
import sys

raw = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
if not raw:
    raise SystemExit("benchmark output is empty")
data = json.loads(raw)
cases = int(data.get("case_count", 0) or 0)
any_hit = int(data.get("any_scope_hit", 0) or 0)
if cases > 0 and any_hit <= 0:
    raise SystemExit("memory_v5 benchmark indicates zero global hit; deployment blocked")
PY

echo "[deploy] done"
