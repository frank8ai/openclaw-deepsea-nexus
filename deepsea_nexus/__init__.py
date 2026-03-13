"""Shim package so the repo supports ``import deepsea_nexus`` directly."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_repo_root_package():
    repo_root = Path(__file__).resolve().parent.parent
    spec = importlib.util.spec_from_file_location(
        __name__,
        repo_root / "__init__.py",
        submodule_search_locations=[str(repo_root)],
    )
    if spec is None or spec.loader is None:
        raise ImportError("unable to load Deep-Sea Nexus root package")
    module = importlib.util.module_from_spec(spec)
    sys.modules[__name__] = module
    spec.loader.exec_module(module)
    return module


_module = _load_repo_root_package()
globals().update(_module.__dict__)
