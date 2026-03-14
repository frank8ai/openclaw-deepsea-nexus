# Deep-Sea Nexus v5.0.0

Local-first long-term memory and context-governance tooling for agent
workflows.

[简体中文](README.md)

Last updated: 2026-03-14

## What It Is

Deep-Sea Nexus is a local-first memory and context-governance layer for
Codex, OpenClaw, and similar agent workflows.

Its core idea is not "store unlimited raw chat history". The current product
model is:

- all memory first passes through context governance
- only important, structured, evidence-backed state should become durable memory
- recall / inject / compress / rescue / replay form one operational loop

## Current Source Map

- Repository entry:
  - `README.md`
- Docs entry:
  - `docs/README.md`
- Product docs:
  - `docs/product/README_EN.md`
  - `docs/product/README.md`
- Technical docs:
  - `docs/TECHNICAL_OVERVIEW_CURRENT.md`
  - `docs/ARCHITECTURE_CURRENT.md`
  - `docs/API_CURRENT.md`
- Operations and governance:
  - `docs/LOCAL_DEPLOY.md`
  - `docs/sop/Context_Policy_v2_EventDriven.md`

Detailed current source of truth remains in Chinese.

## Stable Current Capabilities

- backward-compatible sync API
- async runtime and plugin lifecycle
- Memory v5 scoped memory (`agent_id` / `user_id`)
- context-governed recall / inject / compress / rescue
- local deploy / doctor / smoke / benchmark workflows

## Validation

```bash
python3 -m unittest tests.test_memory_v5 -v
python3 run_tests.py
bash scripts/nexus_doctor_local.sh --check --skip-deploy
python3 scripts/memory_v5_smoke.py
```
