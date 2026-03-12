"""Deprecated compatibility wrapper for the legacy plugin module.

The current implementation lives in ``plugins.nexus_core_plugin``. Keep this
module importable while older scripts and references are migrated.
"""

from .nexus_core_plugin import NexusCorePlugin, RecallResult

__all__ = ["NexusCorePlugin", "RecallResult"]
