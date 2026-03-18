#!/usr/bin/env python3
"""
Daily SmartContext parameter advisor (report-only).

Reads hook compaction metrics from smart_context_metrics.log and generates:
- dated markdown/json reports
- latest markdown/json snapshots

No auto-apply: this script only recommends next parameter values.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _safe_resolve_path(value: Any, fallback: Path) -> Path:
    text = str(value or "").strip()
    if not text:
        return fallback.resolve()
    try:
        return Path(text).expanduser().resolve()
    except RuntimeError:
        # HOME may be unavailable in isolated test envs.
        if text.startswith("~/"):
            home = os.environ.get("HOME") or os.environ.get("USERPROFILE")
            if home:
                return (Path(home) / text[2:]).resolve()
            return (fallback.parent / text[2:]).resolve()
        return Path(text).resolve()


OPENCLAW_HOME = _safe_resolve_path(
    os.environ.get("OPENCLAW_HOME", "~/.openclaw"),
    PROJECT_ROOT / ".openclaw",
)
DEFAULT_WORKSPACE_ROOT = _safe_resolve_path(
    os.environ.get("OPENCLAW_WORKSPACE", OPENCLAW_HOME / "workspace"),
    OPENCLAW_HOME / "workspace",
)


def resolve_default_deepsea_config_path() -> Path:
    override = os.environ.get("DEEPSEA_CONFIG_PATH") or os.environ.get(
        "DEEPSEA_NEXUS_CONFIG"
    )
    if override:
        return _safe_resolve_path(override, PROJECT_ROOT / "config.json")
    return (PROJECT_ROOT / "config.json").resolve()


DEFAULT_METRICS_PATH = (DEFAULT_WORKSPACE_ROOT / "logs" / "smart_context_metrics.log")
DEFAULT_OVERRIDE_PATH = (OPENCLAW_HOME / "state" / "context-optimizer-single-source.json")
DEFAULT_DEEPSEA_CONFIG_PATH = resolve_default_deepsea_config_path()
DEFAULT_REPORT_DIR = (DEFAULT_WORKSPACE_ROOT / "logs" / "smart-context-advisor")
DEFAULT_LOOKBACK_HOURS = 24
DEFAULT_MIN_EVENTS = 8


@dataclass
class ConfigState:
    full_rounds: int
    summary_rounds: int
    compress_after_rounds: int
    source: str


def _to_int(value: Any, fallback: int) -> int:
    try:
        parsed = int(float(value))
    except (TypeError, ValueError):
        return fallback
    if parsed <= 0:
        return fallback
    return parsed


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _parse_iso(ts_raw: Any) -> datetime | None:
    if not ts_raw:
        return None
    text = str(ts_raw).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = (len(ordered) - 1) * p
    lo = int(math.floor(idx))
    hi = int(math.ceil(idx))
    if lo == hi:
        return float(ordered[lo])
    frac = idx - lo
    return float(ordered[lo] + (ordered[hi] - ordered[lo]) * frac)


def _mean(values: List[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def load_current_config(override_path: Path, deepsea_path: Path) -> ConfigState:
    override = _read_json(override_path)
    deepsea = _read_json(deepsea_path)
    deepsea_smart = deepsea.get("smart_context", {}) if isinstance(deepsea, dict) else {}

    if isinstance(override, dict) and override:
        full_rounds = _to_int(override.get("preserveRecent"), 8)
        summary_rounds = _to_int(override.get("compressionThreshold"), 20)
        compress_after_rounds = _to_int(
            override.get("compressAfterRounds"),
            _to_int(deepsea_smart.get("compress_after_rounds"), 35),
        )
        return ConfigState(
            full_rounds=full_rounds,
            summary_rounds=summary_rounds,
            compress_after_rounds=compress_after_rounds,
            source=f"override:{override_path}",
        )

    if isinstance(deepsea_smart, dict) and deepsea_smart:
        return ConfigState(
            full_rounds=_to_int(deepsea_smart.get("full_rounds"), 8),
            summary_rounds=_to_int(deepsea_smart.get("summary_rounds"), 20),
            compress_after_rounds=_to_int(deepsea_smart.get("compress_after_rounds"), 35),
            source=f"deepsea:{deepsea_path}",
        )

    return ConfigState(full_rounds=8, summary_rounds=20, compress_after_rounds=35, source="defaults")


def load_hook_compactions(metrics_path: Path, cutoff_utc: datetime) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not metrics_path.exists():
        return rows

    with metrics_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            raw = line.strip()
            if not raw:
                continue
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if event.get("event") != "hook_compaction":
                continue
            ts = _parse_iso(event.get("ts"))
            if ts is None or ts < cutoff_utc:
                continue
            event["_ts"] = ts.isoformat()
            rows.append(event)

    return rows


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    reasons = Counter()
    hooks = Counter()
    modes = Counter()
    sessions = Counter()
    sources = Counter()
    history_rounds: List[float] = []
    tokens_saved: List[float] = []
    token_estimate: List[float] = []
    effective_keep: List[float] = []
    effective_summary: List[float] = []
    effective_compress: List[float] = []
    policy_refresh_count = 0
    policy_l2_written_count = 0
    fallback_used = 0

    for row in rows:
        reason = str(row.get("reason") or "unknown")
        reasons[reason] += 1
        hooks[str(row.get("hook_phase") or "unknown")] += 1
        modes[str(row.get("mode") or "unknown")] += 1
        sessions[str(row.get("session_key") or "unknown")] += 1
        sources[str(row.get("history_source") or "event")] += 1
        if bool(row.get("fallback_used")):
            fallback_used += 1

        history_length = _to_int(row.get("history_length"), 0)
        if history_length > 0:
            history_rounds.append(float(math.ceil(history_length / 2)))
        tokens_saved.append(float(_to_int(row.get("tokens_saved"), 0)))
        token_estimate.append(float(_to_int(row.get("token_estimate"), 0)))
        effective_keep.append(float(_to_int(row.get("effective_preserve_recent"), 0)))
        effective_summary.append(float(_to_int(row.get("effective_summary_rounds"), 0)))
        effective_compress.append(float(_to_int(row.get("effective_compress_after_rounds"), 0)))
        if bool(row.get("policy_v2_refreshed")):
            policy_refresh_count += 1
        if bool(row.get("policy_v2_l2_written")):
            policy_l2_written_count += 1

    total = len(rows)
    return {
        "total_events": total,
        "reasons": reasons,
        "hooks": hooks,
        "modes": modes,
        "sessions": sessions,
        "sources": sources,
        "fallback_used_count": fallback_used,
        "fallback_used_ratio": (fallback_used / total) if total else 0.0,
        "history_rounds_p50": _percentile(history_rounds, 0.5),
        "history_rounds_p75": _percentile(history_rounds, 0.75),
        "history_rounds_p90": _percentile(history_rounds, 0.9),
        "history_rounds_avg": _mean(history_rounds),
        "tokens_saved_sum": int(sum(tokens_saved)),
        "tokens_saved_avg": _mean(tokens_saved),
        "token_estimate_avg": _mean(token_estimate),
        "effective_preserve_recent_p50": _percentile(effective_keep, 0.5),
        "effective_summary_rounds_p50": _percentile(effective_summary, 0.5),
        "effective_compress_after_rounds_p50": _percentile(effective_compress, 0.5),
        "policy_refresh_ratio": (policy_refresh_count / total) if total else 0.0,
        "policy_l2_written_ratio": (policy_l2_written_count / total) if total else 0.0,
    }


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def _normalized_config(full_rounds: int, summary_rounds: int, compress_after_rounds: int) -> Tuple[int, int, int]:
    full_rounds = _clamp(full_rounds, 6, 24)
    summary_rounds = _clamp(summary_rounds, full_rounds + 6, 72)
    compress_after_rounds = _clamp(compress_after_rounds, summary_rounds + 8, 120)
    return full_rounds, summary_rounds, compress_after_rounds


def recommend(current: ConfigState, stats: Dict[str, Any], min_events: int) -> Dict[str, Any]:
    total = int(stats.get("total_events", 0))
    reasons: Counter = stats.get("reasons", Counter())
    hard_ratio = (reasons.get("token:hard-ratio", 0) / total) if total else 0.0
    soft_ratio = (reasons.get("token:soft-ratio", 0) / total) if total else 0.0
    late_ratio = (
        (
            reasons.get("smart:intelligent-compress-rounds", 0)
            + reasons.get("smart:compress-after-rounds", 0)
            + reasons.get("smart:summary-rounds", 0)
            + reasons.get("smart:summary-window-rounds", 0)
        )
        / total
        if total
        else 0.0
    )
    avg_saved = float(stats.get("tokens_saved_avg", 0.0))
    p90_rounds = float(stats.get("history_rounds_p90", 0.0))
    p50_rounds = float(stats.get("history_rounds_p50", 0.0))

    target_full = current.full_rounds
    target_summary = current.summary_rounds
    target_compress = current.compress_after_rounds
    decision = "keep"
    rationale: List[str] = []

    if total < min_events:
        rationale.append(
            f"样本不足（events={total} < min_events={min_events}），先保持参数，继续累计数据。"
        )
    else:
        if hard_ratio >= 0.20 or p90_rounds >= current.compress_after_rounds + 8:
            decision = "tighten"
            target_full -= 1
            target_summary -= 2
            target_compress -= 3
            rationale.append(
                f"硬触发/尾部轮数偏高（hard_ratio={hard_ratio:.1%}, p90_rounds={p90_rounds:.1f}），建议提前压缩。"
            )
        elif hard_ratio <= 0.05 and late_ratio <= 0.15 and avg_saved < 1500 and p50_rounds < current.summary_rounds * 0.70:
            decision = "loosen"
            target_full += 1
            target_summary += 2
            target_compress += 3
            rationale.append(
                f"硬触发很低且平均节省偏小（hard_ratio={hard_ratio:.1%}, avg_saved={avg_saved:.0f}），可放宽保留原文。"
            )
        else:
            rationale.append(
                f"触发分布平衡（hard_ratio={hard_ratio:.1%}, soft_ratio={soft_ratio:.1%}, late_ratio={late_ratio:.1%}），维持当前设置。"
            )

    full_rounds, summary_rounds, compress_after_rounds = _normalized_config(
        target_full, target_summary, target_compress
    )

    confidence = "low"
    if total >= 30:
        confidence = "high"
    elif total >= min_events:
        confidence = "medium"

    return {
        "decision": decision,
        "confidence": confidence,
        "current": {
            "full_rounds": current.full_rounds,
            "summary_rounds": current.summary_rounds,
            "compress_after_rounds": current.compress_after_rounds,
        },
        "recommended": {
            "full_rounds": full_rounds,
            "summary_rounds": summary_rounds,
            "compress_after_rounds": compress_after_rounds,
        },
        "rationale": rationale,
        "signals": {
            "hard_ratio": hard_ratio,
            "soft_ratio": soft_ratio,
            "late_ratio": late_ratio,
            "avg_tokens_saved": avg_saved,
            "p50_rounds": p50_rounds,
            "p90_rounds": p90_rounds,
        },
    }


def render_markdown(
    now_utc: datetime,
    lookback_hours: int,
    metrics_path: Path,
    stats: Dict[str, Any],
    recommendation: Dict[str, Any],
    config_source: str,
) -> str:
    reasons: Counter = stats.get("reasons", Counter())
    hooks: Counter = stats.get("hooks", Counter())
    modes: Counter = stats.get("modes", Counter())
    sessions: Counter = stats.get("sessions", Counter())
    sources: Counter = stats.get("sources", Counter())

    reason_lines = "\n".join(f"- `{k}`: {v}" for k, v in reasons.most_common()) or "- (none)"
    hook_lines = "\n".join(f"- `{k}`: {v}" for k, v in hooks.most_common()) or "- (none)"
    mode_lines = "\n".join(f"- `{k}`: {v}" for k, v in modes.most_common()) or "- (none)"
    source_lines = "\n".join(f"- `{k}`: {v}" for k, v in sources.most_common()) or "- (none)"
    session_lines = "\n".join(f"- `{k}`: {v}" for k, v in sessions.most_common(8)) or "- (none)"

    rec = recommendation["recommended"]
    cur = recommendation["current"]
    rationale = "\n".join(f"- {line}" for line in recommendation["rationale"])

    return f"""# SmartContext Daily Advisor

