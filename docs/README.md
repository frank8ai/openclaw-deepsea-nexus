# Deep-Sea Nexus Docs Guide

Last updated: 2026-03-14

This file is the documentation entrypoint for the current `v5.0.0` repository
state.

## Start Here

- Current product docs source of truth: `product/README.md`
- Current architecture source of truth: `ARCHITECTURE_CURRENT.md`
- Current public API surface: `API_CURRENT.md`
- Current context-governance source of truth: `sop/Context_Policy_v2_EventDriven.md`
- Main repository overview:
  - `../README.md`
  - `../README_EN.md`

## Current Product Docs

- Product docs index: `product/README.md`
- Product docs index (English): `product/README_EN.md`
- Positioning: `product/positioning.md`
- Users and use cases: `product/users-and-use-cases.md`
- Capabilities and scope: `product/capabilities.md`
- Product roadmap: `product/roadmap.md`

## Current Runtime Guides

- Local deploy and runtime checks: `LOCAL_DEPLOY.md`
- Context-governance policy:
  - `sop/Context_Policy_v2_EventDriven.md`
- Context-governance integration:
  - `sop/Execution_Governor_Context_Management_v1.3_Integration.md`
- SmartContext operating guidance:
  - `sop/SmartContext_Daily_Tuning_and_RCA_2026-02-28.md`
  - `sop/SmartContext_Effectiveness_Path.md`

## Historical Or Reference-Only Docs

These remain in the repo for background context, but they are not the current
runtime source of truth:

- `../DOCUMENTATION.md`
- `../AUTO_SUMMARY_INTEGRATION.md`
- `../SOP_INDEX.md`
- `../CHANGELOG.md`
- `../benchmark.txt`
- `AGENTS.md`
- `PRD.md`
- `examples_v3.md`
- `architecture_v3.md`
- `USAGE_GUIDE.md`
- `SECOND_BRAIN_V5_PLAN.md`
- `SECOND_BRAIN_PARA.md`
- `SMART_CONTEXT_V4_4_0.md`
- `SMART_CONTEXT_V4_3_1.md`
- `sop/SmartContext_Coding_Compression_SOP_v2.md`
- `TASK_LIST.md`
- `TASK_PLAN_context_summary.md`
- `brainstorming_context_summary.md`

## Practical Validation

Recommended local validation order:

```bash
python3 tests/test_memory_v5.py -v
python3 run_tests.py
python3 scripts/archive_repo_runtime_data.py --apply --include-stale-venv --json
PYTHONDONTWRITEBYTECODE=1 python3 scripts/archive_repo_runtime_data.py --json
```

What this checks:

- focused Memory v5 and SmartContext regression coverage
- broader package/runtime regression coverage
- repo-tree cleanup of generated runtime artifacts
- confirmation that no runtime artifacts remain inside the repo tree

## Repo Notes

- Current SmartContext refactor work moved shared logic into:
  - `plugins/smart_context_round.py`
  - `plugins/smart_context_summary.py`
  - `plugins/smart_context_conversation.py`
  - `plugins/smart_context_prompt.py`
  - `plugins/smart_context_now.py`
  - `plugins/smart_context_adaptive.py`
  - `plugins/smart_context_recall.py`
  - `plugins/smart_context_inject.py`
- Runtime cleanup archives are written outside the repo to:
  - `~/.openclaw-runtime/archive/deepsea-nexus/`
