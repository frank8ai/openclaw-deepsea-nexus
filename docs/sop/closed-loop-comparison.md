# Closed-Loop Comparison: SOP vs Summary

This doc compares:
- (A) The two SOPs generated here:
  - `docs/sop/closed-loop-minimal.md`
  - `docs/sop/closed-loop-production.md`
- (B) The 10-mechanism summary (user-provided) and the earlier assistant mapping.

## 1) Coverage Map (10 mechanisms)

1. Trigger mechanism
- SOP(A): Explicitly supports user request; can be triggered manually.
- SOP(B): Supports scheduled maintenance and service remediation.
- Gap: Not explicitly documenting cron/heartbeat/hook triggers. Add as appendix if needed.

2. Context loading
- SOP(A): Inputs + recon step covers project/test discovery.
- SOP(B): Inputs include targetSystem, plans.
- Gap: Memory/long-term context is not formalized as a mandatory input section.

3. Baseline collection
- SOP(A): Snapshot via git status/diff and tool versions.
- SOP(B): Full snapshot artifacts list.

4. Root cause
- SOP(A/B): Both enforce baseline verify/reproduce and root-cause.

5. Change execution
- SOP(A): Minimal fix guidance.
- SOP(B): Minimal + reversible plan, recorded commands.

6. Quality gate
- SOP(A): verifyCmd as DONE.
- SOP(B): functional + smoke + regression + log checks.

7. Release & rollback
- SOP(A): Not rolling back by default; expects git diff review.
- SOP(B): Explicit rollback plan and triggers.

8. Observability
- SOP(A): Not included (dev loop).
- SOP(B): Observability window + indicators.

9. Anti-regression
- SOP(A/B): Both include test/guardrail improvements, but SOP(B) makes it explicit.

10. Memory deposition
- SOP(A/B): Output sections cover summary artifacts; not yet wired to a memory sink.
- Recommendation: add an optional "Log to memory" appendix (daily + long-term).

## 2) Which is better?

- Best for day-to-day dev/bugfix loop: SOP(A).
  - Strongest point: single verifyCmd defines DONE; iteration bounded; low overhead.
  - Weakest point: no explicit observability/rollback.

- Best for high-risk changes (production): SOP(B).
  - Strongest point: snapshot/rollback/observability are first-class.
  - Weakest point: heavier input requirements; needs explicit approvals.

## 3) Improvements (make SOPs closer to the 10-mechanism ideal)

- Add an Appendix: Trigger adapters
  - user request / cron isolated / cron main systemEvent / heartbeat / webhook

- Add an Appendix: Memory sinks
  - Daily memory: `memory/YYYY-MM-DD.md`
  - Long-term playbook: `SOP/` or `docs/sop/`

- Add a Safety Matrix
  - classify actions into: auto / ask / forbid

## 4) Recommendation

- Keep both SOPs.
- For automation: default to SOP(A), escalate to SOP(B) when risk >= medium.
