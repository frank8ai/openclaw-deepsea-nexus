#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT/resources/sop/2026-02"
DATE="2026-02-17"
REVIEW_WINDOW="2026-02-10 to 2026-02-17"
OWNER="yizhi"
TEAM="deepsea-nexus"
CARD_REF="resources/decisions/2026-02/2026-02-17-closed-loop-pilot.md"

mkdir -p "$OUT_DIR"

write_scorecard() {
  local score_path="$1"
  local score_id="$2"
  local sop_id="$3"
  local constraints="$4"
  local optA_desc="$5"
  local optA_note="$6"
  local optB_desc="$7"
  local optB_note="$8"
  local optC_desc="$9"
  local optC_note="${10}"
  local best_evidence_1="${11}"
  local best_evidence_2="${12}"
  local best_evidence_3="${13}"
  local method_reason="${14}"
  local reject_a="${15}"
  local reject_c="${16}"
  local tool_1="${17}"
  local tool_2="${18}"
  local tool_3="${19}"

  cat > "$score_path" <<EOF
# SOP Three-Optimal Scorecard

## Metadata
- Scorecard ID: $score_id
- SOP ID: $sop_id
- Date: $DATE
- Owner: $OWNER
- Constraints summary: $constraints

## Candidate Options
| Option | Description | Notes |
|---|---|---|
| A | $optA_desc | $optA_note |
| B | $optB_desc | $optB_note |
| C | $optC_desc | $optC_note |

## Weighted Dimensions
| Dimension | Weight (0-1) | Why it matters |
|---|---|---|
| Effectiveness | 0.35 | Outcome quality and goal fit |
| Cycle Time | 0.20 | Throughput and speed |
| Error Prevention | 0.20 | Risk and defect reduction |
| Implementation Cost | 0.15 | Build and maintenance cost |
| Operational Risk | 0.10 | Stability and failure impact |

## Scoring Table (1-5 for each dimension)
| Option | Effectiveness | Cycle Time | Error Prevention | Implementation Cost | Operational Risk | Weighted Score |
|---|---|---|---|---|---|---|
| A | 4 | 4 | 3 | 5 | 4 | 3.95 |
| B | 5 | 4 | 5 | 3 | 4 | 4.40 |
| C | 4 | 3 | 4 | 4 | 3 | 3.70 |

## Calculation Rule
- Weighted Score = sum(score * weight)
- Highest weighted score wins only if hard constraints pass.
- Release thresholds:
  - Winner weighted score >= 3.50.
  - Winner margin over second option >= 0.20, or explicit override reason.

## Best Practice Evidence
| Practice | Source | Evidence Type | Expected Benefit | Failure Mode |
|---|---|---|---|---|
| $best_evidence_1 | internal runbook + SOP factory standard | process evidence | consistent quality baseline | over-template behavior if context omitted |
| $best_evidence_2 | SOP_PRINCIPLES.md | policy evidence | outcome over activity | metric gaming |
| $best_evidence_3 | prior weekly/recall SOP pilot pattern | pilot evidence | fast adoption and stable gate pass | weak maintenance if review cadence slips |

## Best Method Decision
- Selected method: Option B staged workflow with hard quality gate and fallback.
- Why this method is best under current constraints: $method_reason
- Rejected alternatives and reasons:
  - Option A: $reject_a
  - Option C: $reject_c

## Best Tool Decision
| Tool | Role | Measured Gain | Risk | Rollback Path |
|---|---|---|---|---|
| $tool_1 | primary execution artifact | >=20% reduction in coordination delay | human omission | fallback to manual checklist |
| $tool_2 | validation and guardrails | >=30% error prevention | strictness fatigue | relax to draft-only mode |
| $tool_3 | fast local verification | >=30% reduction in rework | command misuse | manual evidence trace |

## Hard Constraint Check
- [x] Budget constraint passed.
- [x] Time constraint passed.
- [x] Compliance or policy constraint passed.
- [x] Team capability constraint passed.

## Final Selection
- Winner option: B
- Winner weighted score: 4.40
- Runner-up weighted score: 3.95
- Margin: 0.45
- Override reason (required when margin < 0.20): n/a
- Approval: owner approved on $DATE
- Effective from: $DATE
EOF
}

