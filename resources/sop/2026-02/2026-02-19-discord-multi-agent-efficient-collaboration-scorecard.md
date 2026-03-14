# SOP Three-Optimal Scorecard

## Metadata
- Scorecard ID: SCORE-20260219-01
- SOP ID: SOP-20260219-01
- Date: 2026-02-19
- Owner: yizhi
- Constraints summary: Keep main channel summary-only, preserve role/channel routing, no direct cross-subagent pull, and keep rollback simple.

## Candidate Options
| Option | Description | Notes |
|---|---|---|
| A | Single-agent serial execution with no parallel worker split | Lowest setup cost, but high cycle time and context bloat |
| B | Main-agent orchestration with parallel workers and converge gate | Best balance of speed, quality, and token control |
| C | Peer-to-peer worker mesh with direct worker-to-worker negotiation | High flexibility, but high coordination risk and token burn |

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
| A | 3.70 | 2.80 | 3.60 | 4.60 | 3.90 | 3.66 |
| B | 4.60 | 4.30 | 4.40 | 3.90 | 4.10 | 4.35 |
| C | 4.20 | 3.90 | 2.70 | 3.20 | 2.60 | 3.53 |

## Calculation Rule
- Weighted Score = sum(score * weight)
- Highest weighted score wins only if hard constraints pass.
- Release thresholds:
  - Winner weighted score >= 3.50.
  - Winner margin over second option >= 0.20, or explicit override reason.

## Best Practice Evidence
| Practice | Source | Evidence Type | Expected Benefit | Failure Mode |
|---|---|---|---|---|
| Deterministic binding with most-specific-first routing | ${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/.firecrawl/docs-concepts-multi-agent.md | Official product doc | Reduce routing ambiguity and wrong-agent replies | Binding order drift causes unexpected routing |
| Role-based routing runs after peer and before guild-only | ${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/.firecrawl/docs-openclaw-channels-discord.md | Official product doc | Keep stable ownership while allowing specialization | Missing role/member intent breaks role routing |
| Baseline secure Discord config and fallback | ${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/docs/discord-multi-agent-setup.md | Internal runbook | Fast recovery and lower misconfiguration risk | Baseline applied once but not maintained |

## Best Method Decision
- Selected method: Option B (main-agent orchestration, parallel workers, explicit converge gate)
- Why this method is best under current constraints: It enforces summary-only main channel, parallel execution, and centralized decision at converge point with clear ownership.
- Rejected alternatives and reasons:
  - A rejected for slow cycle and larger context accumulation.
  - C rejected for cross-talk loops and unstable accountability.

## Best Tool Decision
| Tool | Role | Measured Gain | Risk | Rollback Path |
|---|---|---|---|---|
| OpenClaw bindings | Stable agent routing | Wrong-route rate down >= 40% | Misordered bindings | Restore previous openclaw.json backup |
| Structured file drop (`agent/`, `docs/`, `logs/`) | Keep long artifacts off main channel | Main-channel token use down >= 50% | Path discipline drift | Revert to fixed path checklist in SOP |
| Main converge checklist | Final acceptance gate | Rework rounds down >= 30% | Over-check slows urgent fixes | Switch to minimum converge checklist for hotfix window |

## Hard Constraint Check
- [x] Budget constraint passed.
- [x] Time constraint passed.
- [x] Compliance or policy constraint passed.
- [x] Team capability constraint passed.

## Final Selection
- Winner option: B
- Winner weighted score: 4.35
- Runner-up weighted score: 3.66
- Margin: 0.69
- Override reason (required when margin < 0.20): n/a
- Approval: approved
- Effective from: 2026-02-19
