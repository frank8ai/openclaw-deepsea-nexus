# SOP: Minimal Closed-Loop (Dev/Bugfix)

Purpose
- Run a development or bugfix task end-to-end with an automated loop.
- Stop only on: (a) PASS, (b) iteration limit, (c) needs human approval.

Scope
- Works for: coding changes, refactors with tests, small feature additions.
- Not for: production deploys, secret rotation, destructive ops (requires approval gates).

Inputs (must be explicit)
- repoPath: absolute path
- goal: one sentence
- verifyCmd: a single command that defines DONE (exit code 0)
- maxIters: default 6
- constraints: allowed / forbidden actions

Workflow (Closed Loop)
1) Recon
   - Identify stack, entrypoints, tests, lint/typecheck if present.
   - Capture snapshot:
     - `git status --porcelain`
     - `git diff --stat`
     - tool versions if relevant (node/python)

2) Baseline Verify
   - Run `verifyCmd` once without changes.
   - Save full output to `logs/closed-loop/iter-0.txt`.
   - Extract 3-7 actionable clues (error signatures, failing files, missing deps).

3) Minimal Fix
   - Apply the smallest change that plausibly fixes the root cause.
   - Prefer:
     - Localized edits
     - Backward-compatible defaults
     - Test-only shims for optional deps (only if tests require them)

4) Re-Verify
   - Re-run `verifyCmd`.
   - If PASS: go to Finalize.
   - If FAIL: increment iter and repeat (3) -> (4) until maxIters.

5) Approval Gates (stop and ask)
   - Any external send (email/discord/telegram) not explicitly requested.
   - Any destructive change (delete/migrate data, mass file removal).
   - Any cross-system change (prod, billing, permissions, firewall, gateway lifecycle).
   - Any new dependency that changes the runtime or security posture.

6) Finalize
   - Write RESULT:
     - PASS/FAIL
     - verifyCmd used
     - last verify summary (short)
     - changed files list + intent
     - risks/notes

Outputs
- A short RESULT section that can be posted to chat.
- Files:
  - `logs/closed-loop/iter-*.txt` (optional)
  - `RESULT.md` (optional)