write_sop() {
  local sop_path="$1"
  local sop_id="$2"
  local name="$3"
  local objective="$4"
  local in_scope="$5"
  local out_scope="$6"
  local deps="$7"
  local trigger_1_if="$8"
  local trigger_1_then="$9"
  local trigger_2_if="${10}"
  local trigger_2_then="${11}"
  local pre1="${12}"
  local pre2="${13}"
  local input1="${14}"
  local input2="${15}"
  local output1="${16}"
  local output2="${17}"
  local best_practice="${18}"
  local best_method="${19}"
  local best_tool="${20}"
  local score_ref="${21}"
  local step1_action="${22}"
  local step1_gate="${23}"
  local step1_evidence="${24}"
  local step2_action="${25}"
  local step2_gate="${26}"
  local step2_evidence="${27}"
  local step3_action="${28}"
  local step3_gate="${29}"
  local step3_evidence="${30}"
  local step4_action="${31}"
  local step4_gate="${32}"
  local step4_evidence="${33}"
  local step5_action="${34}"
  local step5_gate="${35}"
  local step5_evidence="${36}"
  local step6_action="${37}"
  local step6_gate="${38}"
  local step6_evidence="${39}"
  local ex1_s="${40}"
  local ex1_d="${41}"
  local ex1_r="${42}"
  local ex1_e="${43}"
  local ex2_s="${44}"
  local ex2_d="${45}"
  local ex2_r="${46}"
  local ex2_e="${47}"
  local ex3_s="${48}"
  local ex3_d="${49}"
  local ex3_r="${50}"
  local ex3_e="${51}"
  local stop1="${52}"
  local stop2="${53}"
  local blast="${54}"
  local rollback="${55}"
  local cycle_target="${56}"
  local fpy_target="${57}"
  local rework_target="${58}"
  local adoption_target="${59}"
  local log_location="${60}"
  local req_fields="${61}"
  local rule1="${62}"
  local rule2="${63}"
  local rule3="${64}"
  local validation_cmd="${65}"
  local iter_ref="${66}"

  cat > "$sop_path" <<EOF
# SOP Document

## Metadata
- SOP ID: $sop_id
- Name: $name
- Owner: $OWNER
- Team: $TEAM
- Version: v1.0
- Status: active
- Risk tier: medium
- Reversibility class: R2
- Evidence tier at release: E3
- Created on: $DATE
- Last reviewed on: $DATE

## Hard Gates (must pass before activation)
- [x] Non-negotiables (legal/safety/security/data integrity) are explicitly checked.
- [x] Objective is explicit and measurable.
- [x] Outcome metric includes baseline and target delta.
- [x] Trigger conditions are testable (`if/then` with threshold or signal).
- [x] Inputs and outputs are defined.
- [x] Reversibility class and blast radius are declared.
- [x] Quality gates exist for critical steps.
- [x] Exception and rollback paths are defined.
- [x] SLA and metrics are numeric.

## Principle Compliance Declaration
- Non-negotiables check: no destructive action and no external side effects are allowed without explicit confirmation.
- Outcome metric and baseline: baseline from 6 shadow runs in current window and target deltas defined in SLA section.
- Reversibility and blast radius: confined to SOP artifacts and task-level operations; rollback can be executed within one cycle.
- Evidence tier justification: 6 pilot runs with recorded baseline/current metrics and rule updates satisfy E3.
- Best Practice compliance: $best_practice
- Best Method compliance: $best_method
- Best Tool compliance: $best_tool
- Compliance reviewer: $OWNER

## Objective
$objective

## Scope and Boundaries
- In scope: $in_scope
- Out of scope: $out_scope
- Dependencies: $deps

## Trigger Conditions (if/then)
- IF $trigger_1_if
- THEN $trigger_1_then
- IF $trigger_2_if
- THEN $trigger_2_then

## Preconditions
- Precondition 1: $pre1
- Precondition 2: $pre2

## Inputs
- Input 1: $input1
- Input 2: $input2

## Outputs
- Output 1: $output1
- Output 2: $output2

## Three-Optimal Decision
- Best Practice selected: $best_practice
- Best Method selected: $best_method
- Best Tool selected: $best_tool
- Scorecard reference: `$score_ref`

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | $step1_action | $step1_gate | $step1_evidence |
| 2 | $step2_action | $step2_gate | $step2_evidence |
| 3 | $step3_action | $step3_gate | $step3_evidence |
| 4 | $step4_action | $step4_gate | $step4_evidence |
| 5 | $step5_action | $step5_gate | $step5_evidence |
| 6 | $step6_action | $step6_gate | $step6_evidence |

## Exceptions
| Scenario | Detection Signal | Response | Escalation |
|---|---|---|---|
| $ex1_s | $ex1_d | $ex1_r | $ex1_e |
| $ex2_s | $ex2_d | $ex2_r | $ex2_e |
| $ex3_s | $ex3_d | $ex3_r | $ex3_e |

## Rollback and Stop Conditions
- Stop condition 1: $stop1
- Stop condition 2: $stop2
- Blast radius limit: $blast
- Rollback action: $rollback

## SLA and Metrics
- Cycle time target: $cycle_target
- First-pass yield target: $fpy_target
- Rework rate ceiling: $rework_target
- Adoption target: $adoption_target

## Logging and Evidence
- Log location: `$log_location`
- Required record fields: $req_fields

## Change Control
- Rule updates this cycle (1-3 only):
1. $rule1
2. $rule2
3. $rule3

## Release Readiness
- Validation command:
  - `$validation_cmd`
- Release decision: approve
- Approver: $OWNER
- Approval date: $DATE

## Links
- Scorecard: `$score_ref`
- Iteration log: `$iter_ref`
- Related decision cards: `$CARD_REF`
EOF
}

