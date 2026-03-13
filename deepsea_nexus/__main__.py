"""Shim module so the repo supports ``python -m deepsea_nexus`` directly."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Optional, Sequence


def _load_repo_root_cli():
    repo_root = Path(__file__).resolve().parent.parent
    spec = importlib.util.spec_from_file_location(
        __name__,
        repo_root / "__main__.py",
    )
    if spec is None or spec.loader is None:
        raise ImportError("unable to load Deep-Sea Nexus CLI")
    module = importlib.util.module_from_spec(spec)
    sys.modules[__name__] = module
    spec.loader.exec_module(module)
    return module


_cli = _load_repo_root_cli()
main = _cli.main


if __name__ == "__main__":
    raise SystemExit(main())
