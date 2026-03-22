#!/usr/bin/env python3
"""Run one Codex periodic ingest scan."""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load_local_package():
    spec = importlib.util.spec_from_file_location(
        "deepsea_nexus_codex_ingest",
        REPO_ROOT / "__init__.py",
        submodule_search_locations=[str(REPO_ROOT)],
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


package = _load_local_package()
plugin_module = importlib.import_module(f"{package.__name__}.plugins.codex_periodic_ingest_plugin")


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    resolved = config_path or package.resolve_default_config_path() or str(REPO_ROOT / "config.json")
    return package.ConfigManager(resolved).get_all()


def run_scan(config: Optional[Dict[str, Any]] = None, config_path: Optional[str] = None) -> Dict[str, Any]:
    cfg = config if isinstance(config, dict) else load_config(config_path)
    plugin = plugin_module.CodexPeriodicIngestPlugin()
    import asyncio

    asyncio.run(plugin.initialize(cfg))
    payload = plugin.scan_once()
    payload["health"] = plugin.get_health_summary()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one Deepsea Codex periodic ingest scan")
    parser.add_argument("--config", default=None, help="Optional config path")
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    args = parser.parse_args()

    payload = run_scan(config_path=args.config)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            "stored={stored_documents} sessions={session_documents} history={history_documents} skipped={skipped}".format(
                **payload
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