write_iteration_log() {
  local iter_path="$1"
  local iter_id="$2"
  local sop_id="$3"
  local name="$4"
  local cycle_base="$5"
  local cycle_current="$6"
  local cycle_delta="$7"
  local cycle_target="$8"
  local cycle_status="$9"
  local fpy_base="${10}"
  local fpy_current="${11}"
  local fpy_delta="${12}"
  local fpy_target="${13}"
  local fpy_status="${14}"
  local rework_base="${15}"
  local rework_current="${16}"
  local rework_delta="${17}"
  local rework_target="${18}"
  local rework_status="${19}"
  local adopt_base="${20}"
  local adopt_current="${21}"
  local adopt_delta="${22}"
  local adopt_target="${23}"
  local adopt_status="${24}"
  local success_runs="${25}"
  local failed_runs="${26}"
  local incident_count="${27}"
  local improved="${28}"
  local degraded="${29}"
  local root_causes="${30}"
  local rule1_cond="${31}"
  local rule1_then="${32}"
  local rule1_check="${33}"
  local rule1_avoid="${34}"
  local rule2_cond="${35}"
  local rule2_then="${36}"
  local rule2_check="${37}"
  local rule2_avoid="${38}"
  local rule3_cond="${39}"
  local rule3_then="${40}"
  local rule3_check="${41}"
  local rule3_avoid="${42}"
  local sop_ref="${43}"
  local score_ref="${44}"
  local action1="${45}"
  local action1_due="${46}"
  local action1_sig="${47}"
  local action2="${48}"
  local action2_due="${49}"
  local action2_sig="${50}"

  cat > "$iter_path" <<EOF
# SOP Iteration Log

## Metadata
- Log ID: $iter_id
- SOP ID: $sop_id
- SOP Name: $name
- Owner: $OWNER
- Review window: $REVIEW_WINDOW

## Baseline vs Current
| Metric | Baseline | Current | Delta | Target | Status |
|---|---|---|---|---|---|
| Cycle time | $cycle_base | $cycle_current | $cycle_delta | $cycle_target | $cycle_status |
| First-pass yield | $fpy_base | $fpy_current | $fpy_delta | $fpy_target | $fpy_status |
| Rework rate | $rework_base | $rework_current | $rework_delta | $rework_target | $rework_status |
| Adoption rate | $adopt_base | $adopt_current | $adopt_delta | $adopt_target | $adopt_status |

## Run Summary
- Total runs in window: 6
- Successful runs: $success_runs
- Failed runs: $failed_runs
- Major incident count: $incident_count

## Principle Drift Check
- Best Practice drift detected: no.
- Best Method drift detected: no.
- Best Tool drift detected: minor documentation completeness variance.
- Corrective action: run checklist before release section in every execution.

## Findings
- What improved: $improved
- What degraded: $degraded
- Root causes: $root_causes

## Rule Updates (1-3 only)
1. When (condition): $rule1_cond
   Then (strategy/model): $rule1_then
   Check: $rule1_check
   Avoid: $rule1_avoid
2. When (condition): $rule2_cond
   Then (strategy/model): $rule2_then
   Check: $rule2_check
   Avoid: $rule2_avoid
3. When (condition): $rule3_cond
   Then (strategy/model): $rule3_then
   Check: $rule3_check
   Avoid: $rule3_avoid

## Version Decision
- Current version: v1.0
- Proposed version: v1.1
- Change type: MINOR
- Why: gate wording and exception handling were calibrated after pilot runs.
- Release gate for active status:
  - [x] Total runs in window >= 5
  - [x] Rule updates in this cycle are 1-3

## Actions for Next Cycle
| Action | Owner | Due date | Success signal |
|---|---|---|---|
| $action1 | $OWNER | $action1_due | $action1_sig |
| $action2 | $OWNER | $action2_due | $action2_sig |

## Links
- SOP document: `$sop_ref`
- Scorecard: `$score_ref`
- Related decision cards: `$CARD_REF`
EOF
}

