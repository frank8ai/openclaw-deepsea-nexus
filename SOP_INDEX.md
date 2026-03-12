# SOP Index

## OpenClaw Closed-Loop Router (Local)
- Router SOP (risk routing + evidence contract): `docs/sop/closed-loop-router.md`
- Minimal SOP (local copy): `docs/sop/closed-loop-minimal.md`
- Production SOP (local copy): `docs/sop/closed-loop-production.md`
- Comparison note (local copy): `docs/sop/closed-loop-comparison.md`
- Minimal subagent template (local copy): `docs/sop/min_loop_subagent_template.md`

Notes:
- These are local workspace assets under `/Users/yizhi/.openclaw/workspace-coder` and are meant to be referenced by agents running in this repo.

## SmartContext Ops (2026-02-28)
- RCA + daily tuning SOP:
  - `docs/sop/SmartContext_Daily_Tuning_and_RCA_2026-02-28.md`
- Daily advisor script (report-only):
  - `scripts/smart_context_param_advisor.py`
- Cron install helper:
  - `scripts/install_smart_context_param_advisor_cron.sh`

## Catalog Entries
- `P0-SOP目录 v1`
  - File: `resources/sop/2026-02/2026-02-17-p0-sop-catalog.md`
  - Scope: 12 SOP
- `P1-SOP目录 v1`
  - File: `resources/sop/2026-02/2026-02-17-p1-sop-catalog.md`
  - Scope: 8 SOP
- `P2-SOP目录 v1`
  - File: `resources/sop/2026-02/2026-02-17-p2-sop-catalog.md`
  - Scope: 6 SOP
  - Acceptance: 6/6 strict pass (`python3 scripts/validate_sop_factory.py --sop <file> --strict`)

## Toolchain Iteration (Search SOP + Research SOP)
- External evidence pack:
  - `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- Full iteration report (29 SOP):
  - `resources/sop/2026-02/2026-02-17-all-sop-toolchain-iteration-report.md`
- Per-SOP research notes:
  - `resources/sop/2026-02/research-toolchain/`
- Acceptance:
  - 29/29 strict pass (`python3 scripts/validate_sop_factory.py --sop <file> --strict`)

## System SOP Operations Upgrade
- Active SOPs:
  - `resources/sop/2026-02/2026-02-17-postmortem-writeback-sop.md`
  - `resources/sop/2026-02/2026-02-17-multi-agent-research-merge-sop.md`
- One-page execution cards:
  - `resources/sop/2026-02/2026-02-17-postmortem-writeback-quick-card.md`
  - `resources/sop/2026-02/2026-02-17-multi-agent-research-merge-quick-card.md`
- Monthly KPI dashboard:
  - Script: `scripts/generate_sop_iteration_trends.py`
  - Output: `resources/sop/2026-02/2026-02-sop-iteration-kpi-dashboard.md`

## Governance V2 Upgrade (All SOP)
- Scope:
  - 31/31 SOP upgraded with non-compensatory highest standards and 4 hard mechanisms.
- Hard mechanisms applied:
  - Lifecycle fields (`Effective condition`, `Review cycle`, `Retirement condition`)
  - `Kill Switch` table
  - Dual-track metrics (`Result metric (primary)`, `Process metric (secondary)`, replacement rule)
  - `Auto-downgrade gate` (`active -> draft` when 2 consecutive monthly degradations)
- Retrieval-friendly layer:
  - Metadata fields: `Tags`, `Primary triggers`, `Primary outputs`
  - L0/L1 assets: 31 `.abstract.md` + 31 `.overview.md`
- Acceptance:
  - 31/31 strict pass (`python3 scripts/validate_sop_factory.py --sop <file> --strict`)

## Governance Routing + Writeback (2026-02-19)
- Canonical SOP:
  - `resources/sop/2026-02/2026-02-19-sop-governance-routing-writeback-sop.md`
- Scorecard:
  - `resources/sop/2026-02/2026-02-19-sop-governance-routing-writeback-scorecard.md`
- Iteration log:
  - `resources/sop/2026-02/2026-02-19-sop-governance-routing-writeback-iteration-log.md`
- Retrieval layers:
  - `resources/sop/2026-02/2026-02-19-sop-governance-routing-writeback-sop.abstract.md`
  - `resources/sop/2026-02/2026-02-19-sop-governance-routing-writeback-sop.overview.md`
- Governance rule:
  - HQ is execution entry; Nexus is canonical authority.

## Internet + Web3 SOP Bundle
- Catalog:
  - `resources/sop/2026-02/2026-02-17-internet-web3-sop-catalog.md`
- External evidence pack:
  - `resources/sop/2026-02/2026-02-17-internet-web3-sop-toolchain-research-pack.md`
- Iteration report:
  - `resources/sop/2026-02/2026-02-17-internet-web3-sop-iteration-report.md`
- Generator script:
  - `scripts/generate_internet_web3_sops.py`
- Artifacts generated:
  - 20 SOP + 20 scorecards + 20 iteration logs
  - 20 research notes
  - 20 L0 abstracts + 20 L1 overviews
- Acceptance:
  - 20/20 strict pass (`python3 scripts/validate_sop_factory.py --sop <file> --strict`)
  - 51/51 strict pass after merge with existing SOP set
