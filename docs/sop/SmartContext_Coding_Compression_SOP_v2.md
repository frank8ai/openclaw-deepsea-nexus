# SmartContext Coding Compression SOP v2

Updated: 2026-03-02

> superseded-by: `Context_Policy_v2_EventDriven.md` (event-driven/L1-L2-L3 production profile)

## Objective
- Keep long coding tasks continuous and resumable.
- Control token spend with measurable thresholds.
- Minimize sensitive data persistence in summaries.

## Three-Layer Context Model
- Core State (always preserved): `Goal / Decision / Constraint / Evidence / Next`.
- Execution Snapshot (stage-level): short progress, errors/risks, validation signals.
- Raw Evidence (on-demand): full logs/artifacts remain in files, not in long summary text.

## Inclusion Policy (Whitelist First)
- High-priority keep signals:
  - lines tagged with `KEEP:`, `[KEEP]`, `#KEEP`
  - explicit goals, decisions, hard constraints, evidence pointers, next steps
- Default drop/deprioritize:
  - repeated phrasing/chitchat
  - long raw command output and stack traces without conclusion
  - obsolete trial branches already superseded

## Secret Safety Policy
- Summary text applies default redaction and pointerization:
  - `sk-...` -> `<SECRET_REF:sk>`
  - `API_KEY/SECRET/TOKEN/...=value` -> `...=<SECRET_REF>`
  - long hex/blob strings -> `<SECRET_REF:hex|blob>`
- Rule: keep only reference/path info (env var name, file location), never raw secret values.

## Mode-Aware Compression Rules
- Base config source: `smart_context` in `skills/deepsea-nexus/config.json`
  - current base: `full_rounds=7`, `summary_rounds=18`, `compress_after_rounds=32`, `soft/hard=0.70/0.85`
- Auto mode detection:
  - coding signals: code fences, stack traces, file paths, tooling commands, patch/diff patterns
  - if score >= 4 => `coding`, else `general`
- Effective thresholds:
  - `coding`: keep `9r`, summary `24r`, compress-after `40r`, soft/hard `0.74/0.90`, higher token trigger
  - `general`: keep `6r`, summary `15r`, compress-after `28r`, soft/hard `0.68/0.82`, lower token trigger

## Handoff Output Contract
- First three lines must exist:
  - `status: ...`
  - `repro_entry: ...`
  - `next_min_action: ...`
- Then fixed sections:
  - `Core State - Goal/Decision/Constraint/Evidence/Next`
  - `Execution Snapshot`
  - `Evidence Pointers`
  - `KEEP Whitelist`

## Metrics and Tuning
- Hook metric `hook_compaction` now records:
  - `mode`, `mode_score`, `mode_signals`
  - effective thresholds (`effective_*`)
- Daily advisor should read:
  - mode distribution, p50 effective thresholds, tokens saved, fallback ratio
- Tuning cadence:
  - review 72h windows
  - require >=4 events before changing parameters
  - adjust by small steps and re-validate for 3+ days

## Operational Plan
1. Keep `smart_context` as single source of truth in deepsea config.
2. Sync runtime with:
   - `python3 skills/deepsea-nexus/scripts/sync_openclaw_context_optimizer.py --apply`
3. Monitor advisor output in:
   - `logs/smart-context-advisor/YYYY-MM-DD/`
4. If cost spikes:
   - tighten base `full/summary/compress_after` by small decrement
5. If continuity drops in coding sessions:
   - loosen coding effective thresholds first (not global defaults)