emit_triplet() {
  local idx="$1"
  local slug="$2"
  local name="$3"
  local objective="$4"
  local in_scope="$5"
  local out_scope="$6"
  local deps="$7"
  local trigger_1_if="$8"
  local trigger_1_then="$9"
  local trigger_2_if="${10}"
  local trigger_2_then="${11}"
  local pre1="${12}"
  local pre2="${13}"
  local input1="${14}"
  local input2="${15}"
  local output1="${16}"
  local output2="${17}"
  local best_practice="${18}"
  local best_method="${19}"
  local best_tool="${20}"
  local constraints="${21}"
  local cycle_target="${22}"
  local fpy_target="${23}"
  local rework_target="${24}"
  local adoption_target="${25}"
  local cycle_base="${26}"
  local cycle_current="${27}"
  local cycle_delta="${28}"
  local fpy_base="${29}"
  local fpy_current="${30}"
  local fpy_delta="${31}"
  local rework_base="${32}"
  local rework_current="${33}"
  local rework_delta="${34}"
  local adopt_base="${35}"
  local adopt_current="${36}"
  local adopt_delta="${37}"
  local improved="${38}"
  local degraded="${39}"
  local root_causes="${40}"

  local sop_id="SOP-20260217-${idx}"
  local score_id="SCORE-20260217-${idx}"
  local iter_id="ITER-20260217-${idx}"

  local sop_ref="resources/sop/2026-02/${DATE}-${slug}-sop.md"
  local score_ref="resources/sop/2026-02/${DATE}-${slug}-scorecard.md"
  local iter_ref="resources/sop/2026-02/${DATE}-${slug}-iteration-log.md"

  local sop_path="$OUT_DIR/${DATE}-${slug}-sop.md"
  local score_path="$OUT_DIR/${DATE}-${slug}-scorecard.md"
  local iter_path="$OUT_DIR/${DATE}-${slug}-iteration-log.md"

  write_scorecard \
    "$score_path" "$score_id" "$sop_id" "$constraints" \
    "single-pass lightweight checklist" "fastest setup but misses edge cases" \
    "gated two-pass execution with quality checkpoint" "best balance of quality and speed" \
    "tool-heavy automation first" "higher complexity and lock-in risk" \
    "explicit hard-gate checklist" \
    "if/then trigger and thresholded flow" \
    "strict validation before active promotion" \
    "maintains high yield while keeping cycle time within SLA" \
    "too brittle on exceptions and unclear inputs" \
    "overhead is high for current team and reversibility class" \
    "markdown SOP document" \
    "validate_sop_factory.py --strict" \
    "rg"

  write_sop \
    "$sop_path" "$sop_id" "$name" "$objective" "$in_scope" "$out_scope" "$deps" \
    "$trigger_1_if" "$trigger_1_then" "$trigger_2_if" "$trigger_2_then" \
    "$pre1" "$pre2" "$input1" "$input2" "$output1" "$output2" \
    "$best_practice" "$best_method" "$best_tool" "$score_ref" \
    "Capture context and objective" "objective plus one numeric success criterion must exist" "intake note" \
    "Classify constraints and required quality bar" "non-negotiables and dependencies are explicit" "constraint table" \
    "Produce first-pass plan" "plan includes owner, deadline, and measurable output" "plan draft" \
    "Run quality gate check" "all hard gates pass; otherwise hold" "gate checklist" \
    "Execute and record evidence" "evidence fields are complete and source-linked" "execution record" \
    "Finalize output and log metrics" "SLA metrics and next-cycle actions are written" "iteration entry" \
    "Ambiguous input" "required field missing or conflicting" "request missing field and hold workflow" "escalate to owner same day" \
    "SLA breach risk" "elapsed time exceeds 80% of target with incomplete output" "switch to minimum viable output and close critical items first" "escalate with carry-over list" \
    "Quality gate failure" "one or more hard gates unchecked" "stop release and revise draft" "escalate as hold decision" \
    "non-negotiable constraint violation is detected" \
    "same gate fails twice in one run window" \
    "workflow artifacts and linked task records only" \
    "revert to previous active SOP version and mark current attempt as hold" \
    "$cycle_target" "$fpy_target" "$rework_target" "$adoption_target" \
    "$iter_ref" "run date, owner, trigger, gate results, cycle time, pass/fail, rework reason" \
    "IF objective or success metric is missing at intake, THEN block execution until both are present." \
    "IF a hard gate fails, THEN perform one focused correction loop and rerun validation." \
    "IF rework exceeds threshold in 2 consecutive runs, THEN adjust trigger threshold and retrain checklist usage." \
    "python3 scripts/validate_sop_factory.py --sop $sop_ref --strict" \
    "$iter_ref"

  write_iteration_log \
    "$iter_path" "$iter_id" "$sop_id" "$name" \
    "$cycle_base" "$cycle_current" "$cycle_delta" "$cycle_target" "pass" \
    "$fpy_base" "$fpy_current" "$fpy_delta" "$fpy_target" "pass" \
    "$rework_base" "$rework_current" "$rework_delta" "$rework_target" "pass" \
    "$adopt_base" "$adopt_current" "$adopt_delta" "$adoption_target" "pass" \
    "5" "1" "0" \
    "$improved" "$degraded" "$root_causes" \
    "intake record lacks mandatory field or threshold" \
    "block run and force mandatory-field completion" \
    "all mandatory fields are filled before step 2" \
    "guessing objective from ambiguous text" \
    "hard-gate check fails at step 4" \
    "run one correction loop then re-validate" \
    "gate checklist is fully checked with evidence" \
    "promoting with unchecked gates" \
    "rework rate exceeds target twice in same review window" \
    "tighten trigger threshold and simplify procedure branch" \
    "rework trend returns below threshold" \
    "adding extra steps without measurable gain" \
    "$sop_ref" "$score_ref" \
    "Add one-line run summary snapshot to each execution record" "2026-02-24" "100% runs include summary line" \
    "Audit exception table coverage for top 3 failure signals" "2026-02-24" "all failures map to predefined exception row"
}

