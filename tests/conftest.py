#!/usr/bin/env python
"""
Pytest configuration for Deep-Sea Nexus v2.0
"""

import importlib.util
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def optional_pytest_plugins() -> list[str]:
    # Keep async plugin optional so sync-only test entrypoints still run in lean envs.
    if importlib.util.find_spec("pytest_asyncio") is None:
        return []
    return ["pytest_asyncio"]


pytest_plugins = optional_pytest_plugins()
