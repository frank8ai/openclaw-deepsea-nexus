#!/usr/bin/env bash
# Deep-Sea Nexus local doctor: one-click health check + auto-repair
set -u
set -o pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="repair"
RUN_QUICK_DEPLOY=1

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0
CHANGED_COUNT=0
NEEDS_LAUNCHD_RELOAD=0
NEEDS_GATEWAY_RESTART=0
VECTOR_COUNT=""

PLIST_PATH="${HOME}/Library/LaunchAgents/ai.openclaw.gateway.plist"
EXPECTED_VECTOR_DB="${NEXUS_VECTOR_DB:-${HOME}/.openclaw/workspace/memory/.vector_db_restored}"
EXPECTED_COLLECTION="${NEXUS_COLLECTION:-deepsea_nexus_restored}"
PYTHON_BIN=""
NEXUS_JSON=""

usage() {
  cat <<'EOF'
Usage: bash scripts/nexus_doctor_local.sh [--check|--repair] [--skip-deploy]

Options:
  --check        Read-only health checks only.
  --repair       Check + auto-fix (default).
  --skip-deploy  In repair mode, skip deploy_local_v4.sh --quick.
  -h, --help     Show this help.
EOF
}

info() { echo "[INFO] $*"; }
ok()   { PASS_COUNT=$((PASS_COUNT + 1)); echo "[PASS] $*"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); echo "[WARN] $*"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); echo "[FAIL] $*"; }
changed() { CHANGED_COUNT=$((CHANGED_COUNT + 1)); echo "[FIX ] $*"; }

need_cmd() {
  local cmd="$1"
  if command -v "${cmd}" >/dev/null 2>&1; then
    ok "command found: ${cmd}"
    return 0
  fi
  fail "missing command: ${cmd}"
  return 1
}

resolve_python() {
  if [[ -n "${NEXUS_PYTHON_PATH:-}" && -x "${NEXUS_PYTHON_PATH}" ]]; then
    PYTHON_BIN="${NEXUS_PYTHON_PATH}"
  elif [[ -x "${HOME}/miniconda3/envs/openclaw-nexus/bin/python" ]]; then
    PYTHON_BIN="${HOME}/miniconda3/envs/openclaw-nexus/bin/python"
  elif [[ -x "${ROOT_DIR}/.venv-3.13/bin/python" ]]; then
    PYTHON_BIN="${ROOT_DIR}/.venv-3.13/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  else
    PYTHON_BIN=""
  fi

  if [[ -n "${PYTHON_BIN}" ]]; then
    ok "python runtime: ${PYTHON_BIN}"
  else
    fail "python runtime not found"
  fi
}

plist_get_env() {
  local key="$1"
  /usr/libexec/PlistBuddy -c "Print :EnvironmentVariables:${key}" "${PLIST_PATH}" 2>/dev/null || true
}

plist_set_env() {
  local key="$1"
  local value="$2"
  /usr/libexec/PlistBuddy -c "Set :EnvironmentVariables:${key} ${value}" "${PLIST_PATH}" 2>/dev/null || \
    /usr/libexec/PlistBuddy -c "Add :EnvironmentVariables:${key} string ${value}" "${PLIST_PATH}"
}

