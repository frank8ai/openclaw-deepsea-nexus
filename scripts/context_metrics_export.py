#!/usr/bin/env python3
"""
Export context metrics for Control UI canvas
Writes JSON (and optional HTML) into ~/.openclaw/canvas/
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List


def resolve_openclaw_home() -> Path:
    return Path(os.environ.get("OPENCLAW_HOME", "~/.openclaw")).expanduser().resolve()


def resolve_workspace_root() -> Path:
    return Path(
        os.environ.get("OPENCLAW_WORKSPACE", resolve_openclaw_home() / "workspace")
    ).expanduser().resolve()


def resolve_canvas_output_path() -> Path:
    return (resolve_openclaw_home() / "canvas" / "context-metrics.json").resolve()


def _read_jsonl(path: str, limit: int = 2000) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    if len(rows) > limit:
        rows = rows[-limit:]
    return rows


def _avg(values: List[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / max(1, len(values))


def build_payload(base_path: str, window: int = 200) -> Dict[str, Any]:
    log_dir = os.path.join(base_path, "logs")
    smart_path = os.path.join(log_dir, "smart_context_metrics.log")
    engine_path = os.path.join(log_dir, "context_engine_metrics.log")

    smart_rows = _read_jsonl(smart_path, limit=5000)
    engine_rows = _read_jsonl(engine_path, limit=5000)

    smart_recent = smart_rows[-window:]
    engine_recent = engine_rows[-window:]

    inject_rows = [r for r in smart_recent if r.get("event") == "inject"]
    engine_builds = [r for r in engine_recent if r.get("event") == "context_build"]

    inject_series = []
    for r in inject_rows:
        inject_series.append(
            {
                "ts": r.get("ts"),
                "ratio": float(r.get("ratio", 0.0)),
                "retrieved": int(r.get("retrieved", 0)),
                "injected": int(r.get("injected", 0)),
                "reason": r.get("reason", "unknown"),
            }
        )

    token_series = []
    for r in engine_builds:
        token_series.append(
            {
                "ts": r.get("ts"),
                "tokens": int(r.get("tokens", 0)),
                "items": int(r.get("items_used", 0)),
                "lines": int(r.get("lines", 0)),
            }
        )

    ratios = [p["ratio"] for p in inject_series]
    tokens = [p["tokens"] for p in token_series]
    items = [p["items"] for p in token_series]

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "window": window,
        "summary": {
            "inject_avg_ratio": round(_avg(ratios), 3),
            "inject_events": len(inject_series),
            "avg_tokens": round(_avg(tokens), 1),
            "avg_items": round(_avg(items), 2),
        },
        "inject_series": inject_series,
        "token_series": token_series,
    }


def _write_html(path: str) -> None:
    html = """<!doctype html>
<html lang="zh-Hans">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Context Metrics</title>
  <style>
    body { font-family: ui-sans-serif, system-ui, -apple-system, Helvetica, Arial; margin: 16px; color: #111; }
    h1 { font-size: 20px; margin-bottom: 4px; }
    .meta { color: #666; font-size: 12px; margin-bottom: 12px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    canvas { width: 100%; height: 260px; border: 1px solid #eee; border-radius: 8px; }
    .card { border: 1px solid #eee; border-radius: 8px; padding: 10px; }
  </style>
</head>
<body>
  <h1>Context Metrics</h1>
  <div class="meta" id="meta">loading...</div>
  <div class="grid">
    <div class="card">
      <strong>Inject Ratio</strong>
      <canvas id="injectCanvas" width="600" height="260"></canvas>
    </div>
    <div class="card">
      <strong>Context Tokens</strong>
      <canvas id="tokenCanvas" width="600" height="260"></canvas>
    </div>
  </div>
  <script>
    async function load() {
      const res = await fetch('./context-metrics.json', { cache: 'no-store' });
      const data = await res.json();
      document.getElementById('meta').textContent =
        `generated=${data.generated_at} | inject_avg_ratio=${data.summary.inject_avg_ratio} | avg_tokens=${data.summary.avg_tokens}`;
      drawLine('injectCanvas', data.inject_series.map(p => p.ratio), 1.0);
      drawLine('tokenCanvas', data.token_series.map(p => p.tokens), Math.max(1, ...data.token_series.map(p => p.tokens)));
    }
    function drawLine(id, series, maxY) {
      const canvas = document.getElementById(id);
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.strokeStyle = '#1f6feb';
      ctx.lineWidth = 2;
      const pad = 20;
      const w = canvas.width - pad * 2;
      const h = canvas.height - pad * 2;
      const n = Math.max(1, series.length);
      ctx.beginPath();
      series.forEach((v, i) => {
        const x = pad + (w * (i / Math.max(1, n - 1)));
        const y = pad + h - (h * (v / Math.max(1, maxY)));
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
    }
    load();
  </script>
</body>
</html>
"""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=str(resolve_workspace_root()))
    parser.add_argument("--window", type=int, default=200)
    parser.add_argument("--out", default=str(resolve_canvas_output_path()))
    parser.add_argument("--write-html", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args.base, args.window)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    if args.write_html:
        html_path = os.path.join(os.path.dirname(args.out), "context-metrics.html")
        _write_html(html_path)


if __name__ == "__main__":
    main()
