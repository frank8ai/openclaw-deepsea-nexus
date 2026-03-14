"""Current CLI entrypoint for OpenClaw Deep-Sea Nexus."""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


def _load_local_package():
    repo_root = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location(
        "deepsea_nexus_cli",
        repo_root / "__init__.py",
        submodule_search_locations=[str(repo_root)],
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_package():
    if __package__:
        return sys.modules[__package__]
    return _load_local_package()


def _serialize(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    return value


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deepsea-nexus",
        description="Current OpenClaw Deep-Sea Nexus CLI for version, health, recall, and path checks.",
    )
    subparsers = parser.add_subparsers(dest="command")

    version_parser = subparsers.add_parser("version", help="Print package and API version")
    version_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    health_parser = subparsers.add_parser("health", help="Initialize the sync API and print runtime health")
    health_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    recall_parser = subparsers.add_parser("recall", help="Run a sync recall query")
    recall_parser.add_argument("query", help="Recall query")
    recall_parser.add_argument("-n", "--limit", type=int, default=5, help="Maximum number of hits")
    recall_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    paths_parser = subparsers.add_parser(
        "paths",
        help="Show effective config and key runtime paths",
    )
    paths_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    return parser


def _print_text_results(results: List[Dict[str, Any]]) -> None:
    if not results:
        print("No recall results.")
        return

    for index, item in enumerate(results, start=1):
        relevance = float(item.get("relevance", 0.0))
        source = item.get("source") or "<unknown>"
        content = " ".join(str(item.get("content", "")).split())
        preview = content[:160]
        print(f"{index}. [{relevance:.2f}] {source}")
        if preview:
            print(f"   {preview}")


def _build_paths_payload(package: Any) -> Dict[str, Any]:
    runtime_paths = importlib.import_module(f"{package.__name__}.runtime_paths")
    config_path = package.resolve_default_config_path()
    config = package.ConfigManager(config_path)
    cfg = config.get_all()

    payload = {
        "config_path": config_path,
        "workspace_base": runtime_paths.resolve_workspace_base(
            cfg,
            allow_nexus_base=True,
        ),
        "memory_v5_root": runtime_paths.resolve_memory_root(cfg),
        "vector_db": config.get("nexus.vector_db_path"),
        "collection": config.get("nexus.collection_name"),
        "brain_base_path": config.get("brain.base_path"),
        "package_version": package.__version__,
        "api_version": package.get_version(),
    }
    return payload


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    package = _load_package()

    if args.command == "version":
        payload = {
            "package_version": package.__version__,
            "api_version": package.get_version(),
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"OpenClaw Deep-Sea Nexus {payload['package_version']}")
            print(f"API version: {payload['api_version']}")
        return 0

    if args.command == "health":
        package.nexus_init()
        payload = _serialize(package.nexus_health())
        payload["package_version"] = package.__version__
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"Package version: {payload['package_version']}")
            print(f"Plugin protocol version: {payload.get('version', 'unknown')}")
            print(f"Available: {payload.get('available', False)}")
            print(f"Initialized: {payload.get('initialized', False)}")
            print(f"Documents: {payload.get('documents', 0)}")
        return 0

    if args.command == "recall":
        package.nexus_init()
        results = _serialize(package.nexus_recall(args.query, n=args.limit))
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            _print_text_results(results)
        return 0

    if args.command == "paths":
        payload = _build_paths_payload(package)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"Config path: {payload.get('config_path') or '<none>'}")
            print(f"Workspace base: {payload.get('workspace_base')}")
            print(f"Memory v5 root: {payload.get('memory_v5_root')}")
            print(f"Vector DB: {payload.get('vector_db')}")
            print(f"Collection: {payload.get('collection')}")
            print(f"Brain base path: {payload.get('brain_base_path') or '<none>'}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