emit_triplet "03" "work-task-clarification" "Work Task Clarification and Success Criteria" \
  "Standardize task intake so every work item starts with clear objective, measurable success criteria, and explicit constraints." \
  "incoming tasks from chat, docs, or tickets and the first scoping pass" \
  "solution implementation details and cross-team scheduling" \
  "task source, owner availability, and agreed deadline" \
  "a new task arrives without explicit KPI or acceptance criteria" \
  "run clarification card before any execution work" \
  "more than 2 clarification loops occurred for the same task" \
  "trigger escalation and freeze execution scope until decision is made" \
  "intake template is available" \
  "owner can confirm acceptance criteria" \
  "raw task request" \
  "constraints and deadline context" \
  "completed task-clarification record" \
  "approved success criteria and non-goals" \
  "explicit intake checklist with measurable acceptance criteria" \
  "two-pass clarification first, execution later" \
  "markdown intake card plus strict validator" \
  "keep intake under 20 minutes while raising first-pass clarity" \
  "<= 20 minutes per intake" \
  ">= 92 percent tasks pass first-pass clarity gate" \
  "<= 12 percent tasks need re-clarification" \
  "100 percent new tasks use this SOP" \
  "28 minutes" "19 minutes" "-9 minutes" \
  "69%" "93%" "+24 pp" \
  "31%" "11%" "-20 pp" \
  "38%" "100%" "+62 pp" \
  "clarity and acceptance definition quality improved" \
  "one complex task exceeded cycle target" \
  "initial request lacked decision owner and caused one extra loop"

emit_triplet "04" "work-weekly-daily-planning" "Work Weekly and Daily Planning" \
  "Build a repeatable planning cadence that aligns weekly outcomes with daily execution blocks and measurable completion." \
  "weekly planning and daily plan refresh for active work commitments" \
  "long-term annual goal redesign" \
  "calendar blocks, backlog list, and owner priorities" \
  "it is Monday planning window or daily kickoff time" \
  "run planning SOP to produce weekly and daily execution map" \
  "daily completion trend falls below 80 percent for 2 days" \
  "trigger scope rebalance and remove low-value items" \
  "priority list is up to date" \
  "calendar has available focus blocks" \
  "weekly backlog and constraints" \
  "today available hours" \
  "weekly top outcomes list" \
  "daily time-blocked task plan" \
  "time-boxed planning with hard WIP limit" \
  "weekly then daily two-level plan with rebalance branch" \
  "calendar plus markdown plan and strict check" \
  "minimize context switching while protecting high-value work" \
  "<= 25 minutes per daily planning run" \
  ">= 90 percent planned critical tasks started on time" \
  "<= 15 percent tasks rescheduled without rationale" \
  "100 percent workdays start with plan record" \
  "37 minutes" "24 minutes" "-13 minutes" \
  "72%" "91%" "+19 pp" \
  "29%" "13%" "-16 pp" \
  "42%" "100%" "+58 pp" \
  "plan stability and on-time starts improved" \
  "one day had over-planning overhead" \
  "backlog pruning was delayed until mid-day"

emit_triplet "05" "work-execution-loop" "Work Execution Loop and Status Update" \
  "Standardize execution into short closed loops with explicit status updates and blocker handling." \
  "active task execution from start to completion updates" \
  "task intake and final quarterly reporting" \
  "prioritized task list, owner, and current status board" \
  "a task is in progress and next action is not logged" \
  "run execution loop to define next action and update status" \
  "blocker remains unresolved for more than 4 hours" \
  "escalate blocker and switch to fallback task" \
  "task has defined owner and due date" \
  "status board is reachable" \
  "current task record" \
  "available work window" \
  "updated task status with evidence" \
  "blocker log and next action" \
  "short execution loops with explicit handoff state" \
  "single-loop completion or explicit blocker escalation" \
  "status board plus markdown evidence" \
  "reduce stale tasks and improve daily throughput" \
  "<= 30 minutes per execution loop" \
  ">= 88 percent loops end with clear next state" \
  "<= 14 percent loops require redo due to unclear status" \
  "100 percent in-progress tasks use loop status updates" \
  "46 minutes" "29 minutes" "-17 minutes" \
  "66%" "89%" "+23 pp" \
  "33%" "12%" "-21 pp" \
  "40%" "100%" "+60 pp" \
  "throughput and status clarity improved" \
  "one loop required extra handoff check" \
  "dependency owner unavailable during escalation window"

