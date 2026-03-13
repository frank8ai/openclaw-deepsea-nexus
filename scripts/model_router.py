#!/usr/bin/env python3
"""
Lightweight Model Router (heuristic)
根据输入内容给出低成本/高性能模型建议
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORKSPACE_ROOT = Path(
    os.environ.get(
        "OPENCLAW_WORKSPACE",
        os.path.join(os.path.expanduser("~"), ".openclaw", "workspace"),
    )
).expanduser()


def resolve_config_path(path: str | None = None) -> Path:
    if path:
        return Path(path).expanduser().resolve()

    env_override = os.environ.get("DEEPSEA_CONFIG_PATH") or os.environ.get(
        "DEEPSEA_NEXUS_CONFIG"
    )
    candidates = []
    if env_override:
        candidates.append(Path(env_override).expanduser())
    candidates.extend(
        [
            Path(os.getcwd()) / "config.json",
            PROJECT_ROOT / "config.json",
            DEFAULT_WORKSPACE_ROOT / "skills" / "deepsea-nexus" / "config.json",
        ]
    )

    for candidate in candidates:
        expanded = candidate.expanduser()
        if expanded.exists():
            return expanded.resolve()
    return (PROJECT_ROOT / "config.json").resolve()


def load_config(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def classify(text: str, routing: Dict[str, Any]) -> Dict[str, Any]:
    text = text or ""
    text_lower = text.lower()
    code_keywords = routing.get("code_keywords", [])
    light_max_chars = int(routing.get("light_max_chars", 600))

    is_code = any(k.lower() in text_lower for k in code_keywords)
    is_light = len(text) <= light_max_chars and not is_code

    if is_code:
        model = routing.get("code_model") or routing.get("heavy_model")
        tier = "code"
    elif is_light:
        model = routing.get("light_model")
        tier = "light"
    else:
        model = routing.get("heavy_model")
        tier = "heavy"

    return {
        "tier": tier,
        "model": model,
        "length": len(text),
        "is_code": is_code,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(resolve_config_path()))
    parser.add_argument("--text", default="")
    args = parser.parse_args()

    cfg = load_config(args.config)
    routing = cfg.get("routing", {})
    if not routing or not routing.get("enabled", True):
        print(json.dumps({"error": "routing disabled"}, ensure_ascii=False))
        return

    result = classify(args.text, routing)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
