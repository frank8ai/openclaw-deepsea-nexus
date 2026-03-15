# Deep-Sea Nexus v5.1.0 Upgrade Plan

Date: 2026-03-14

## Positioning

- Current stable baseline: `v5.0.0` (+ hotfix 1)
- Target version: `v5.1.0`
- Goal: start the first governance-focused optimization wave on top of the
  stable baseline

## Upgrade Theme

`v5.1.0` focuses on governance-layer hardening, not a large rewrite.

Priority order:

1. event/rule observability correctness
2. scope and lifecycle governance quality
3. compatibility-preserving runtime optimization

## Workstreams

### WS-1 Event governance correctness

- Make wildcard subscription semantics operational in EventBus.
- Ensure governance subscribers such as `session.*` and `nexus.*` can reliably
  receive events.
- Keep sync + async dispatch compatible.

### WS-2 Scope/lifecycle governance continuation

- Continue hardening scoped memory isolation guarantees.
- Tighten lifecycle operator stories (`audit / archive / backfill`) and docs.

### WS-3 Operations and release surface clarity

- Keep release/docs/version anchors consistent with upgrade lane.
- Preserve `v5.0.0` release baseline references for historical traceability.

## Initial Slice Completed (Kickoff)

Completed in the kickoff slice:

- package version bumped to `5.1.0`
- EventBus wildcard matching implemented (`fnmatch` based)
- wildcard behavior covered by unit tests
- upgrade docs and release-plan entrypoint added

## Validation Gate

Required gate for each incremental slice:

```bash
python3 -m pytest -q
```

Expected:

- no regression on sync compatibility API
- no regression on Memory v5 lifecycle flows
- no regression on runtime plugin lifecycle tests