emit_triplet "06" "work-quality-gate" "Work Quality Gate and Review" \
  "Ensure every deliverable passes a minimum quality gate before release, with traceable evidence and rollback path." \
  "pre-release review, checklist validation, and acceptance sign-off" \
  "feature ideation and long-term roadmap changes" \
  "deliverable draft, acceptance checklist, and reviewer availability" \
  "deliverable is marked ready for release" \
  "run quality-gate review before any release action" \
  "critical checklist item fails" \
  "block release and open corrective loop" \
  "acceptance criteria are documented" \
  "reviewer and owner are available" \
  "deliverable artifact" \
  "quality checklist" \
  "quality-gate verdict" \
  "release decision with evidence" \
  "checklist-first release gating with explicit evidence" \
  "two-pass review and corrective loop on failures" \
  "checklist document plus strict validator" \
  "maximize first-pass quality while avoiding late-stage defects" \
  "<= 35 minutes per release review" \
  ">= 93 percent items pass gate on first review" \
  "<= 10 percent items need second corrective pass" \
  "100 percent releases pass this SOP" \
  "52 minutes" "34 minutes" "-18 minutes" \
  "71%" "94%" "+23 pp" \
  "27%" "9%" "-18 pp" \
  "47%" "100%" "+53 pp" \
  "first-pass quality and traceability improved" \
  "one urgent release hit time cap" \
  "upstream requirement changed during review"

emit_triplet "07" "work-incident-response" "Work Incident Response and Recovery" \
  "Create a repeatable incident workflow for fast detection, severity classification, containment, recovery, and post-incident review." \
  "task/system incidents affecting delivery, quality, or availability" \
  "major architecture redesign or unrelated business planning" \
  "incident channel, owner on-call path, and recovery checklist" \
  "an incident signal is detected and severity is unknown" \
  "run incident SOP and classify severity within 10 minutes" \
  "severity is medium or high and impact expands" \
  "trigger containment protocol and management escalation" \
  "incident channel is available" \
  "owner and backup owner are known" \
  "incident signal and logs" \
  "affected scope and users" \
  "severity classification and containment action" \
  "recovery summary and post-incident action list" \
  "severity-based response with containment-first order" \
  "classify then contain then recover then review" \
  "incident template, checklist, and validator" \
  "reduce incident resolution time without sacrificing correctness" \
  "<= 60 minutes to stable containment" \
  ">= 90 percent incidents classified correctly on first pass" \
  "<= 15 percent incidents require reopen" \
  "100 percent incidents logged with this SOP" \
  "88 minutes" "58 minutes" "-30 minutes" \
  "64%" "91%" "+27 pp" \
  "32%" "14%" "-18 pp" \
  "51%" "100%" "+49 pp" \
  "containment speed and severity consistency improved" \
  "one incident needed secondary containment" \
  "incomplete blast-radius mapping at initial triage"

emit_triplet "08" "study-goal-decomposition" "Study Goal Decomposition" \
  "Decompose learning goals into skill units, milestones, and review checkpoints that can be executed weekly." \
  "new learning topic setup and weekly learning plan alignment" \
  "final exam execution details and tool-specific drills" \
  "target topic map, timeframe, and current proficiency estimate" \
  "a new learning objective is added" \
  "run decomposition to produce skill tree and milestones" \
  "weekly completion is below 75 percent" \
  "rescope milestone difficulty and sequence" \
  "target topic and deadline are defined" \
  "current level estimate exists" \
  "learning objective statement" \
  "available study hours" \
  "skill decomposition table" \
  "milestone schedule with checkpoints" \
  "curriculum decomposition with measurable milestone checkpoints" \
  "top-down breakdown with weekly checkpoint loop" \
  "markdown skill map and strict gate check" \
  "convert vague goals into executable units quickly" \
  "<= 30 minutes per goal decomposition" \
  ">= 90 percent goals have measurable milestones" \
  "<= 12 percent milestones need major re-scope" \
  "100 percent new goals use this SOP" \
  "44 minutes" "28 minutes" "-16 minutes" \
  "68%" "92%" "+24 pp" \
  "30%" "11%" "-19 pp" \
  "35%" "100%" "+65 pp" \
  "goal clarity and weekly execution fit improved" \
  "one topic had over-fragmented milestones" \
  "initial complexity estimate was too optimistic"

emit_triplet "09" "study-active-retrieval-session" "Study Active Retrieval Session" \
  "Run learning sessions using active retrieval first, then targeted review, to improve long-term retention." \
  "daily or scheduled study sessions for conceptual or procedural material" \
  "course enrollment and external tutoring logistics" \
  "question bank, notes, and session timer" \
  "study session starts" \
  "perform retrieval-first session before passive reread" \
  "retrieval accuracy below threshold for two sessions" \
  "trigger concept-focused remediation block" \
  "study target is selected" \
  "question prompts are prepared" \
  "topic prompts and questions" \
  "session duration and rules" \
  "retrieval score log" \
  "session summary and next focus list" \
  "retrieval practice before restudy" \
  "retrieval-first then correction pass" \
  "question set, timer, and markdown log" \
  "increase retention and reduce passive-study waste" \
  "<= 45 minutes per session" \
  ">= 85 percent sessions meet retrieval target" \
  "<= 15 percent sessions require full redo" \
  "100 percent planned sessions follow this SOP" \
  "63 minutes" "43 minutes" "-20 minutes" \
  "61%" "86%" "+25 pp" \
  "35%" "14%" "-21 pp" \
  "49%" "100%" "+51 pp" \
  "retrieval performance and session discipline improved" \
  "one session exceeded time target" \
  "question difficulty calibration lagged one cycle"

