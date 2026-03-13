# Deep-Sea Nexus Product Docs

Last updated: 2026-03-13

This file is the English entrypoint for the current product narrative.

## What It Is

Deep-Sea Nexus is a local-first memory and context-governance layer for agent
workflows. It helps Codex, OpenClaw, and similar local agent setups keep
durable memory, scoped recall, and observable context behavior across
long-running tasks and repeated sessions.

## Read In This Order

1. English product docs index: `README_EN.md`
2. Chinese product docs index: `README.md`
3. Positioning (Chinese): `positioning.md`
4. Users and use cases (Chinese): `users-and-use-cases.md`
5. Capabilities and scope (Chinese): `capabilities.md`
6. Roadmap (Chinese): `roadmap.md`

## Current Source Map

- Product docs:
  - `README_EN.md`
  - `README.md`
- Technical docs:
  - `../ARCHITECTURE_CURRENT.md`
  - `../API_CURRENT.md`
- Operational docs:
  - `../LOCAL_DEPLOY.md`
  - `../sop/Execution_Governor_Context_Management_v1.3_Integration.md`

## Product Summary

Current stable promises:

- backward-compatible sync API for existing automation
- async runtime and plugin lifecycle
- Memory v5 scoped memory (`agent_id` / `user_id`)
- local deploy / doctor / smoke / benchmark workflows
- gradual migration instead of rewrite-only adoption

Current non-goals:

- hosted SaaS product
- team collaboration platform
- multi-tenant cloud memory service
- generic enterprise knowledge platform