ensure_launchagent_env() {
  if [[ ! -f "${PLIST_PATH}" ]]; then
    fail "launchagent plist not found: ${PLIST_PATH}"
    return
  fi
  ok "launchagent plist exists: ${PLIST_PATH}"

  local cur_python cur_db cur_collection
  cur_python="$(plist_get_env NEXUS_PYTHON_PATH)"
  cur_db="$(plist_get_env NEXUS_VECTOR_DB)"
  cur_collection="$(plist_get_env NEXUS_COLLECTION)"

  if [[ "${cur_python}" == "${PYTHON_BIN}" ]]; then
    ok "plist NEXUS_PYTHON_PATH is correct"
  elif [[ "${MODE}" == "repair" ]]; then
    plist_set_env NEXUS_PYTHON_PATH "${PYTHON_BIN}"
    changed "updated plist NEXUS_PYTHON_PATH"
    NEEDS_LAUNCHD_RELOAD=1
  else
    fail "plist NEXUS_PYTHON_PATH mismatch (current='${cur_python}')"
  fi

  if [[ "${cur_db}" == "${EXPECTED_VECTOR_DB}" ]]; then
    ok "plist NEXUS_VECTOR_DB is correct"
  elif [[ "${MODE}" == "repair" ]]; then
    plist_set_env NEXUS_VECTOR_DB "${EXPECTED_VECTOR_DB}"
    changed "updated plist NEXUS_VECTOR_DB"
    NEEDS_LAUNCHD_RELOAD=1
  else
    fail "plist NEXUS_VECTOR_DB mismatch (current='${cur_db}')"
  fi

  if [[ "${cur_collection}" == "${EXPECTED_COLLECTION}" ]]; then
    ok "plist NEXUS_COLLECTION is correct"
  elif [[ "${MODE}" == "repair" ]]; then
    plist_set_env NEXUS_COLLECTION "${EXPECTED_COLLECTION}"
    changed "updated plist NEXUS_COLLECTION"
    NEEDS_LAUNCHD_RELOAD=1
  else
    fail "plist NEXUS_COLLECTION mismatch (current='${cur_collection}')"
  fi
}

reload_launchagent_if_needed() {
  if [[ "${MODE}" != "repair" || "${NEEDS_LAUNCHD_RELOAD}" -ne 1 ]]; then
    return
  fi
  info "reloading launchagent to apply environment changes"
  launchctl unload "${PLIST_PATH}" >/dev/null 2>&1 || true
  launchctl load "${PLIST_PATH}" >/dev/null 2>&1 || true
  sleep 2
  changed "launchagent reloaded"
}

ensure_gateway_health() {
  local status
  status="$(openclaw gateway status 2>/dev/null || true)"
  if echo "${status}" | grep -q "Runtime: running" && echo "${status}" | grep -q "RPC probe: ok"; then
    ok "gateway runtime and rpc probe are healthy"
    return
  fi

  if [[ "${MODE}" != "repair" ]]; then
    fail "gateway is not healthy"
    return
  fi

  info "gateway not healthy, restarting"
  openclaw gateway restart >/dev/null 2>&1 || true
  sleep 3
  status="$(openclaw gateway status 2>/dev/null || true)"
  if echo "${status}" | grep -q "Runtime: running" && echo "${status}" | grep -q "RPC probe: ok"; then
    changed "gateway restarted and healthy"
  else
    fail "gateway still unhealthy after restart"
  fi
}

ensure_hook_ready() {
  local hook="$1"
  local hook_info
  hook_info="$(openclaw hooks info "${hook}" 2>/dev/null || true)"
  if echo "${hook_info}" | grep -q "✓ Ready"; then
    ok "hook ready: ${hook}"
    return
  fi

  if [[ "${MODE}" != "repair" ]]; then
    fail "hook not ready: ${hook}"
    return
  fi

  info "enabling hook: ${hook}"
  if openclaw hooks enable "${hook}" >/dev/null 2>&1; then
    hook_info="$(openclaw hooks info "${hook}" 2>/dev/null || true)"
    if echo "${hook_info}" | grep -q "✓ Ready"; then
      changed "hook enabled: ${hook}"
      NEEDS_GATEWAY_RESTART=1
      return
    fi
  fi
  fail "failed to enable hook: ${hook}"
}

ensure_recall_hook_not_duplicated() {
  local hooks_list
  hooks_list="$(openclaw hooks list 2>/dev/null || true)"
  local rag_line
  rag_line="$(echo "${hooks_list}" | grep "deepsea-rag-" || true)"
  if [[ -z "${rag_line}" ]]; then
    warn "cannot determine deepsea-rag-recall status"
    return
  fi

  if echo "${rag_line}" | grep -qi "disabled"; then
    ok "deepsea-rag-recall is disabled (no duplicate recall injection)"
    return
  fi

  if [[ "${MODE}" != "repair" ]]; then
    warn "deepsea-rag-recall is enabled; may duplicate memory injection"
    return
  fi

  if openclaw hooks disable deepsea-rag-recall >/dev/null 2>&1; then
    changed "disabled deepsea-rag-recall to avoid duplicate injection"
    NEEDS_GATEWAY_RESTART=1
  else
    warn "failed to disable deepsea-rag-recall"
  fi
}

