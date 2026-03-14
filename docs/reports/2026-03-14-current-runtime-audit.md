# Current Runtime Audit (2026-03-14)

## Scope

Audit target:

- current product/technical release pack
- SmartContext / ContextEngine / Memory v5 current runtime paths
- config defaults that influence context governance

Source of truth used in this audit:

- `docs/TECHNICAL_OVERVIEW_CURRENT.md`
- `docs/ARCHITECTURE_CURRENT.md`
- `docs/API_CURRENT.md`
- `docs/sop/Context_Policy_v2_EventDriven.md`
- `docs/sop/SmartContext_Daily_Tuning_and_RCA_2026-02-28.md`

## Findings

### 1. Decision blocks could enter durable memory without evidence

Problem:

- `plugins/smart_context.py` extracted `decision_block` entries from raw text and
  stored them directly.
- stored decision documents did not carry evidence pointers or replay commands.

Why this was wrong:

- current policy says `No Evidence, No Memory`
- compression output should drop decision text without evidence pointer

### 2. Runtime auto-tune defaults were still acting like hidden policy

Problem:

- `smart_context.inject_ratio_auto_tune` defaulted to enabled in runtime code
- `config.json` also had SmartContext and ContextEngine auto-tune writes enabled

Why this was wrong:

- current tuning SOP is report-only by default
- fixed governance should not drift through implicit runtime config rewrites

## Changes Landed

### A. Enforced evidence-aware decision storage

- `plugins/smart_context.py`
  - decision blocks now gather supporting `evidence_pointers` / `replay_commands`
  - if neither exists, durable decision-block writes are skipped with metrics
- `plugins/smart_context_graph.py`
  - stored decision-block documents now include:
    - `Decision: ...`
    - `Evidence: ...` when present
    - `Replay: ...` when present
- `plugins/smart_context_summary.py`
  - structured summary no longer carries `Decisions:` when no evidence/replay is
    available

### B. Restored report-first tuning defaults

- `plugins/smart_context_runtime.py`
  - runtime no longer auto-tunes unless config explicitly enables it
- `plugins/smart_context.py`
  - SmartContext default `inject_ratio_auto_tune` is now disabled
- `config.json`
  - `smart_context.inject_ratio_auto_tune = false`
  - `context_engine.auto_tune_enabled = false`

### C. Aligned ContextEngine compatibility assembly with current governance

- `plugins/context_engine.py`
  - compatibility retrieval now reuses `build_context_block()`
  - legacy `smart_retrieve()` / `inject_context()` / `resume_session()` no longer
    format a separate unmanaged recall block
  - current NOW rescue context is folded into the same budgeted assembly path

### D. Reduced current host-specific default paths

- runtime path defaults now prefer:
  - `OPENCLAW_WORKSPACE`
  - fallback `OPENCLAW_HOME`
- affected current runtime modules:
  - `runtime_paths.py`
  - `plugins/now_manager.py`
  - `write_guard.py`
  - `vector_store.py`
  - `plugins/session_manager.py`
  - `session_manager.py`
  - `plugins/flush_manager.py`
- current config defaults no longer pin `/Users/yizhi/...` absolute paths
  - `config.json`
  - `config.yaml`
- additional historical docs were explicitly marked archive/reference-only so
  they stop competing with the current release pack

### E. Reduced host-specific defaults in current operational entrypoints

- current entry scripts now prefer env-aware workspace resolution instead of one
  host path:
  - `scripts/deploy_local_v5.sh`
  - `scripts/nexus_doctor_local.sh`
  - `scripts/audit_recent_summaries.py`
- report output for `audit_recent_summaries.py` now defaults to the current repo
  `docs/reports/` path instead of assuming one OpenClaw workspace checkout
- additional archive banners were added to older plan/reference docs:
  - `docs/SECOND_BRAIN_V5_PLAN.md`
  - `docs/SECOND_BRAIN_PARA.md`

## Validation

Targeted validation:

```bash
python3 -m unittest \
  tests.test_memory_v5.TestSmartContextRuntimeState \
  tests.test_memory_v5.TestSmartContextPluginOrchestration \
  tests.test_memory_v5.TestSmartContextSummaryHelpers \
  tests.test_memory_v5.TestSmartContextGraphHelpers -v
python3 -m py_compile \
  plugins/smart_context.py \
  plugins/smart_context_runtime.py \
  plugins/smart_context_summary.py \
  plugins/smart_context_graph.py \
  tests/test_memory_v5.py
git diff --check
```

Full regression:

```bash
python3 run_tests.py
```

Result:

- all targeted tests passed
- full repo test suite passed

## Remaining Follow-Up Plan

### Next slice 1

Continue shrinking host-specific defaults in remaining non-core operational
entrypoints and maintenance scripts so the repo-wide defaults match the already
cleaned current runtime.

### Next slice 2

Separate current operational runbooks from remaining historical integration
notes that still describe older SmartContext / ContextEngine coupling.
