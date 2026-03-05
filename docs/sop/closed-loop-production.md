# SOP: Production-Grade Closed Loop (With Snapshot/Rollback/Observability)

Purpose
- Run automated remediation or change safely with preflight, rollback points, and post-verify.
- Designed for high-risk environments where “PASS” is not enough without runtime confirmation.

Scope
- Works for: service remediation, config changes, scheduled maintenance.
- Requires explicit approvals for: production changes, external comms, destructive actions.

Inputs
- targetSystem: host/service/repo identifier
- goal: one sentence
- verifyPlan:
  - functional check(s)
  - regression/smoke checks
  - health checks
- rollbackPlan:
  - what snapshot to take
  - how to restore
- observabilityPlan:
  - metrics/log queries
  - alert thresholds

Workflow (Closed Loop)
1) Preflight + Authorization
   - Confirm scope and permissions.
   - Confirm approvals are in place for high-risk steps.

2) Baseline Snapshot (“Before”)
   - Capture immutable snapshot artifacts:
     - config dump (relevant files)
     - process list + port listeners
     - recent logs tail
     - current version/commit
   - Persist snapshot id and paths.

3) Reproduce + Root Cause
   - Reproduce the symptom with a deterministic probe.
   - Identify the root cause; avoid surface restarts as the only fix.

4) Plan Change (Minimal + Reversible)
   - Define smallest reversible change.
   - Define rollback trigger conditions.

5) Execute Change
   - Apply change.
   - Record exact commands and file diffs.

6) Quality Gates
   - Run functional verification.
   - Run smoke/regression checks.
   - Confirm no new errors in logs.

7) Runtime Observability Window
   - Watch key indicators for a fixed window (e.g., 10-30 min):
     - error rate
     - timeout/latency
     - queue depth
     - crash loops
     - port conflicts

8) Rollback (If Any Gate Fails)
   - Restore from snapshot.
   - Re-run baseline probe.
   - Escalate with evidence.

9) Postmortem Lite (Prevent Recurrence)
   - Add/adjust tests.
   - Add guardrails.
   - Update playbook.

Outputs
- CHANGELOG entry (what/why).
- Snapshot location + rollback steps.
- Verification results + observability notes.
- A short message suitable for stakeholder update.