restart_gateway_if_needed() {
  if [[ "${MODE}" != "repair" || "${NEEDS_GATEWAY_RESTART}" -ne 1 ]]; then
    return
  fi
  info "restarting gateway after hook updates"
  openclaw gateway restart >/dev/null 2>&1 || true
  sleep 3
  changed "gateway restarted for hook changes"
}

check_python_dependencies() {
  if [[ -z "${PYTHON_BIN}" ]]; then
    return
  fi
  local dep_out
  dep_out="$("${PYTHON_BIN}" - <<'PY'
import importlib
mods=["chromadb","sentence_transformers"]
states=[]
for name in mods:
    try:
        importlib.import_module(name)
        states.append(f"{name}=ok")
    except Exception:
        states.append(f"{name}=missing")
print(" ".join(states))
PY
)"
  if echo "${dep_out}" | grep -q "chromadb=ok"; then
    ok "python dependency chromadb available"
  else
    fail "python dependency chromadb missing"
  fi
  if echo "${dep_out}" | grep -q "sentence_transformers=ok"; then
    ok "python dependency sentence_transformers available"
  else
    warn "python dependency sentence_transformers missing (vector recall quality may degrade)"
  fi
}

check_nexus_health() {
  if [[ -z "${PYTHON_BIN}" ]]; then
    return
  fi
  export NEXUS_VECTOR_DB="${EXPECTED_VECTOR_DB}"
  export NEXUS_COLLECTION="${EXPECTED_COLLECTION}"

  local raw_output
  raw_output="$("${PYTHON_BIN}" - <<'PY'
import json
import os
import sys
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/skills"))

payload = {"ok": False}
try:
    from deepsea_nexus import nexus_init, nexus_health, nexus_stats
    init_ok = bool(nexus_init())
    health = nexus_health() if init_ok else {}
    stats = nexus_stats() if init_ok else {}
    payload = {
        "ok": init_ok and bool(health.get("available")),
        "init_ok": init_ok,
        "health_available": bool(health.get("available")),
        "health_documents": int(health.get("documents", 0)),
        "stats_documents": int(stats.get("total_documents", 0)),
        "stats_status": str(stats.get("status", "")),
    }
except Exception as exc:
    payload = {"ok": False, "error": str(exc)}

print(json.dumps(payload, ensure_ascii=True))
PY
)"

  # deepsea_nexus may print startup logs; keep the last JSON line only.
  NEXUS_JSON="$(printf '%s\n' "${raw_output}" | grep -E '^\{.*\}$' | tail -n 1)"
  if [[ -z "${NEXUS_JSON}" ]]; then
    fail "cannot parse nexus health payload"
    warn "raw output: ${raw_output}"
    return
  fi

  local parsed init_ok health_ok docs
  parsed="$("${PYTHON_BIN}" - "${NEXUS_JSON}" <<'PY'
import json,sys
raw = sys.argv[1]
try:
    obj=json.loads(raw)
    init_ok="true" if obj.get("init_ok") else "false"
    health_ok="true" if obj.get("ok") else "false"
    docs=str(obj.get("stats_documents", 0))
    print(f"{init_ok}|{health_ok}|{docs}")
except Exception:
    print("false|false|0")
PY
)"
  IFS='|' read -r init_ok health_ok docs <<< "${parsed}"

  if [[ "${init_ok}" == "true" ]]; then
    ok "nexus_init succeeded"
  else
    fail "nexus_init failed"
  fi

  if [[ "${health_ok}" == "true" ]]; then
    ok "nexus health available"
  else
    fail "nexus health unavailable"
  fi

  if [[ "${docs}" =~ ^[0-9]+$ ]] && [[ "${docs}" -gt 0 ]]; then
    ok "nexus API documents count: ${docs}"
  else
    warn "nexus API documents count is ${docs}"
  fi
}

