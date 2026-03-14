# Context Policy v2 (Current Canonical)

Updated: 2026-03-14

> Current source of truth for Deep-Sea Nexus context governance.
> Applies to:
> - Python `SmartContext`
> - OpenClaw `context-optimizer` single-source sync
> - current docs and operational checks
> Fixed baseline: `8 / 20 / 35` (`full / summary / compress-after`).

## 1) Non-Negotiables
- All memory must be handled through context governance, not side-channel free-text dumps.
- Keep the round thresholds fixed at `8 / 20 / 35` unless a new canonical policy replaces this document.
- Never do free-form compression before preserving typed critical state.
- `No Evidence, No Memory`:
  - a durable decision without evidence pointer must not enter L2 durable memory.
- Raw logs, stack traces, transcripts, and artifacts stay outside summaries.
  - summaries keep pointers only.

## 2) Compression Stages
- `0-8` rounds:
  - keep full turns.
- `9-20` rounds:
  - keep summary-form context.
- `21-35` rounds:
  - keep compressed summary plus rescued NOW state.
- `>35` rounds:
  - remain in compressed mode, but runtime/hook should surface a stronger `compress_after_rounds` reason and archive posture.

## 3) Three-Layer Memory Model
- `L1 Working Context` (ephemeral, TTL default `24h`):
  - `Goal / Status / Constraints / Blockers / Next / Open Questions`
  - optional runtime details:
    - `Owner / ETA / Risk`
- `L2 Durable Decision`:
  - `Decision / Why / Constraint / Evidence pointer / Reversal condition`
  - only written when evidence exists.
- `L3 Evidence Store`:
  - raw logs, files, commands, artifact ids, hashes, reports, and session traces.
  - L1/L2 store pointers, not raw payloads.

## 4) Pre-Compression Preserve Whitelist
Before any summary-only or compressed state is emitted, preserve these fields when present:

- `Goal / Objective`
- `Current status / phase`
- `Hard constraints`
- `Confirmed decisions`
- `Blockers / risks`
- `Next minimum action`
- `Open questions`
- `Evidence pointers`
  - examples:
    - `path[:line]`
    - `log path`
    - `artifact id/hash`
- `Replay command`
  - prefer one smallest reproducible command

## 5) What Compression Should Drop
- repeated phrasing, chit-chat, and acknowledgement noise
- concluded raw logs or stack traces once their outcome is captured
- obsolete trial branches already superseded by a later decision
- large raw code copied into summaries when the current file path is already known
- any decision text that lacks evidence pointer

## 6) Summary And NOW Contracts
- Default structured summary fields:
  - `Summary`
  - `Goal`
  - `Status`
  - `Decisions`
  - `Constraints`
  - `Blockers`
  - `Next`
  - `Questions`
  - `Evidence`
  - `Replay`
- NOW rescue fields must preserve the same typed state in compact form.
- Keep the handoff human-readable and bounded.
  - target: one line per field, not verbose prose.

## 7) Event-Driven Refresh
Refresh summary state only when one of these events happens:

- decision changed
- status changed
- new blocker appeared
- new validation result appeared
- phase boundary reached
- `compress_after_rounds` triggered
- hard token ratio triggered

If none of the above changed:

- reuse the previous structured summary
- avoid rewriting the same summary every turn

## 8) Runtime Mapping
- Deep-Sea config:
  - `smart_context.full_rounds = 8`
  - `smart_context.summary_rounds = 20`
  - `smart_context.compress_after_rounds = 35`
- OpenClaw single-source override:
  - `preserveRecent <- full_rounds`
  - `compressionThreshold <- summary_rounds`
  - `compressAfterRounds <- compress_after_rounds`
- Python runtime status model:
  - `full`
  - `summary`
  - `compressed`
- Python runtime must still distinguish:
  - `summary_rounds`
  - `compress_after_rounds`
  as separate reasons once it is inside compressed mode.

## 9) Evidence Discipline
- Preferred durable evidence forms:
  - file path
  - report path
  - replay command
  - artifact id/hash
  - log path
- Secrets never belong in L1/L2 text.
  - keep only references such as env var names, file paths, or vault keys.

## 10) Design Inputs
This policy direction aligns with stable external best-practice signals:

- Anthropic long-context guidance:
  - keep context structured and avoid forcing the model to rediscover state from raw history.
  - <https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/long-context-tips>
- OpenAI prompt caching guidance:
  - keep stable prefixes and move changing material to the tail when possible.
  - <https://platform.openai.com/docs/guides/prompt-caching>
- `MemGPT`:
  - separate working context from external memory instead of pretending everything fits in one prompt.
  - <https://arxiv.org/abs/2310.08560>