- Generated (UTC): `{now_utc.isoformat()}`
- Metrics window: last `{lookback_hours}h`
- Metrics source: `{metrics_path}`
- Config source: `{config_source}`

## Event Snapshot
- Hook compactions: **{stats["total_events"]}**
- Tokens saved total: **{stats["tokens_saved_sum"]}**
- Avg tokens saved / compaction: **{stats["tokens_saved_avg"]:.1f}**
- Avg token estimate / compaction: **{stats["token_estimate_avg"]:.1f}**
- History rounds (avg/p50/p75/p90): **{stats["history_rounds_avg"]:.1f} / {stats["history_rounds_p50"]:.1f} / {stats["history_rounds_p75"]:.1f} / {stats["history_rounds_p90"]:.1f}**
- Effective thresholds p50 (keep/summary/compress): **{stats["effective_preserve_recent_p50"]:.1f} / {stats["effective_summary_rounds_p50"]:.1f} / {stats["effective_compress_after_rounds_p50"]:.1f}**
- Policy v2 refresh ratio: **{stats["policy_refresh_ratio"]:.1%}**
- Policy v2 L2-write ratio: **{stats["policy_l2_written_ratio"]:.1%}**
- Fallback used ratio: **{stats["fallback_used_ratio"]:.1%}**

