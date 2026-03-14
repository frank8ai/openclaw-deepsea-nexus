# Minimal Closed-Loop Subagent Template (Deep-Sea Nexus)

repoPath: `{{repoPath}}`

> Fill `repoPath` with the actual checkout path for the repo you want the
> subagent to operate on.

goal:
- Make `verifyCmd` pass with minimal code changes (no new deps unless required by tests).
- Keep behavior backward compatible; avoid production-write side effects.

verifyCmd (auto-detected):
- `python3 run_tests.py`

maxIters:
- 6

rules:
- Do: recon -> run verifyCmd -> minimal fix -> re-run verifyCmd (repeat up to maxIters).
- Prefer fixing root-cause over suppressing tests.
- Keep edits minimal and localized.
- No remote push, no production changes, no login/keys.
- If a fix requires new dependency, prefer a tiny local stub when used only by tests.
- If stuck after maxIters: report FAIL with last error summary + suggested next step.

deliverables:
- PASS/FAIL
- Last verify output summary (key failures only)
- Key changed files list
- Rationale (1-3 bullets)
