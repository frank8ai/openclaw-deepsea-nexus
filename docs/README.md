# OpenClaw Deep-Sea Nexus Docs Guide

Last updated: 2026-03-14

This file is the documentation entrypoint for the current `v5.0.0` release
pack.

Current release state:

- `v5.0.0` official release baseline
- release note:
  - `releases/V5_0_0_OFFICIAL_2026-03-14.md`

## Document Model

Current docs are split into four layers:

- Product
  - what the product is
  - who it serves
  - what it currently promises
- Technical
  - how the current runtime is shaped
  - which interfaces are public
  - which modules are current vs compatibility
- Operations and Governance
  - how to deploy, verify, and operate it
  - which context policy is current
- Archive
  - historical design notes, older PRDs, migration archaeology

## Start Here

- Product source of truth:
  - `product/README.md`
- Technical source of truth:
  - `TECHNICAL_OVERVIEW_CURRENT.md`
  - `ARCHITECTURE_CURRENT.md`
  - `API_CURRENT.md`
- Operations and governance source of truth:
  - `LOCAL_DEPLOY.md`
  - `sop/Context_Policy_v2_EventDriven.md`
  - `sop/Execution_Governor_Context_Management_v1.3_Integration.md`

## Read By Task

### Understand the product

- `product/README.md`
- `product/positioning.md`
- `product/capabilities.md`
- `product/users-and-use-cases.md`
- `product/roadmap.md`

### Understand the current system

- `TECHNICAL_OVERVIEW_CURRENT.md`
- `ARCHITECTURE_CURRENT.md`
- `API_CURRENT.md`

### Understand context governance

- `sop/Context_Policy_v2_EventDriven.md`
- `sop/Execution_Governor_Context_Management_v1.3_Integration.md`
- `sop/SmartContext_Effectiveness_Path.md`

### Deploy or verify locally

- `LOCAL_DEPLOY.md`
- `../scripts/deploy_local_v5.sh`
- `../scripts/nexus_doctor_local.sh`
- `../scripts/memory_v5_smoke.py`

## English Docs

English docs are intentionally minimal in the current release pack:

- repository entry:
  - `../README_EN.md`
- product entry:
  - `product/README_EN.md`

Detailed current source of truth remains in Chinese.

## Archive / Reference-Only Docs

These documents remain in the repo for background context, but they are not
the current source of truth:

- `PRD.md`
- `USAGE_GUIDE.md`
- `architecture_v3.md`
- `SECOND_BRAIN_V5_PLAN.md`
- `SECOND_BRAIN_PARA.md`
- `SMART_CONTEXT_V4_4_0.md`
- `SMART_CONTEXT_V4_3_1.md`
- `CONTEXT_ENGINE.md`
- `AGENTS.md`
- `CLEANUP_v2_DUPLICATES.md`
- `SOP_MEMORY_GAP_ITERATION_2026-02-23.md`
- `SYSTEM_PROMPT_TEMPLATE.md`
- `sop/SmartContext_Coding_Compression_SOP_v2.md`
- `TASK_LIST.md`
- `TASK_PLAN_context_summary.md`
- `brainstorming_context_summary.md`

## Validation Baseline

Recommended local verification order:

```bash
python3 -m unittest tests.test_memory_v5 -v
python3 scripts/context_recall_scorecard.py --golden docs/evals/context_recall_golden_cases.json
python3 run_tests.py
bash scripts/nexus_doctor_local.sh --check --skip-deploy
python3 scripts/memory_v5_smoke.py
python3 scripts/memory_v5_maintenance.py --dry-run --write-report
```