## Reason Distribution
{reason_lines}

## Hook Phase Distribution
{hook_lines}

## Mode Distribution
{mode_lines}

## History Source Distribution
{source_lines}

## Top Sessions
{session_lines}

## Recommendation
- Decision: **{recommendation["decision"]}**
- Confidence: **{recommendation["confidence"]}**

Current:
- `full_rounds`: {cur["full_rounds"]}
- `summary_rounds`: {cur["summary_rounds"]}
- `compress_after_rounds`: {cur["compress_after_rounds"]}

Recommended:
- `full_rounds`: {rec["full_rounds"]}
- `summary_rounds`: {rec["summary_rounds"]}
- `compress_after_rounds`: {rec["compress_after_rounds"]}

Rationale:
{rationale}

## Safety Notes
- This advisor is **report-only** and does not auto-apply any config.
- Apply only after observing at least 3 days of stable trend.
- Recommended apply path:
  1. update `skills/deepsea-nexus/config.json` (`smart_context` block)
  2. run `python3 skills/deepsea-nexus/scripts/sync_openclaw_context_optimizer.py --apply`
  3. restart gateway and validate `hook_compaction` trends
"""


def write_reports(out_dir: Path, now_local: datetime, markdown: str, payload: Dict[str, Any]) -> Tuple[Path, Path]:
    day_dir = out_dir / now_local.strftime("%Y-%m-%d")
    day_dir.mkdir(parents=True, exist_ok=True)
    stamp = now_local.strftime("%H%M%S")
    md_path = day_dir / f"advisor-{stamp}.md"
    json_path = day_dir / f"advisor-{stamp}.json"

    md_path.write_text(markdown, encoding="utf-8")
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    latest_md = out_dir / "latest.md"
    latest_json = out_dir / "latest.json"
    latest_md.write_text(markdown, encoding="utf-8")
    latest_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return md_path, json_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Daily SmartContext parameter advisor (report-only)")
    parser.add_argument("--metrics", default=str(DEFAULT_METRICS_PATH), help="Path to smart_context_metrics.log")
    parser.add_argument(
        "--override-config",
        default=str(DEFAULT_OVERRIDE_PATH),
        help="Path to context-optimizer single-source override JSON",
    )
    parser.add_argument(
        "--deepsea-config",
        default=str(DEFAULT_DEEPSEA_CONFIG_PATH),
        help="Path to deepsea-nexus config.json",
    )
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR), help="Output report directory")
    parser.add_argument("--lookback-hours", type=int, default=DEFAULT_LOOKBACK_HOURS, help="Lookback window in hours")
    parser.add_argument("--min-events", type=int, default=DEFAULT_MIN_EVENTS, help="Min events required for tuning")
    parser.add_argument("--print-markdown", action="store_true", help="Print markdown to stdout")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    now_utc = datetime.now(timezone.utc)
    now_local = datetime.now()
    cutoff_utc = now_utc - timedelta(hours=max(1, int(args.lookback_hours)))

    metrics_path = Path(args.metrics).expanduser().resolve()
    override_path = Path(args.override_config).expanduser().resolve()
    deepsea_path = Path(args.deepsea_config).expanduser().resolve()
    report_dir = Path(args.report_dir).expanduser().resolve()

    current = load_current_config(override_path, deepsea_path)
    rows = load_hook_compactions(metrics_path, cutoff_utc)
    stats = summarize(rows)
    rec = recommend(current, stats, min_events=max(1, int(args.min_events)))

    markdown = render_markdown(
        now_utc=now_utc,
        lookback_hours=max(1, int(args.lookback_hours)),
        metrics_path=metrics_path,
        stats=stats,
        recommendation=rec,
        config_source=current.source,
    )
    payload = {
        "generated_at_utc": now_utc.isoformat(),
        "lookback_hours": max(1, int(args.lookback_hours)),
        "metrics_path": str(metrics_path),
        "config_source": current.source,
        "stats": {
            "total_events": stats["total_events"],
            "tokens_saved_sum": stats["tokens_saved_sum"],
            "tokens_saved_avg": stats["tokens_saved_avg"],
            "token_estimate_avg": stats["token_estimate_avg"],
            "history_rounds_avg": stats["history_rounds_avg"],
            "history_rounds_p50": stats["history_rounds_p50"],
            "history_rounds_p75": stats["history_rounds_p75"],
            "history_rounds_p90": stats["history_rounds_p90"],
            "fallback_used_ratio": stats["fallback_used_ratio"],
            "effective_preserve_recent_p50": stats["effective_preserve_recent_p50"],
            "effective_summary_rounds_p50": stats["effective_summary_rounds_p50"],
            "effective_compress_after_rounds_p50": stats["effective_compress_after_rounds_p50"],
            "policy_refresh_ratio": stats["policy_refresh_ratio"],
            "policy_l2_written_ratio": stats["policy_l2_written_ratio"],
            "reasons": dict(stats["reasons"]),
            "hooks": dict(stats["hooks"]),
            "modes": dict(stats["modes"]),
            "sources": dict(stats["sources"]),
            "sessions_top8": dict(stats["sessions"].most_common(8)),
        },
        "recommendation": rec,
    }

    md_path, json_path = write_reports(report_dir, now_local, markdown, payload)
    print(f"[advisor] markdown={md_path}")
    print(f"[advisor] json={json_path}")
    print(
        "[advisor] recommended full_rounds={full_rounds} summary_rounds={summary_rounds} compress_after_rounds={compress_after_rounds} (decision={decision}, confidence={confidence})".format(
            full_rounds=rec["recommended"]["full_rounds"],
            summary_rounds=rec["recommended"]["summary_rounds"],
            compress_after_rounds=rec["recommended"]["compress_after_rounds"],
            decision=rec["decision"],
            confidence=rec["confidence"],
        )
    )

    if args.print_markdown:
        print("")
        print(markdown)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