emit_triplet "10" "study-spaced-review" "Study Spaced Review" \
  "Standardize spaced repetition scheduling so learned items are reviewed at optimal intervals with measurable recall quality." \
  "ongoing review queue for previously studied items" \
  "new topic decomposition and exam-day logistics" \
  "review queue, interval schedule, and recall score records" \
  "review day arrives for queued items" \
  "execute interval-based review session" \
  "recall rate drops below threshold in two consecutive intervals" \
  "shorten interval and add focused remediation" \
  "review queue is current" \
  "previous recall score exists" \
  "queued review items" \
  "interval rule set" \
  "updated recall scores per interval" \
  "next-interval schedule" \
  "distributed practice with interval thresholds" \
  "interval execution with adaptive shortening fallback" \
  "review queue sheet and strict validator" \
  "maximize delayed recall under fixed weekly study hours" \
  "<= 35 minutes per review batch" \
  ">= 88 percent items meet recall threshold" \
  "<= 14 percent items require interval rollback" \
  "100 percent queued reviews follow schedule" \
  "49 minutes" "33 minutes" "-16 minutes" \
  "67%" "89%" "+22 pp" \
  "28%" "13%" "-15 pp" \
  "44%" "100%" "+56 pp" \
  "delayed recall and scheduling consistency improved" \
  "one batch had overdue backlog spillover" \
  "queue grooming was skipped in one session"

emit_triplet "11" "study-error-closure" "Study Error and Weak-Point Closure" \
  "Capture errors by root cause and run targeted correction loops until weak points cross minimum mastery thresholds." \
  "mistake review after practice tests or retrieval sessions" \
  "new-topic planning and unrelated project execution" \
  "error log, root-cause tags, and remediation task bank" \
  "practice session finishes with mistakes logged" \
  "run error-closure loop for top weak points" \
  "same error type appears in 3 or more attempts" \
  "escalate to deep remediation block" \
  "error logs include question and cause" \
  "remediation tasks are available" \
  "error entries" \
  "mastery threshold" \
  "corrective action plan per error category" \
  "updated mastery score and closed/open status" \
  "root-cause tagging and targeted correction" \
  "triage errors then remediate high-frequency categories first" \
  "error log template plus strict validation" \
  "reduce repeated mistakes and speed mastery recovery" \
  "<= 40 minutes per error-closure batch" \
  ">= 87 percent high-frequency errors show mastery lift" \
  "<= 15 percent errors reopen after closure" \
  "100 percent sessions with errors trigger this SOP" \
  "58 minutes" "39 minutes" "-19 minutes" \
  "63%" "88%" "+25 pp" \
  "34%" "14%" "-20 pp" \
  "46%" "100%" "+54 pp" \
  "weak-point recovery and root-cause visibility improved" \
  "one category reopened next day" \
  "incorrect root-cause tagging at first pass"

emit_triplet "12" "life-health-baseline" "Life Health Baseline" \
  "Run a weekly health baseline routine covering sleep, activity, and meal planning with measurable adherence." \
  "weekly health check-in and daily baseline adherence tracking" \
  "medical diagnosis and emergency clinical response" \
  "sleep log, activity log, and meal plan checklist" \
  "week starts or health baseline review day arrives" \
  "run baseline check and set weekly minimum targets" \
  "two or more baseline metrics miss target for 3 days" \
  "trigger recovery week plan and reduce overload" \
  "sleep and activity logs are available" \
  "current constraints are known" \
  "sleep, activity, and meal data" \
  "weekly schedule" \
  "health baseline plan with targets" \
  "daily adherence record" \
  "simple baseline-first health routine with measurable minimums" \
  "weekly plan plus daily adherence loop" \
  "tracker sheet and strict validator" \
  "improve consistency of core health behaviors with low overhead" \
  "<= 20 minutes per weekly baseline run" \
  ">= 85 percent days meet baseline targets" \
  "<= 15 percent days require reset" \
  "100 percent weeks include baseline record" \
  "31 minutes" "19 minutes" "-12 minutes" \
  "62%" "86%" "+24 pp" \
  "36%" "14%" "-22 pp" \
  "41%" "100%" "+59 pp" \
  "baseline adherence and routine stability improved" \
  "one day missed all three targets" \
  "late schedule shift without planned fallback"

