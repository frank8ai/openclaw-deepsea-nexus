"""
Memory v5 focused tests.
"""

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PARENT_DIR = REPO_ROOT.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))


def _load_local_package():
    init_path = REPO_ROOT / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        "deepsea_nexus_local",
        init_path,
        submodule_search_locations=[str(REPO_ROOT)],
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


deepsea_nexus = _load_local_package()
MemoryScope = deepsea_nexus.MemoryScope
MemoryV5Service = deepsea_nexus.MemoryV5Service


class TestMemoryV5Scopes(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            "paths": {"base": self.temp_dir},
            "memory_v5": {
                "enabled": True,
                "root": "memory/95_MemoryV5",
                "async_ingest": False,
                "graph_enabled": False,
                "fts_enabled": True,
                "scope": {"agent_id": "default", "user_id": "default"},
            },
        }
        self.service = MemoryV5Service(self.config)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_scope_isolation_and_physical_layout(self):
        scope_main = MemoryScope(agent_id="main", user_id="default")
        scope_writer = MemoryScope(agent_id="writer", user_id="default")

        self.service.ingest_document(
            title="MainScopeDoc",
            content="Main scope keeps this framework decision.",
            tags=["scope-main"],
            scope=scope_main,
        )
        self.service.ingest_document(
            title="WriterScopeDoc",
            content="Writer scope keeps this copy style note.",
            tags=["scope-writer"],
            scope=scope_writer,
        )

        main_hits = self.service.recall("framework decision", limit=3, scope=scope_main)
        writer_hits = self.service.recall("copy style", limit=3, scope=scope_writer)
        cross_hits = self.service.recall("copy style", limit=3, scope=scope_main)

        self.assertTrue(any("MainScopeDoc" in h.title for h in main_hits))
        self.assertTrue(any("WriterScopeDoc" in h.title for h in writer_hits))
        self.assertFalse(any("WriterScopeDoc" in h.title for h in cross_hits))

        main_item_dir = os.path.join(self.temp_dir, "memory/95_MemoryV5/main/default/items")
        writer_item_dir = os.path.join(self.temp_dir, "memory/95_MemoryV5/writer/default/items")
        self.assertTrue(os.path.isdir(main_item_dir))
        self.assertTrue(os.path.isdir(writer_item_dir))
        self.assertGreater(len(os.listdir(main_item_dir)), 0)
        self.assertGreater(len(os.listdir(writer_item_dir)), 0)

    def test_chinese_query_recall(self):
        scope = MemoryScope(agent_id="main", user_id="default")
        self.service.ingest_document(
            title="框架决策",
            content="我们最后采用 FastAPI 作为主框架，并保留 Django 兼容层。",
            tags=["framework"],
            scope=scope,
        )

        hits = self.service.recall("之前我们决定用哪个框架？", limit=5, scope=scope)
        self.assertTrue(any(("FastAPI" in h.content) or ("框架" in h.content) for h in hits))

    def test_archive_item_respects_scope_path(self):
        scope = MemoryScope(agent_id="main", user_id="default")
        result = self.service.ingest_document(
            title="ArchiveDoc",
            content="This note will be archived.",
            tags=["archive-test"],
            scope=scope,
        )
        item_id = str(result.get("item_id", ""))
        self.assertTrue(item_id)

        before_items = self.service.list_items(scope=scope, include_archived=False)
        self.assertTrue(any(row.get("id") == item_id for row in before_items))

        self.assertTrue(self.service.archive_item(item_id, scope=scope))
        after_items = self.service.list_items(scope=scope, include_archived=False)
        self.assertFalse(any(row.get("id") == item_id for row in after_items))


class TestPackageRootExports(unittest.TestCase):
    def test_documented_exports_exist(self):
        required = [
            "nexus_search",
            "nexus_add_document",
            "nexus_add_documents",
            "nexus_write",
            "manual_flush",
            "get_flush_manager",
            "get_session",
            "get_version",
            "SummaryParser",
            "StructuredSummary",
            "create_summary_prompt",
            "parse_summary",
            "ContextEngine",
            "ContextEnginePlugin",
            "get_engine",
            "smart_retrieve",
            "inject_context",
            "detect_trigger",
            "store_summary",
        ]
        for name in required:
            self.assertTrue(hasattr(deepsea_nexus, name), f"missing root export: {name}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
