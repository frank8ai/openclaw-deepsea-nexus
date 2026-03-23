#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OPENCLAW_HOME_DIR="${OPENCLAW_HOME:-${HOME}/.openclaw}"
infer_workspace_dir() {
  if [[ -n "${OPENCLAW_WORKSPACE:-}" ]]; then
    printf '%s\n' "${OPENCLAW_WORKSPACE}"
    return
  fi

  if [[ "$(basename "${ROOT_DIR}")" == "deepsea-nexus" ]] && [[ "$(basename "$(dirname "${ROOT_DIR}")")" == "skills" ]]; then
    printf '%s\n' "$(dirname "$(dirname "${ROOT_DIR}")")"
    return
  fi

  printf '%s\n' "${OPENCLAW_HOME_DIR}/workspace"
}

OPENCLAW_WORKSPACE_DIR="$(infer_workspace_dir)"
if [[ -n "${NEXUS_PYTHON_PATH:-}" && -x "${NEXUS_PYTHON_PATH}" ]]; then
  PYTHON_BIN="${NEXUS_PYTHON_PATH}"
elif [[ -x "${ROOT_DIR}/.venv-3.13/bin/python" ]]; then
  PYTHON_BIN="${ROOT_DIR}/.venv-3.13/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
elif [[ -x "${HOME}/miniconda3/envs/openclaw-nexus/bin/python" ]]; then
  PYTHON_BIN="${HOME}/miniconda3/envs/openclaw-nexus/bin/python"
else
  PYTHON_BIN="${NEXUS_PYTHON_PATH:-python3}"
fi

MODE="--full"
BENCH_CASES="${ROOT_DIR}/docs/memory_v5_benchmark_sample.json"
RUN_LIFECYCLE_AUDIT=0
LIFECYCLE_ALL_AGENTS=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --full|--quick)
      MODE="$1"
      shift
      ;;
    --with-lifecycle-audit)
      RUN_LIFECYCLE_AUDIT=1
      shift
      ;;
    --lifecycle-all-agents)
      RUN_LIFECYCLE_AUDIT=1
      LIFECYCLE_ALL_AGENTS=1
      shift
      ;;
    --benchmark-cases)
      if [[ $# -lt 2 ]]; then
        echo "[deploy] missing value for --benchmark-cases" >&2
        exit 2
      fi
      BENCH_CASES="$2"
      shift 2
      ;;
    --help|-h)
      cat <<'EOF'
Usage: bash scripts/deploy_local_v5.sh [--full|--quick] [benchmark_cases.json]
       [--benchmark-cases <path>] [--with-lifecycle-audit] [--lifecycle-all-agents]

Options:
  --full                  Run full test gate before smoke/benchmark (default)
  --quick                 Run memory_v5 focused tests before smoke/benchmark
  --benchmark-cases PATH  Override benchmark case pack
  --with-lifecycle-audit  Run memory_v5 lifecycle maintenance in dry-run report mode
  --lifecycle-all-agents  Same as above, but audit all discovered Memory v5 scopes
EOF
      exit 0
      ;;
    *)
      if [[ "$1" == --* ]]; then
        echo "[deploy] unknown option: $1" >&2
        exit 2
      fi
      BENCH_CASES="$1"
      shift
      ;;
  esac
done

NEXUS_VECTOR_DB_VALUE="${NEXUS_VECTOR_DB:-${OPENCLAW_WORKSPACE_DIR}/memory/.vector_db_restored}"
NEXUS_COLLECTION_VALUE="${NEXUS_COLLECTION:-deepsea_nexus_restored}"

echo "[deploy] Deep-Sea Nexus local deploy (v5.5.0)"
echo "[deploy] root=${ROOT_DIR}"
echo "[deploy] python=${PYTHON_BIN}"
echo "[deploy] workspace=${OPENCLAW_WORKSPACE_DIR}"
echo "[deploy] vector_db=${NEXUS_VECTOR_DB_VALUE}"
echo "[deploy] collection=${NEXUS_COLLECTION_VALUE}"
echo "[deploy] benchmark_cases=${BENCH_CASES}"
echo "[deploy] lifecycle_audit=${RUN_LIFECYCLE_AUDIT}"
echo "[deploy] lifecycle_all_agents=${LIFECYCLE_ALL_AGENTS}"

cd "${ROOT_DIR}"

run_py() {
  set +e
  env -u OPENCLAW_WORKSPACE -u NEXUS_VECTOR_DB -u NEXUS_COLLECTION "${PYTHON_BIN}" "$@"
  rc=$?
  set -e
  if [[ ${rc} -eq 0 ]]; then
    return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    FALLBACK_PY="$(command -v python3)"
    if [[ "${FALLBACK_PY}" != "${PYTHON_BIN}" ]]; then
      echo "[deploy] primary python failed (rc=${rc}), fallback -> ${FALLBACK_PY}"
      env -u OPENCLAW_WORKSPACE -u NEXUS_VECTOR_DB -u NEXUS_COLLECTION "${FALLBACK_PY}" "$@"
      fb_rc=$?
      if [[ ${fb_rc} -eq 0 ]]; then
        PYTHON_BIN="${FALLBACK_PY}"
      fi
      return ${fb_rc}
    fi
  fi
  return ${rc}
}

run_py_runtime() {
  local -a env_args=(
    "OPENCLAW_WORKSPACE=${OPENCLAW_WORKSPACE_DIR}"
    "NEXUS_VECTOR_DB=${NEXUS_VECTOR_DB_VALUE}"
    "NEXUS_COLLECTION=${NEXUS_COLLECTION_VALUE}"
  )

  set +e
  env "${env_args[@]}" "${PYTHON_BIN}" "$@"
  rc=$?
  set -e
  if [[ ${rc} -eq 0 ]]; then
    return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    FALLBACK_PY="$(command -v python3)"
    if [[ "${FALLBACK_PY}" != "${PYTHON_BIN}" ]]; then
      echo "[deploy] primary python failed (rc=${rc}), fallback -> ${FALLBACK_PY}"
      env "${env_args[@]}" "${FALLBACK_PY}" "$@"
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
run_py_runtime - <<'PY'
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
run_py_runtime scripts/memory_v5_smoke.py

echo "[deploy] memory_v5 benchmark"
BENCH_JSON="$(run_py_runtime scripts/memory_v5_benchmark.py --cases "${BENCH_CASES}" --all-agents)"
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

if [[ "${RUN_LIFECYCLE_AUDIT}" == "1" ]]; then
  echo "[deploy] memory_v5 lifecycle audit"
  MAINTENANCE_ARGS=("scripts/memory_v5_maintenance.py" "--dry-run" "--write-report")
  if [[ "${LIFECYCLE_ALL_AGENTS}" == "1" ]]; then
    MAINTENANCE_ARGS+=("--all-agents")
  fi
  run_py_runtime "${MAINTENANCE_ARGS[@]}"
fi

echo "[deploy] done"