check_vector_collection_count() {
  if [[ -z "${PYTHON_BIN}" ]]; then
    return
  fi
  VECTOR_COUNT="$("${PYTHON_BIN}" - <<'PY'
import os
import sys
count = "ERR"
try:
    import chromadb
    from chromadb.config import Settings
    db = os.environ.get("NEXUS_VECTOR_DB", "").strip()
    col = os.environ.get("NEXUS_COLLECTION", "").strip()
    client = chromadb.PersistentClient(
        path=db,
        settings=Settings(anonymized_telemetry=False),
        tenant="default_tenant",
        database="default_database",
    )
    collection = client.get_collection(col)
    count = str(collection.count())
except Exception:
    pass
print(count)
PY
)"

  if [[ "${VECTOR_COUNT}" =~ ^[0-9]+$ ]]; then
    if [[ "${VECTOR_COUNT}" -gt 0 ]]; then
      ok "vector DB count (${EXPECTED_COLLECTION}): ${VECTOR_COUNT}"
    else
      warn "vector DB count is 0 for ${EXPECTED_COLLECTION}"
    fi
  else
    fail "cannot read vector DB count for ${EXPECTED_COLLECTION}"
  fi
}

run_quick_deploy_if_needed() {
  if [[ "${MODE}" != "repair" || "${RUN_QUICK_DEPLOY}" -ne 1 ]]; then
    return
  fi
  info "running deploy_local_v4.sh --quick"
  if NEXUS_PYTHON_PATH="${PYTHON_BIN}" \
    NEXUS_VECTOR_DB="${EXPECTED_VECTOR_DB}" \
    NEXUS_COLLECTION="${EXPECTED_COLLECTION}" \
    bash "${ROOT_DIR}/scripts/deploy_local_v4.sh" --quick >/tmp/nexus_doctor_deploy.out 2>/tmp/nexus_doctor_deploy.err; then
    changed "quick deploy check passed"
  else
    fail "quick deploy check failed (see /tmp/nexus_doctor_deploy.err)"
  fi
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --check)
        MODE="check"
        shift
        ;;
      --repair)
        MODE="repair"
        shift
        ;;
      --skip-deploy)
        RUN_QUICK_DEPLOY=0
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "Unknown argument: $1"
        usage
        exit 1
        ;;
    esac
  done
}

main() {
  parse_args "$@"

  info "Deep-Sea Nexus local doctor mode=${MODE}"
  info "expected vector db: ${EXPECTED_VECTOR_DB}"
  info "expected collection: ${EXPECTED_COLLECTION}"

  need_cmd openclaw || true
  need_cmd launchctl || true
  need_cmd /usr/libexec/PlistBuddy || true

  resolve_python
  check_python_dependencies
  ensure_launchagent_env
  reload_launchagent_if_needed
  ensure_gateway_health
  ensure_hook_ready context-optimizer
  ensure_hook_ready nexus-auto-recall
  ensure_hook_ready nexus-auto-save
  ensure_recall_hook_not_duplicated
  restart_gateway_if_needed
  run_quick_deploy_if_needed
  check_nexus_health
  check_vector_collection_count

  echo
  echo "=== Deep-Sea Nexus Local Doctor Summary ==="
  echo "mode=${MODE} pass=${PASS_COUNT} warn=${WARN_COUNT} fail=${FAIL_COUNT} changed=${CHANGED_COUNT}"
  echo "python=${PYTHON_BIN:-N/A}"
  echo "vector_db=${EXPECTED_VECTOR_DB}"
  echo "collection=${EXPECTED_COLLECTION}"
  if [[ -n "${VECTOR_COUNT}" ]]; then
    echo "vector_count=${VECTOR_COUNT}"
  fi

  if [[ "${FAIL_COUNT}" -gt 0 ]]; then
    exit 1
  fi
  exit 0
}

main "$@"
