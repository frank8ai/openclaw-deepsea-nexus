# Context Policy v2 (Event-Driven, Replayable)

Updated: 2026-03-02

## 1) Memory Architecture
- `L1 Runtime State` (ephemeral, TTL 24h):
  - `Goal / Now / Blocker / Next / Owner / ETA / Risk`
  - Used only for current execution continuity.
- `L2 Durable Decision` (long):
  - `Decision / Why / Constraint / Evidence pointer / Reversal condition`
  - Stored only if score >= 3 and evidence exists.
- `L3 Evidence Store`:
  - raw logs/artifacts/session files remain external.
  - summaries keep pointers only (`path[:line]`, command, artifact id/hash).

## 2) Event-Driven Summarization
- Summary refresh only when one of these occurs:
  - decision changed
  - status changed (`start/in-progress/blocked/validated`)
  - new blocker appears
  - new validation result appears
  - phase complete trigger (`compress-after-rounds` / hard-ratio)
- If no event:
  - reuse previous summary (no rewrite churn).

## 3) Security & Redaction
- L1/L2 never keep secret values.
- Secret pointer format only:
  - `<SECRET_REF:sk>`
  - `<SECRET_REF>`
  - `<SECRET_REF:hex|blob>`
- Keep `env var / file path / vault key` references only.

## 4) Hard Rules
- `No Evidence, No Memory`:
  - no evidence pointer => decision cannot enter L2.
- `One Change, One Record`:
  - each meaningful event writes at most one structured L2 record.
- `TTL Context`:
  - L1 auto-expire after 24h (default) to avoid stale pollution.

## 5) Handoff Contract (enforced in summary format)
- Required lines:
  - `State`
  - `Decisions` (top 3)
  - `Blocker`
  - `Replay` (single command)
  - `Next` (single smallest action)
- Additional lines:
  - `L1`, `L2`, `Evidence`, `Events`, `TTL`
- Total summary lines capped at 12.

## 6) Metrics
- `hook_compaction` now emits:
  - mode/effective thresholds
  - `policy_v2_refreshed`
  - `policy_v2_events`
  - `policy_v2_l2_score`
  - `policy_v2_l2_written`
- Advisor tracks:
  - mode distribution
  - effective threshold p50
  - policy refresh ratio
  - L2 write ratio