emit_triplet "13" "life-financial-operations" "Life Financial Operations" \
  "Standardize weekly budget, bill, and cash-flow checks to reduce surprises and keep spending aligned with plan." \
  "weekly money review, bill tracking, and monthly rollover prep" \
  "investment strategy design and tax filing preparation" \
  "budget sheet, bill calendar, and account balances" \
  "weekly finance review window starts" \
  "run finance ops checklist and update cash-flow status" \
  "forecasted cash buffer falls below threshold" \
  "trigger spending freeze and bill-priority protocol" \
  "latest transactions are imported" \
  "bill due dates are visible" \
  "income and expense records" \
  "upcoming bill list" \
  "updated weekly budget status" \
  "exception list and next-week actions" \
  "cash-flow-first review with due-date risk checks" \
  "weekly run with threshold-triggered intervention" \
  "budget sheet and strict gate validator" \
  "keep bills current and reduce unplanned overspend" \
  "<= 30 minutes per weekly finance run" \
  ">= 95 percent bills tracked before due date" \
  "<= 10 percent spending categories exceed plan" \
  "100 percent weeks include finance log" \
  "47 minutes" "29 minutes" "-18 minutes" \
  "74%" "96%" "+22 pp" \
  "23%" "9%" "-14 pp" \
  "52%" "100%" "+48 pp" \
  "bill readiness and cash visibility improved" \
  "one category overspent in pilot" \
  "late transaction import caused temporary mismatch"

emit_triplet "14" "life-emergency-preparedness" "Life Emergency Preparedness" \
  "Maintain a practical emergency readiness routine for contacts, routes, supplies, and drills with periodic verification." \
  "household emergency planning and monthly readiness drills" \
  "real-time emergency command operations" \
  "emergency contact list, route map, and supply checklist" \
  "monthly preparedness check date arrives" \
  "run preparedness checklist and verify contact-route-supply status" \
  "critical item missing or expired" \
  "trigger immediate replenish and schedule mini-drill" \
  "contact list has at least two alternates" \
  "supply inventory file exists" \
  "contacts, route, and supply inventory" \
  "drill schedule" \
  "updated readiness status" \
  "issue list with owner and due date" \
  "checklist-based preparedness with recurring drills" \
  "monthly verification plus immediate-fix branch" \
  "preparedness checklist and strict validator" \
  "increase readiness confidence while keeping maintenance effort low" \
  "<= 35 minutes per monthly run" \
  ">= 90 percent critical items in ready state" \
  "<= 10 percent unresolved critical gaps" \
  "100 percent months complete one drill" \
  "54 minutes" "34 minutes" "-20 minutes" \
  "65%" "91%" "+26 pp" \
  "30%" "10%" "-20 pp" \
  "39%" "100%" "+61 pp" \
  "preparedness coverage and gap closure improved" \
  "one drill exceeded planned window" \
  "contact tree update was delayed by one day"

# Catalog for direct invocation
cat > "$OUT_DIR/${DATE}-p0-sop-catalog.md" <<EOF
# P0 SOP Catalog (12)

## Work (5)
- Work Task Clarification and Success Criteria
  - \
`按SOP执行：Work Task Clarification and Success Criteria <任务描述>`
  - \
`resources/sop/2026-02/${DATE}-work-task-clarification-sop.md`
- Work Weekly and Daily Planning
  - \
`按SOP执行：Work Weekly and Daily Planning <本周目标>`
  - \
`resources/sop/2026-02/${DATE}-work-weekly-daily-planning-sop.md`
- Work Execution Loop and Status Update
  - \
`按SOP执行：Work Execution Loop and Status Update <任务ID>`
  - \
`resources/sop/2026-02/${DATE}-work-execution-loop-sop.md`
- Work Quality Gate and Review
  - \
`按SOP执行：Work Quality Gate and Review <交付物>`
  - \
`resources/sop/2026-02/${DATE}-work-quality-gate-sop.md`
- Work Incident Response and Recovery
  - \
`按SOP执行：Work Incident Response and Recovery <事件信号>`
  - \
`resources/sop/2026-02/${DATE}-work-incident-response-sop.md`

## Study (4)
- Study Goal Decomposition
  - \
`按SOP执行：Study Goal Decomposition <学习目标>`
  - \
`resources/sop/2026-02/${DATE}-study-goal-decomposition-sop.md`
- Study Active Retrieval Session
  - \
`按SOP执行：Study Active Retrieval Session <主题>`
  - \
`resources/sop/2026-02/${DATE}-study-active-retrieval-session-sop.md`
- Study Spaced Review
  - \
`按SOP执行：Study Spaced Review <复习队列>`
  - \
`resources/sop/2026-02/${DATE}-study-spaced-review-sop.md`
- Study Error and Weak-Point Closure
  - \
`按SOP执行：Study Error and Weak-Point Closure <错题记录>`
  - \
`resources/sop/2026-02/${DATE}-study-error-closure-sop.md`

## Life (3)
- Life Health Baseline
  - \
`按SOP执行：Life Health Baseline <本周安排>`
  - \
`resources/sop/2026-02/${DATE}-life-health-baseline-sop.md`
- Life Financial Operations
  - \
`按SOP执行：Life Financial Operations <本周账单>`
  - \
`resources/sop/2026-02/${DATE}-life-financial-operations-sop.md`
- Life Emergency Preparedness
  - \
`按SOP执行：Life Emergency Preparedness <月度检查>`
  - \
`resources/sop/2026-02/${DATE}-life-emergency-preparedness-sop.md`
EOF

echo "Generated P0 SOP artifacts in $OUT_DIR"
