"""Patch chromadb persistent data loader for compatibility.

In some environments, older persisted collections store index metadata as a
plain dict. Newer chromadb expects a PersistentData object with attributes.
This patch wraps dict -> PersistentData on load.

Must be imported before creating a chromadb client.
"""

from __future__ import annotations

import chromadb.segment.impl.vector.local_persistent_hnsw as lp


_ORIG_LOAD = lp.PersistentData.load_from_file


def _wrap_dict(ret):
    if isinstance(ret, dict):
        return lp.PersistentData(
            dimensionality=ret.get("dimensionality"),
            total_elements_added=ret.get("total_elements_added", 0),
            id_to_label=ret.get("id_to_label", {}),
            label_to_id=ret.get("label_to_id", {}),
            id_to_seq_id=ret.get("id_to_seq_id", {}),
        )
    return ret


@staticmethod
def _patched_load_from_file(filename: str) -> "lp.PersistentData":
    ret = _ORIG_LOAD(filename)
    return _wrap_dict(ret)


lp.PersistentData.load_from_file = _patched_load_from_file
