"""Lightweight psutil stub used for the Deep-Sea Nexus test suite.

The upstream library is optional in this repo. The bundled performance tests
only require enough surface area to report current process RSS.

If real `psutil` is installed, Python will import that instead.
"""

from __future__ import annotations

import os
import resource
from dataclasses import dataclass


@dataclass
class _MemInfo:
    rss: int


class Process:
    def __init__(self, pid: int | None = None):
        self.pid = int(pid or os.getpid())

    def memory_info(self) -> _MemInfo:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        rss_kb = int(getattr(usage, "ru_maxrss", 0) or 0)
        # On macOS, ru_maxrss is in bytes; on Linux it's in KB.
        rss_bytes = rss_kb if rss_kb > 10**9 else rss_kb * 1024
        return _MemInfo(rss=rss_bytes)
