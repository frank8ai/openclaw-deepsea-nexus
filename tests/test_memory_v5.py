"""
Memory v5 focused tests.
"""

import contextlib
import asyncio
import importlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import warnings
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("NEXUS_TEST_MODE", "1")
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
NexusCorePlugin = importlib.import_module(
    f"{deepsea_nexus.__name__}.plugins.nexus_core_plugin"
).NexusCorePlugin
runtime_paths = importlib.import_module(f"{deepsea_nexus.__name__}.runtime_paths")
context_engine_runtime = importlib.import_module(
    f"{deepsea_nexus.__name__}.plugins.context_engine_runtime"
)
smart_context_runtime = importlib.import_module(
    f"{deepsea_nexus.__name__}.plugins.smart_context_runtime"
)
smart_context_conversation = importlib.import_module(
    f"{deepsea_nexus.__name__}.plugins.smart_context_conversation"
)
smart_context_text = importlib.import_module(
    f"{deepsea_nexus.__name__}.plugins.smart_context_text"
)
smart_context_inject = importlib.import_module(
    f"{deepsea_nexus.__name__}.plugins.smart_context_inject"
)
smart_context_module = importlib.import_module(
    f"{deepsea_nexus.__name__}.plugins.smart_context"
)
compat_module = importlib.import_module(f"{deepsea_nexus.__name__}.compat")
smart_context_decision = importlib.import_module(
    f"{deepsea_nexus.__name__}.plugins.smart_context_decision"
)
smart_context_graph = importlib.import_module(
    f"{deepsea_nexus.__name__}.plugins.smart_context_graph"
)
smart_context_rescue = importlib.import_module(
    f"{deepsea_nexus.__name__}.plugins.smart_context_rescue"
)
smart_context_recall = importlib.import_module(
    f"{deepsea_nexus.__name__}.plugins.smart_context_recall"
)
smart_context_graph_inject = importlib.import_module(
    f"{deepsea_nexus.__name__}.plugins.smart_context_graph_inject"
)
smart_context_storage = importlib.import_module(
    f"{deepsea_nexus.__name__}.plugins.smart_context_storage"
)
smart_context_round = importlib.import_module(
    f"{deepsea_nexus.__name__}.plugins.smart_context_round"
)
smart_context_adaptive = importlib.import_module(
    f"{deepsea_nexus.__name__}.plugins.smart_context_adaptive"
)
smart_context_now = importlib.import_module(
    f"{deepsea_nexus.__name__}.plugins.smart_context_now"
)
smart_context_prompt = importlib.import_module(
    f"{deepsea_nexus.__name__}.plugins.smart_context_prompt"
)
smart_context_summary = importlib.import_module(
    f"{deepsea_nexus.__name__}.plugins.smart_context_summary"
)


def _load_script_module(module_name: str):
    script_path = REPO_ROOT / "scripts" / f"{module_name}.py"
    script_dir = str(script_path.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location(
        f"deepsea_nexus_script_{module_name.replace('.', '_')}",
        script_path,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_repo_file_module(module_name: str, relative_path: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(
        f"deepsea_nexus_repo_{module_name.replace('.', '_')}",
        module_path,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _make_stub_module(name: str, **attrs):
    module = ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


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


class TestVersionAndEntrypoints(unittest.TestCase):
    def test_get_version_matches_package_version(self):
        self.assertEqual(deepsea_nexus.get_version(), deepsea_nexus.__version__)

    def test_legacy_plugin_module_forwards_to_current_plugin(self):
        legacy = importlib.import_module(f"{deepsea_nexus.__name__}.plugins.nexus_core")
        current = importlib.import_module(f"{deepsea_nexus.__name__}.plugins.nexus_core_plugin")

        self.assertIs(legacy.NexusCorePlugin, current.NexusCorePlugin)
        self.assertIs(legacy.RecallResult, current.RecallResult)

    def test_cli_version_json(self):
        cli = importlib.import_module(f"{deepsea_nexus.__name__}.__main__")
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = cli.main(["version", "--json"])

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["package_version"], deepsea_nexus.__version__)
        self.assertEqual(payload["api_version"], deepsea_nexus.get_version())

    def test_cli_paths_json(self):
        cli = importlib.import_module(f"{deepsea_nexus.__name__}.__main__")
        stdout = io.StringIO()

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "paths": {"base": temp_dir},
                        "memory_v5": {"root": "memory/95_MemoryV5"},
                        "brain": {"base_path": temp_dir},
                        "nexus": {
                            "vector_db_path": str(Path(temp_dir) / "vector-db"),
                            "collection_name": "test_collection",
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            isolated_env = dict(os.environ)
            isolated_env.pop("NEXUS_VECTOR_DB", None)
            isolated_env.pop("NEXUS_COLLECTION", None)

            with mock.patch.dict(os.environ, isolated_env, clear=True):
                with mock.patch.object(
                    deepsea_nexus,
                    "resolve_default_config_path",
                    return_value=str(config_path),
                ):
                    with contextlib.redirect_stdout(stdout):
                        exit_code = cli.main(["paths", "--json"])

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["config_path"], str(config_path))
        self.assertEqual(payload["workspace_base"], temp_dir)
        self.assertEqual(
            payload["memory_v5_root"],
            str(Path(temp_dir) / "memory/95_MemoryV5"),
        )
        self.assertEqual(payload["vector_db"], str(Path(temp_dir) / "vector-db"))
        self.assertEqual(payload["collection"], "test_collection")
        self.assertEqual(payload["brain_base_path"], temp_dir)

    def test_repo_shim_package_supports_standard_imports(self):
        result = subprocess.run(
            [sys.executable, "-m", "deepsea_nexus", "version", "--json"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["package_version"], deepsea_nexus.__version__)
        self.assertEqual(payload["api_version"], deepsea_nexus.get_version())


class TestCurrentRuntimeFixes(unittest.TestCase):
    def test_add_document_feeds_memory_v5_without_brain(self):
        temp_dir = tempfile.mkdtemp()
        plugin = NexusCorePlugin()
        config = {
            "paths": {"base": temp_dir},
            "memory_v5": {
                "enabled": True,
                "root": "memory/95_MemoryV5",
                "async_ingest": False,
                "graph_enabled": False,
                "fts_enabled": True,
            },
            "brain": {"enabled": False},
        }

        try:
            original_test_mode = os.environ.get("NEXUS_TEST_MODE")
            os.environ["NEXUS_TEST_MODE"] = "1"
            self.assertTrue(asyncio.run(plugin.initialize(config)))
            doc_id = asyncio.run(
                plugin.add_document(
                    content="Memory v5 should receive this document without brain hooks.",
                    title="MemoryV5Write",
                    tags="alpha,beta",
                )
            )
            self.assertTrue(doc_id)
            service = plugin._get_mem_v5_service()
            self.assertIsNotNone(service)
            hits = service.recall("receive this document", limit=5)
            self.assertTrue(any(hit.title == "MemoryV5Write" for hit in hits))
        finally:
            if original_test_mode is None:
                os.environ.pop("NEXUS_TEST_MODE", None)
            else:
                os.environ["NEXUS_TEST_MODE"] = original_test_mode
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_context_engine_falls_back_to_sync_api_adapter(self):
        deepsea_nexus.clear_plugin_registry()
        context_engine_module = importlib.import_module(
            f"{deepsea_nexus.__name__}.plugins.context_engine"
        )
        engine = context_engine_module.ContextEngine()
        adapter = engine.nexus_core

        self.assertIsInstance(adapter, context_engine_module._CompatNexusCoreAdapter)
        self.assertTrue(callable(getattr(adapter, "search_recall", None)))
        self.assertTrue(callable(getattr(adapter, "add_document", None)))

    def test_context_engine_smart_retrieve_uses_budgeted_context_block(self):
        context_engine_module = importlib.import_module(
            f"{deepsea_nexus.__name__}.plugins.context_engine"
        )
        engine = context_engine_module.ContextEngine()
        engine.configure_runtime(
            {
                "paths": {"base": str(REPO_ROOT)},
                "context_engine": {
                    "max_tokens": 1000,
                    "max_items": 2,
                    "max_chars_per_item": 120,
                    "max_lines_total": 12,
                    "include_now": True,
                    "include_recent_summary": True,
                    "include_memory": True,
                },
            }
        )
        engine.should_retrieve = mock.Mock(return_value=(True, "question"))
        engine._search_vector_store = mock.Mock(
            return_value=[
                {
                    "content": "FastAPI keeps the relay control plane stable.",
                    "source": "docs/relay.md",
                    "relevance": 0.91,
                    "metadata": {},
                }
            ]
        )

        with mock.patch.object(
            context_engine_module.smart_context_now,
            "get_rescue_context",
            return_value="## NOW Rescue Context\nGoal: stabilize relay audit",
        ):
            result = engine.smart_retrieve("relay audit", n=1)

        self.assertTrue(result.triggered)
        self.assertEqual(result.trigger_type, "question")
        self.assertIn("## NOW", result.context_text)
        self.assertIn("Goal: stabilize relay audit", result.context_text)
        self.assertNotIn("## NOW Rescue Context", result.context_text)
        self.assertIn("## RECALL (Top-K)", result.context_text)
        self.assertIn("[1] (docs/relay.md · 0.91)", result.context_text)


class TestLegacyMaintenanceScripts(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir) / "repo"
        self.workspace_root = Path(self.temp_dir) / "workspace"
        self.repo_root.mkdir(parents=True, exist_ok=True)
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        (self.repo_root / "config.json").write_text(
            json.dumps(
                {
                    "paths": {
                        "base": str(self.workspace_root),
                        "memory": "memory/90_Memory",
                    }
                }
            ),
            encoding="utf-8",
        )
        self.legacy_layout = _load_script_module("_legacy_layout")
        self.index_rebuild = _load_script_module("index_rebuild")

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_resolve_legacy_layout_uses_repo_config(self):
        layout = self.legacy_layout.resolve_legacy_layout(repo_root=self.repo_root)

        self.assertEqual(layout.repo_root, self.repo_root.resolve())
        self.assertEqual(layout.workspace_root, self.workspace_root.resolve())
        self.assertEqual(
            layout.memory_root,
            (self.workspace_root / "memory" / "90_Memory").resolve(),
        )

    def test_daily_flush_moves_sessions_into_month_archive(self):
        layout = self.legacy_layout.resolve_legacy_layout(repo_root=self.repo_root)
        date_str = "2026-03-13"
        day_dir = layout.memory_root / date_str
        day_dir.mkdir(parents=True, exist_ok=True)
        session_path = day_dir / "session_1200_Test.md"
        session_path.write_text("# test\n", encoding="utf-8")
        (day_dir / "_INDEX.md").write_text("old index", encoding="utf-8")

        stats = self.legacy_layout.daily_flush_legacy_layout(date_str=date_str, layout=layout)

        archived_path = layout.memory_root / "2026-03" / session_path.name
        self.assertEqual(stats["flushed_count"], 1)
        self.assertEqual(stats["archive_dir"], str((layout.memory_root / "2026-03").resolve()))
        self.assertFalse(session_path.exists())
        self.assertTrue(archived_path.exists())
        self.assertIn(
            "# 2026-03-13 Daily Index",
            (day_dir / "_INDEX.md").read_text(encoding="utf-8"),
        )

    def test_rebuild_all_filters_flat_daily_dirs_by_month(self):
        layout = self.legacy_layout.resolve_legacy_layout(repo_root=self.repo_root)
        target_dir = layout.memory_root / "2026-02-10"
        target_dir.mkdir(parents=True, exist_ok=True)
        other_dir = layout.memory_root / "2026-03-01"
        other_dir.mkdir(parents=True, exist_ok=True)

        (target_dir / "session_0930_Test.md").write_text(
            """---
tags: [Testing]
created: 2026-02-10T09:30:00
---

# Test

#GOLD important regression keyword
""",
            encoding="utf-8",
        )
        (other_dir / "session_1015_Other.md").write_text("# noop\n", encoding="utf-8")

        results = self.index_rebuild.rebuild_all(layout, month="2026-02")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["date"], "2026-02-10")
        self.assertTrue((target_dir / "_INDEX.md").exists())
        self.assertFalse((other_dir / "_INDEX.md").exists())


class TestImportSessionsScript(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir) / "repo"
        self.workspace_root = Path(self.temp_dir) / "workspace"
        self.repo_root.mkdir(parents=True, exist_ok=True)
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.import_sessions = _load_script_module("import_sessions")

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_resolve_config_path_prefers_config_json(self):
        json_path = self.repo_root / "config.json"
        yaml_path = self.repo_root / "config.yaml"
        json_path.write_text('{"paths": {"base": "json-base"}}', encoding="utf-8")
        yaml_path.write_text("paths:\n  base: yaml-base\n", encoding="utf-8")

        resolved = self.import_sessions.resolve_config_path(nexus_root=self.repo_root)

        self.assertEqual(resolved, json_path.resolve())

    def test_build_default_session_dirs_discovers_repo_and_workspace_roots(self):
        repo_session_dir = self.repo_root / "memory" / "90_Memory" / "2026-02"
        workspace_session_dir = self.workspace_root / "memory" / "90_Memory" / "2026-03"
        repo_session_dir.mkdir(parents=True, exist_ok=True)
        workspace_session_dir.mkdir(parents=True, exist_ok=True)
        (repo_session_dir / "session_0900_Repo.md").write_text("# repo\n", encoding="utf-8")
        (workspace_session_dir / "session_1000_Workspace.md").write_text(
            "# workspace\n",
            encoding="utf-8",
        )

        session_dirs = self.import_sessions.build_default_session_dirs(
            workspace_root=self.workspace_root,
            nexus_root=self.repo_root,
        )

        self.assertEqual(
            set(session_dirs),
            {
                str(repo_session_dir.resolve()),
                str(workspace_session_dir.resolve()),
            },
        )


class TestLegacyEntryHelpers(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir) / "repo"
        self.workspace_root = Path(self.temp_dir) / "workspace"
        self.repo_root.mkdir(parents=True, exist_ok=True)
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.import_sessions_simple = _load_script_module("import_sessions_simple")
        self.import_sessions_sqlite = _load_script_module("import_sessions_sqlite")
        self.auto_recall = _load_repo_file_module("auto_recall", "auto_recall.py")

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_import_sessions_simple_uses_current_metadata_key(self):
        session_dir = self.repo_root / "memory" / "90_Memory" / "2026-03"
        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / "session_0900_Test.md").write_text(
            """---
title: Test Session
tags: [alpha, beta]
created: 2026-03-13T09:00:00
---

Session body
""",
            encoding="utf-8",
        )

        collection = SimpleNamespace()
        add_calls = []

        def _add(**kwargs):
            add_calls.append(kwargs)

        collection.add = _add

        stats = self.import_sessions_simple.import_sessions(str(session_dir), collection)

        self.assertEqual(stats["imported"], 1)
        self.assertEqual(stats["failed"], 0)
        self.assertEqual(len(add_calls), 1)
        self.assertIn("metadatas", add_calls[0])
        self.assertNotIn("metadatars", add_calls[0])
        self.assertEqual(add_calls[0]["metadatas"][0]["title"], "Test Session")

    def test_import_sessions_sqlite_discovers_repo_and_workspace_roots(self):
        repo_session_dir = self.repo_root / "memory" / "90_Memory" / "2026-02"
        workspace_session_dir = self.workspace_root / "memory" / "90_Memory" / "2026-03"
        repo_session_dir.mkdir(parents=True, exist_ok=True)
        workspace_session_dir.mkdir(parents=True, exist_ok=True)
        (repo_session_dir / "session_0900_Repo.md").write_text("# repo\n", encoding="utf-8")
        (workspace_session_dir / "session_1000_Workspace.md").write_text(
            "# workspace\n",
            encoding="utf-8",
        )

        session_dirs = self.import_sessions_sqlite.build_default_session_dirs(
            workspace_root=self.workspace_root,
            nexus_root=self.repo_root,
        )

        self.assertEqual(
            set(session_dirs),
            {
                str(repo_session_dir.resolve()),
                str(workspace_session_dir.resolve()),
            },
        )

    def test_auto_recall_prefers_current_repo_config_json(self):
        json_path = self.repo_root / "config.json"
        yaml_path = self.repo_root / "config.yaml"
        json_path.write_text('{"paths": {"base": "json-base"}}', encoding="utf-8")
        yaml_path.write_text("paths:\n  base: yaml-base\n", encoding="utf-8")

        resolved = self.auto_recall.resolve_config_path(nexus_root=self.repo_root)
        recall = self.auto_recall.AutoRecall(
            use_socket=False,
            nexus_root=str(self.repo_root),
        )

        self.assertEqual(resolved, json_path.resolve())
        self.assertEqual(recall.nexus_root, self.repo_root.resolve())
        self.assertEqual(recall.config_path, str(json_path.resolve()))


class TestNextThreeCuts(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir) / "repo"
        self.workspace_root = Path(self.temp_dir) / "workspace"
        self.repo_root.mkdir(parents=True, exist_ok=True)
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.import_all = _load_script_module("import_all")

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_import_all_discovers_session_rescue_and_daily_sources(self):
        repo_session_dir = self.repo_root / "memory" / "90_Memory" / "2026-02"
        repo_session_dir.mkdir(parents=True, exist_ok=True)
        (repo_session_dir / "session_0900_Repo.md").write_text("# repo\n", encoding="utf-8")

        workspace_rescue_dir = (
            self.workspace_root / "Obsidian" / "90_Memory" / "2026-02-11-Rescue"
        )
        workspace_rescue_dir.mkdir(parents=True, exist_ok=True)
        (workspace_rescue_dir / "SESSION_0900_Rescue.md").write_text(
            "# rescue\n",
            encoding="utf-8",
        )

        repo_daily = self.repo_root / "memory" / "2026-03-13.md"
        repo_daily.parent.mkdir(parents=True, exist_ok=True)
        repo_daily.write_text("# daily\n", encoding="utf-8")

        session_dirs = self.import_all.build_default_session_dirs(
            workspace_root=self.workspace_root,
            nexus_root=self.repo_root,
        )
        rescue_dirs = self.import_all.build_default_rescue_dirs(
            workspace_root=self.workspace_root,
            nexus_root=self.repo_root,
        )
        daily_files = self.import_all.build_default_daily_files(
            workspace_root=self.workspace_root,
            nexus_root=self.repo_root,
        )

        self.assertEqual(session_dirs, [str(repo_session_dir.resolve())])
        self.assertEqual(rescue_dirs, [str(workspace_rescue_dir.resolve())])
        self.assertEqual(daily_files, [str(repo_daily.resolve())])

    def test_src_config_supports_yaml_and_current_base_override(self):
        config_dir = Path(self.temp_dir) / "config-cwd"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_yaml = config_dir / "config.yaml"
        config_yaml.write_text(
            "paths:\n  base: ~/yaml-nexus\nindex:\n  max_index_tokens: 123\n",
            encoding="utf-8",
        )

        with mock.patch.dict(
            os.environ,
            {"DEEPSEA_NEXUS_ROOT": str(self.repo_root)},
            clear=False,
        ):
            with mock.patch("os.getcwd", return_value=str(config_dir)):
                config_module = _load_repo_file_module("src_config_yaml", "src/config.py")
                self.assertEqual(config_module.config.get("index.max_index_tokens"), 123)
                self.assertEqual(
                    config_module.resolve_default_base_path(),
                    str(self.repo_root.resolve()),
                )
                self.assertEqual(
                    config_module.config.get("paths.base"),
                    str(Path("~/yaml-nexus").expanduser().resolve()),
                )

    def test_src_data_structures_base_path_prefers_current_repo_override(self):
        with mock.patch.dict(
            os.environ,
            {"DEEPSEA_NEXUS_ROOT": str(self.repo_root)},
            clear=False,
        ):
            data_structures_module = _load_repo_file_module(
                "src_data_structures_current_base",
                "src/data_structures.py",
            )
            config = data_structures_module.NexusConfig()
            self.assertEqual(config.base_path, str(self.repo_root.resolve()))


class TestAnotherThreeCuts(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir) / "repo"
        self.repo_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_nexus_core_default_base_prefers_current_repo_override(self):
        with mock.patch.dict(
            os.environ,
            {"DEEPSEA_NEXUS_ROOT": str(self.repo_root)},
            clear=False,
        ):
            nexus_core_module = _load_repo_file_module(
                "src_nexus_core_current_base",
                "src/nexus_core.py",
            )
            self.assertEqual(
                nexus_core_module._resolve_default_base_path(),
                str(self.repo_root.resolve()),
            )
            self.assertEqual(
                nexus_core_module._DEFAULT_BASE,
                str(self.repo_root.resolve()),
            )

    def test_semantic_recall_prefers_config_json(self):
        config_json = self.repo_root / "config.json"
        config_yaml = self.repo_root / "config.yaml"
        config_json.write_text(
            json.dumps({"rag": {"top_k": 9, "similarity_threshold": 0.7}}),
            encoding="utf-8",
        )
        config_yaml.write_text(
            "rag:\n  top_k: 3\n  similarity_threshold: 0.1\n",
            encoding="utf-8",
        )

        with mock.patch("os.getcwd", return_value=str(self.repo_root)):
            semantic_recall_module = _load_repo_file_module(
                "src_semantic_recall_json",
                "src/retrieval/semantic_recall.py",
            )
            recall = semantic_recall_module.SemanticRecall(manager=SimpleNamespace())
            self.assertEqual(
                semantic_recall_module.resolve_config_path(),
                config_json.resolve(),
            )
            self.assertEqual(recall.default_top_k, 9)
            self.assertEqual(recall.similarity_threshold, 0.7)

    def test_rag_integrator_prefers_current_repo_config_json(self):
        config_json = self.repo_root / "config.json"
        config_json.write_text(
            json.dumps({"rag": {"top_k": 11, "max_context_tokens": 4096}}),
            encoding="utf-8",
        )

        with mock.patch("os.getcwd", return_value=str(self.repo_root)):
            rag_integrator_module = _load_repo_file_module(
                "src_rag_integrator_json",
                "src/rag/rag_integrator.py",
            )
            integrator = rag_integrator_module.RAGIntegrator(
                semantic_recall=SimpleNamespace(),
            )
            self.assertEqual(
                rag_integrator_module.resolve_config_path(),
                config_json.resolve(),
            )
            self.assertEqual(integrator.default_top_k, 11)
            self.assertEqual(integrator.max_context_tokens, 4096)


class TestFiveMoreCuts(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir) / "repo"
        self.repo_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _vector_store_stubs(self):
        class DummySettings:
            def __init__(self, *args, **kwargs):
                self.kwargs = kwargs

        class DummySentenceTransformer:
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

        @contextlib.contextmanager
        def _dummy_lock(*args, **kwargs):
            yield

        utils_pkg = _make_stub_module("utils")
        vector_db_lock = _make_stub_module(
            "utils.vector_db_lock",
            vector_db_write_lock=_dummy_lock,
        )
        utils_pkg.vector_db_lock = vector_db_lock

        return {
            "chromadb": _make_stub_module("chromadb", PersistentClient=object),
            "chromadb.config": _make_stub_module(
                "chromadb.config",
                Settings=DummySettings,
            ),
            "sentence_transformers": _make_stub_module(
                "sentence_transformers",
                SentenceTransformer=DummySentenceTransformer,
            ),
            "utils": utils_pkg,
            "utils.vector_db_lock": vector_db_lock,
        }

    def _batch_script_stubs(self):
        chunking_pkg = _make_stub_module("chunking")
        chunking_text_splitter = _make_stub_module(
            "chunking.text_splitter",
            create_splitter=lambda *args, **kwargs: SimpleNamespace(),
        )
        chunking_pkg.text_splitter = chunking_text_splitter

        vector_store_pkg = _make_stub_module("vector_store")
        vector_store_init = _make_stub_module(
            "vector_store.init_chroma",
            create_vector_store=lambda *args, **kwargs: SimpleNamespace(
                embedder=SimpleNamespace(),
                collection=SimpleNamespace(),
            ),
        )
        vector_store_manager = _make_stub_module(
            "vector_store.manager",
            create_manager=lambda *args, **kwargs: SimpleNamespace(),
        )
        vector_store_pkg.init_chroma = vector_store_init
        vector_store_pkg.manager = vector_store_manager

        return {
            "chunking": chunking_pkg,
            "chunking.text_splitter": chunking_text_splitter,
            "vector_store": vector_store_pkg,
            "vector_store.init_chroma": vector_store_init,
            "vector_store.manager": vector_store_manager,
        }

    def test_vector_store_init_prefers_config_json(self):
        config_json = self.repo_root / "config.json"
        config_yaml = self.repo_root / "config.yaml"
        config_json.write_text(
            json.dumps({"embedding": {"model_name": "json-model"}}),
            encoding="utf-8",
        )
        config_yaml.write_text(
            "embedding:\n  model_name: yaml-model\n",
            encoding="utf-8",
        )

        with mock.patch.dict(sys.modules, self._vector_store_stubs(), clear=False):
            with mock.patch("os.getcwd", return_value=str(self.repo_root)):
                module = _load_repo_file_module(
                    "vector_store_init_json",
                    "vector_store/init_chroma.py",
                )
                store = module.VectorStoreInit()
                self.assertEqual(module.resolve_config_path(), config_json.resolve())
                self.assertEqual(store.config["embedding"]["model_name"], "json-model")

    def test_vector_store_manager_prefers_config_json(self):
        config_json = self.repo_root / "config.json"
        config_yaml = self.repo_root / "config.yaml"
        config_json.write_text(
            json.dumps({"vector_store": {"collection_name": "json-collection"}}),
            encoding="utf-8",
        )
        config_yaml.write_text(
            "vector_store:\n  collection_name: yaml-collection\n",
            encoding="utf-8",
        )

        with mock.patch("os.getcwd", return_value=str(self.repo_root)):
            module = _load_repo_file_module(
                "vector_store_manager_json",
                "vector_store/manager.py",
            )
            manager = module.VectorStoreManager(
                embedder=SimpleNamespace(),
                collection=SimpleNamespace(),
            )
            self.assertEqual(module.resolve_config_path(), config_json.resolve())
            self.assertEqual(
                manager.config["vector_store"]["collection_name"],
                "json-collection",
            )

    def test_text_splitter_prefers_config_json(self):
        config_json = self.repo_root / "config.json"
        config_yaml = self.repo_root / "config.yaml"
        config_json.write_text(
            json.dumps({"chunking": {"chunk_size": 321, "chunk_overlap": 12}}),
            encoding="utf-8",
        )
        config_yaml.write_text(
            "chunking:\n  chunk_size: 111\n  chunk_overlap: 7\n",
            encoding="utf-8",
        )

        with mock.patch("os.getcwd", return_value=str(self.repo_root)):
            module = _load_repo_file_module(
                "text_splitter_json",
                "chunking/text_splitter.py",
            )
            splitter = module.TextSplitter()
            self.assertEqual(module.resolve_config_path(), config_json.resolve())
            self.assertEqual(splitter.chunk_size, 321)
            self.assertEqual(splitter.chunk_overlap, 12)

    def test_batch_chunk_prefers_config_json(self):
        config_json = self.repo_root / "config.json"
        config_yaml = self.repo_root / "config.yaml"
        config_json.write_text(
            json.dumps({"chunking": {"chunk_size": 222}}),
            encoding="utf-8",
        )
        config_yaml.write_text("chunking:\n  chunk_size: 99\n", encoding="utf-8")

        with mock.patch.dict(sys.modules, self._batch_script_stubs(), clear=False):
            with mock.patch("os.getcwd", return_value=str(self.repo_root)):
                module = _load_repo_file_module(
                    "batch_chunk_json",
                    "scripts/batch_chunk.py",
                )
                processor = module.BatchChunkProcessor()
                self.assertEqual(module.resolve_config_path(), config_json.resolve())
                self.assertEqual(processor.config["chunking"]["chunk_size"], 222)

    def test_batch_chunk_default_input_prefers_workspace_obsidian(self):
        workspace_root = self.repo_root / "workspace"
        obsidian_dir = workspace_root / "Obsidian"
        obsidian_dir.mkdir(parents=True, exist_ok=True)

        with mock.patch.dict(
            os.environ,
            {"OPENCLAW_WORKSPACE": str(workspace_root)},
            clear=False,
        ):
            with mock.patch.dict(sys.modules, self._batch_script_stubs(), clear=False):
                module = _load_repo_file_module(
                    "batch_chunk_default_input",
                    "scripts/batch_chunk.py",
                )
                self.assertEqual(
                    module.resolve_default_input_path(),
                    obsidian_dir.resolve(),
                )

    def test_daily_index_help_mentions_config_json_and_yaml(self):
        with mock.patch.dict(sys.modules, self._batch_script_stubs(), clear=False):
            module = _load_repo_file_module(
                "daily_index_help",
                "scripts/daily_index.py",
            )
            stdout = io.StringIO()
            with mock.patch.object(sys, "argv", ["daily_index.py", "--help"]):
                with contextlib.redirect_stdout(stdout):
                    with self.assertRaises(SystemExit) as exc:
                        module.main()

        self.assertEqual(exc.exception.code, 0)
        self.assertIn("config.json/config.yaml", stdout.getvalue())

    def test_daily_index_default_directory_prefers_workspace_memory(self):
        workspace_root = self.repo_root / "workspace"
        memory_dir = workspace_root / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)

        with mock.patch.dict(
            os.environ,
            {"OPENCLAW_WORKSPACE": str(workspace_root)},
            clear=False,
        ):
            with mock.patch.dict(sys.modules, self._batch_script_stubs(), clear=False):
                module = _load_repo_file_module(
                    "daily_index_default_dir",
                    "scripts/daily_index.py",
                )
                self.assertEqual(
                    module.resolve_default_index_directory(),
                    memory_dir.resolve(),
                )


class TestFiveFurtherCuts(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir) / "repo"
        self.repo_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_conftest_makes_pytest_asyncio_optional(self):
        conftest_module = _load_repo_file_module(
            "tests_conftest_optional_plugin",
            "tests/conftest.py",
        )

        with mock.patch.object(
            conftest_module.importlib.util,
            "find_spec",
            return_value=None,
        ):
            self.assertEqual(conftest_module.optional_pytest_plugins(), [])

        with mock.patch.object(
            conftest_module.importlib.util,
            "find_spec",
            return_value=object(),
        ):
            self.assertEqual(
                conftest_module.optional_pytest_plugins(),
                ["pytest_asyncio"],
            )

    def test_model_router_prefers_current_repo_config_json(self):
        config_json = self.repo_root / "config.json"
        config_json.write_text(
            json.dumps({"routing": {"enabled": True, "light_model": "gpt-test"}}),
            encoding="utf-8",
        )

        with mock.patch("os.getcwd", return_value=str(self.repo_root)):
            module = _load_repo_file_module(
                "scripts_model_router_json",
                "scripts/model_router.py",
            )
            self.assertEqual(module.resolve_config_path(), config_json.resolve())
            self.assertEqual(
                module.load_config(str(config_json))["routing"]["light_model"],
                "gpt-test",
            )

    def test_flush_summaries_workspace_root_prefers_config_base(self):
        workspace_root = self.repo_root / "workspace"
        workspace_root.mkdir(parents=True, exist_ok=True)
        flush_stubs = {
            "auto_summary": _make_stub_module("auto_summary", HybridStorage=object),
            "vector_store": _make_stub_module(
                "vector_store",
                create_vector_store=lambda *args, **kwargs: SimpleNamespace(),
            ),
            "knowledge_common": _make_stub_module(
                "knowledge_common",
                classify_text=None,
                make_trace_id=None,
                normalize_text=None,
                stable_hash=None,
            ),
        }

        with mock.patch.dict(sys.modules, flush_stubs, clear=False):
            module = _load_repo_file_module(
                "scripts_flush_summaries_paths",
                "scripts/flush_summaries.py",
            )

        resolved = module.resolve_workspace_root({"paths": {"base": str(workspace_root)}})
        self.assertEqual(resolved, workspace_root.resolve())

    def test_nexus_auto_save_uses_current_repo_and_workspace_overrides(self):
        workspace_root = self.repo_root / "workspace"
        openclaw_home = self.repo_root / "openclaw-home"
        with mock.patch.dict(
            os.environ,
            {
                "DEEPSEA_NEXUS_ROOT": str(self.repo_root),
                "OPENCLAW_WORKSPACE": str(workspace_root),
                "OPENCLAW_HOME": str(openclaw_home),
                "NEXUS_VECTOR_DB": str(
                    workspace_root / "memory" / ".vector_db_restored"
                ),
            },
            clear=False,
        ):
            module = _load_repo_file_module(
                "scripts_nexus_auto_save_paths",
                "scripts/nexus_auto_save.py",
            )
            self.assertEqual(module.NEXUS_PATH, str(self.repo_root.resolve()))
            self.assertEqual(
                module.VECTOR_DB_PATH,
                str((workspace_root / "memory" / ".vector_db_restored")),
            )
            self.assertEqual(module.LOG_DIR, str(openclaw_home / "logs"))

    def test_smart_context_param_advisor_defaults_to_current_repo_config(self):
        with mock.patch.dict(
            os.environ,
            {},
            clear=True,
        ):
            module = _load_repo_file_module(
                "scripts_smart_context_param_advisor_defaults",
                "scripts/smart_context_param_advisor.py",
            )
            self.assertEqual(
                module.resolve_default_deepsea_config_path(),
                (REPO_ROOT / "config.json").resolve(),
            )

    def test_repo_root_init_supports_top_level_import(self):
        module_path = REPO_ROOT / "__init__.py"
        spec = importlib.util.spec_from_file_location(
            "__init__",
            module_path,
        )
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[spec.name] = module
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ImportWarning)
                spec.loader.exec_module(module)
            self.assertTrue(hasattr(module, "get_version"))
            self.assertEqual(module.__version__, deepsea_nexus.__version__)
        finally:
            sys.modules.pop(spec.name, None)


class TestFiveMoreLegacyPathCuts(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir) / "repo"
        self.repo_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_batch_save_summary_prefers_current_repo_and_workspace_memory(self):
        workspace_root = self.repo_root / "workspace"
        with mock.patch.dict(
            os.environ,
            {
                "DEEPSEA_NEXUS_ROOT": str(self.repo_root),
                "OPENCLAW_WORKSPACE": str(workspace_root),
            },
            clear=False,
        ):
            module = _load_repo_file_module(
                "batch_save_summary_paths",
                "batch_save_summary.py",
            )
            self.assertEqual(module.resolve_nexus_root(), self.repo_root.resolve())
            self.assertEqual(
                module.resolve_memory_dir(),
                (workspace_root / "memory").resolve(),
            )
            self.assertEqual(module.NEXUS_PATH, str(self.repo_root.resolve()))

    def test_context_metrics_export_defaults_follow_workspace_and_home(self):
        workspace_root = self.repo_root / "workspace"
        openclaw_home = self.repo_root / "openclaw-home"
        with mock.patch.dict(
            os.environ,
            {
                "OPENCLAW_WORKSPACE": str(workspace_root),
                "OPENCLAW_HOME": str(openclaw_home),
            },
            clear=False,
        ):
            module = _load_repo_file_module(
                "context_metrics_export_paths",
                "scripts/context_metrics_export.py",
            )
            self.assertEqual(module.resolve_workspace_root(), workspace_root.resolve())
            self.assertEqual(
                module.resolve_canvas_output_path(),
                (openclaw_home / "canvas" / "context-metrics.json").resolve(),
            )

    def test_context_metrics_dashboard_defaults_follow_workspace_override(self):
        workspace_root = self.repo_root / "workspace"
        with mock.patch.dict(
            os.environ,
            {"OPENCLAW_WORKSPACE": str(workspace_root)},
            clear=False,
        ):
            module = _load_repo_file_module(
                "context_metrics_dashboard_paths",
                "scripts/context_metrics_dashboard.py",
            )
            self.assertEqual(module.resolve_workspace_root(), workspace_root.resolve())

    def test_vector_db_snapshot_defaults_follow_workspace_override(self):
        workspace_root = self.repo_root / "workspace"
        with mock.patch.dict(
            os.environ,
            {"OPENCLAW_WORKSPACE": str(workspace_root)},
            clear=True,
        ):
            module = _load_repo_file_module(
                "vector_db_snapshot_paths",
                "scripts/vector_db_snapshot.py",
            )
            self.assertEqual(
                module._resolve_db_path(),
                (workspace_root / "memory" / ".vector_db_restored").resolve(),
            )
            self.assertEqual(
                module._resolve_snapshots_dir(),
                (
                    workspace_root
                    / "memory"
                    / "archives"
                    / "vector_db_snapshots"
                ).resolve(),
            )

    def test_vector_db_healthcheck_defaults_follow_workspace_override(self):
        workspace_root = self.repo_root / "workspace"
        with mock.patch.dict(
            os.environ,
            {"OPENCLAW_WORKSPACE": str(workspace_root)},
            clear=True,
        ):
            module = _load_repo_file_module(
                "vector_db_healthcheck_paths",
                "scripts/vector_db_healthcheck.py",
            )
            self.assertEqual(
                module._resolve_db_path(),
                (workspace_root / "memory" / ".vector_db_restored").resolve(),
            )
            self.assertEqual(
                module._resolve_snapshots_dir(),
                (
                    workspace_root
                    / "memory"
                    / "archives"
                    / "vector_db_snapshots"
                ).resolve(),
            )
            self.assertEqual(
                module._log_path(),
                (workspace_root / "logs" / "vector_db_health.jsonl").resolve(),
            )


class TestFiveMoreLegacyEntryCuts(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir) / "repo"
        self.repo_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_quick_save_uses_openclaw_home_summary_log_dir(self):
        openclaw_home = Path(self.temp_dir) / "openclaw-home"
        env = os.environ.copy()
        env["OPENCLAW_HOME"] = str(openclaw_home)

        result = subprocess.run(
            [
                "bash",
                str(REPO_ROOT / "quick_save.sh"),
                "conversation/1",
                "## 📋 总结\n兼容测试摘要",
            ],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        saved = openclaw_home / "logs" / "summaries" / "conversation_1.txt"
        self.assertTrue(saved.exists())
        self.assertIn("兼容测试摘要", saved.read_text(encoding="utf-8"))

    def test_install_smart_context_param_advisor_cron_uses_current_repo_and_workspace(self):
        fake_bin = Path(self.temp_dir) / "bin"
        fake_bin.mkdir(parents=True, exist_ok=True)
        crontab_state = Path(self.temp_dir) / "crontab.txt"
        fake_crontab = fake_bin / "crontab"
        fake_crontab.write_text(
            "#!/bin/sh\n"
            "state=\"$FAKE_CRONTAB_FILE\"\n"
            "if [ \"$1\" = \"-l\" ]; then\n"
            "  if [ -f \"$state\" ]; then cat \"$state\"; exit 0; fi\n"
            "  exit 1\n"
            "fi\n"
            "cat > \"$state\"\n",
            encoding="utf-8",
        )
        fake_crontab.chmod(0o755)

        workspace_root = Path(self.temp_dir) / "workspace"
        openclaw_home = Path(self.temp_dir) / "openclaw-home"
        env = os.environ.copy()
        env["PATH"] = f"{fake_bin}:{env.get('PATH', '')}"
        env["FAKE_CRONTAB_FILE"] = str(crontab_state)
        env["OPENCLAW_WORKSPACE"] = str(workspace_root)
        env["OPENCLAW_HOME"] = str(openclaw_home)
        env["NEXUS_PYTHON_PATH"] = sys.executable

        result = subprocess.run(
            [
                "bash",
                str(REPO_ROOT / "scripts" / "install_smart_context_param_advisor_cron.sh"),
            ],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        installed = crontab_state.read_text(encoding="utf-8")
        self.assertIn(str(REPO_ROOT.resolve()), installed)
        self.assertIn(
            str(workspace_root / "logs" / "smart_context_param_advisor.cron.log"),
            installed,
        )
        self.assertNotIn("/Users/yizhi/.openclaw/workspace/skills/deepsea-nexus", installed)

    def test_search_sessions_defaults_follow_workspace_override(self):
        workspace_root = self.repo_root / "workspace"
        with mock.patch.dict(
            os.environ,
            {"OPENCLAW_WORKSPACE": str(workspace_root)},
            clear=True,
        ):
            module = _load_repo_file_module(
                "search_sessions_paths",
                "scripts/search_sessions.py",
            )
            self.assertEqual(
                module.resolve_default_db_path(),
                (workspace_root / "memory" / "sessions.db").resolve(),
            )

    def test_openclaw_compaction_audit_defaults_follow_home_and_workspace(self):
        workspace_root = self.repo_root / "workspace"
        openclaw_home = self.repo_root / "openclaw-home"
        with mock.patch.dict(
            os.environ,
            {
                "OPENCLAW_WORKSPACE": str(workspace_root),
                "OPENCLAW_HOME": str(openclaw_home),
            },
            clear=True,
        ):
            module = _load_repo_file_module(
                "openclaw_compaction_audit_paths",
                "scripts/openclaw_compaction_audit.py",
            )
            self.assertEqual(
                module.GATEWAY_LOG,
                (openclaw_home / "logs" / "gateway.log").resolve(),
            )
            self.assertEqual(
                module.STATE_PATH,
                (workspace_root / "logs" / "compaction_audit_state.json").resolve(),
            )
            self.assertEqual(
                module.SMART_LOG,
                (workspace_root / "logs" / "smart_context_metrics.log").resolve(),
            )

    def test_vector_db_rebuild_defaults_follow_workspace_override(self):
        workspace_root = self.repo_root / "workspace"
        with mock.patch.dict(
            os.environ,
            {"OPENCLAW_WORKSPACE": str(workspace_root)},
            clear=True,
        ):
            module = _load_repo_file_module(
                "vector_db_rebuild_paths",
                "scripts/vector_db_rebuild_from_v5.py",
            )
            self.assertEqual(
                module._resolve_default_memory_v5_root(),
                (workspace_root / "memory" / "95_MemoryV5").resolve(),
            )
            self.assertEqual(
                module._resolve_default_db_path(),
                (workspace_root / "memory" / ".vector_db_restored").resolve(),
            )


class TestRepoRuntimeCleanupScript(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir) / "repo"
        self.repo_root.mkdir(parents=True, exist_ok=True)
        self.archive_base = Path(self.temp_dir) / "archive"
        self.cleanup_script = _load_script_module("archive_repo_runtime_data")

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_discover_runtime_artifacts_excludes_venv_by_default(self):
        logs_dir = self.repo_root / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        (logs_dir / "runtime.log").write_text("log", encoding="utf-8")
        cache_dir = self.repo_root / "pkg" / "__pycache__"
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "mod.cpython-311.pyc").write_bytes(b"pyc")
        venv_dir = self.repo_root / ".venv"
        venv_dir.mkdir(parents=True, exist_ok=True)
        (venv_dir / "pyvenv.cfg").write_text("version = 3.8.2\n", encoding="utf-8")

        artifacts = self.cleanup_script.discover_runtime_artifacts(self.repo_root)
        rels = {item.relative_path for item in artifacts}

        self.assertIn("logs", rels)
        self.assertIn("pkg/__pycache__", rels)
        self.assertNotIn(".venv", rels)

    def test_archive_runtime_artifacts_moves_selected_paths(self):
        logs_dir = self.repo_root / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        (logs_dir / "runtime.log").write_text("log", encoding="utf-8")
        cache_dir = self.repo_root / "pkg" / "__pycache__"
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "mod.cpython-311.pyc").write_bytes(b"pyc")
        venv_dir = self.repo_root / ".venv"
        venv_dir.mkdir(parents=True, exist_ok=True)
        (venv_dir / "pyvenv.cfg").write_text("version = 3.8.2\n", encoding="utf-8")

        result = self.cleanup_script.archive_runtime_artifacts(
            repo_root=self.repo_root,
            archive_base=self.archive_base,
            include_stale_venv=True,
            apply=True,
        )

        archive_root = Path(result["archive_root"])
        self.assertFalse(logs_dir.exists())
        self.assertFalse(cache_dir.exists())
        self.assertFalse(venv_dir.exists())
        self.assertTrue((archive_root / "payload" / "logs" / "runtime.log").exists())
        self.assertTrue((archive_root / "payload" / "pkg" / "__pycache__" / "mod.cpython-311.pyc").exists())
        self.assertTrue((archive_root / "payload" / ".venv" / "pyvenv.cfg").exists())
        self.assertTrue((archive_root / "manifest.json").exists())


class TestRuntimePathHelpers(unittest.TestCase):
    def test_resolve_openclaw_workspace_prefers_env(self):
        with mock.patch.dict(os.environ, {"OPENCLAW_WORKSPACE": "/tmp/custom-openclaw-workspace"}, clear=False):
            resolved = runtime_paths.resolve_openclaw_workspace()

        self.assertEqual(resolved, "/tmp/custom-openclaw-workspace")

    def test_resolve_workspace_base_prefers_paths_base(self):
        config = {
            "paths": {"base": "~/workspace-main"},
            "base_path": "~/workspace-fallback",
            "workspace_root": "~/workspace-root",
        }

        resolved = runtime_paths.resolve_workspace_base(config)

        self.assertTrue(resolved.endswith("workspace-main"))

    def test_resolve_log_path_accepts_nexus_base_fallback(self):
        config = {
            "nexus": {"base_path": "/tmp/deepsea-nexus-test-base"},
        }

        resolved = runtime_paths.resolve_log_path(
            config,
            "nexus_core_metrics.log",
            allow_nexus_base=True,
        )

        self.assertEqual(
            resolved,
            "/tmp/deepsea-nexus-test-base/logs/nexus_core_metrics.log",
        )

    def test_resolve_memory_root_keeps_absolute_root(self):
        config = {
            "paths": {"base": "/tmp/workspace"},
            "memory_v5": {"root": "/tmp/custom-memory-root"},
        }

        resolved = runtime_paths.resolve_memory_root(config)

        self.assertEqual(resolved, "/tmp/custom-memory-root")

    def test_resolve_workspace_base_falls_back_to_env_workspace(self):
        with mock.patch.dict(os.environ, {"OPENCLAW_WORKSPACE": "/tmp/openclaw-workspace-env"}, clear=False):
            resolved = runtime_paths.resolve_workspace_base({})

        self.assertEqual(resolved, "/tmp/openclaw-workspace-env")


class TestHostPathDefaults(unittest.TestCase):
    def test_now_manager_uses_openclaw_workspace_default_path(self):
        module = importlib.import_module(f"{deepsea_nexus.__name__}.plugins.now_manager")

        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.dict(
            os.environ,
            {"OPENCLAW_WORKSPACE": temp_dir},
            clear=False,
        ):
            manager = module.NOWManager()

        self.assertEqual(manager.path, os.path.join(temp_dir, "NOW.md"))

    def test_write_guard_defaults_follow_openclaw_workspace(self):
        module = importlib.import_module(f"{deepsea_nexus.__name__}.write_guard")

        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.dict(
            os.environ,
            {
                "OPENCLAW_WORKSPACE": temp_dir,
                "NEXUS_TEST_MODE": "0",
                "PYTEST_CURRENT_TEST": "",
                "UNITTEST_RUNNING": "0",
                "NEXUS_ENFORCE_WRITE_GUARD": "1",
            },
            clear=False,
        ):
            policy = module.get_guard_policy()
            alert_path = module._alert_log_path()

        self.assertEqual(
            policy["expected_vector_db"],
            os.path.join(temp_dir, "memory", ".vector_db_restored"),
        )
        self.assertEqual(
            str(alert_path),
            os.path.join(temp_dir, "logs", "nexus_write_guard_alerts.jsonl"),
        )

    def test_vector_store_defaults_follow_openclaw_workspace(self):
        module = _load_repo_file_module("vector_store_host_defaults", "vector_store.py")
        fake_collection = object()
        fake_client = SimpleNamespace(get_or_create_collection=lambda **kwargs: fake_collection)
        module.CHROMA_AVAILABLE = True
        module.chromadb = SimpleNamespace(PersistentClient=mock.Mock(return_value=fake_client))
        module.Settings = mock.Mock(side_effect=lambda **kwargs: {"settings": kwargs})

        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.dict(
            os.environ,
            {"OPENCLAW_WORKSPACE": temp_dir, "NEXUS_VECTOR_DB": ""},
            clear=False,
        ):
            store = module.VectorStore()

        self.assertEqual(
            store.persist_path,
            os.path.join(temp_dir, "memory", ".vector_db_restored"),
        )

    def test_session_manager_plugin_defaults_to_workspace_memory(self):
        module = importlib.import_module(f"{deepsea_nexus.__name__}.plugins.session_manager")

        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.dict(
            os.environ,
            {"OPENCLAW_WORKSPACE": temp_dir},
            clear=False,
        ):
            plugin = module.SessionManagerPlugin()
            self.assertTrue(asyncio.run(plugin.initialize({})))
            self.assertEqual(plugin._config["base_path"], os.path.join(temp_dir, "memory"))
            self.assertTrue(asyncio.run(plugin.stop()))

    def test_flush_manager_plugin_defaults_to_workspace_memory(self):
        module = importlib.import_module(f"{deepsea_nexus.__name__}.plugins.flush_manager")

        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.dict(
            os.environ,
            {"OPENCLAW_WORKSPACE": temp_dir},
            clear=False,
        ):
            plugin = module.FlushManagerPlugin()
            self.assertTrue(asyncio.run(plugin.initialize({})))
            self.assertEqual(plugin._config["base_path"], os.path.join(temp_dir, "memory"))
            self.assertEqual(plugin._archive_path, os.path.join(temp_dir, "memory", "archive"))


class TestOperationalEntrypathCleanup(unittest.TestCase):
    def test_audit_recent_summaries_path_helpers_follow_workspace_and_repo(self):
        module = _load_script_module("audit_recent_summaries")

        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.dict(
            os.environ,
            {"OPENCLAW_WORKSPACE": temp_dir},
            clear=False,
        ):
            workspace = module.resolve_openclaw_workspace()
            report_dir = module.default_report_dir()
            stores = module.discover_vector_stores(Path(temp_dir) / "memory" / ".vector_db_restored")

        self.assertEqual(workspace, Path(temp_dir).resolve())
        self.assertEqual(report_dir, (REPO_ROOT / "docs" / "reports").resolve())
        self.assertEqual(stores, [])

    def test_warmup_script_defaults_follow_workspace_and_current_collection(self):
        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.dict(
            os.environ,
            {
                "OPENCLAW_WORKSPACE": temp_dir,
                "NEXUS_VECTOR_DB": "",
                "NEXUS_COLLECTION": "deepsea_nexus_restored",
            },
            clear=False,
        ):
            module = _load_script_module("warmup")
            self.assertEqual(module.resolve_workspace_root(), Path(temp_dir).resolve())
            self.assertEqual(
                module.resolve_vector_db_path(),
                (Path(temp_dir).resolve() / "memory" / ".vector_db_restored").resolve(),
            )
            self.assertEqual(module.resolve_collection_name(), "deepsea_nexus_restored")
            self.assertEqual(module.resolve_repo_root(), REPO_ROOT.resolve())

    def test_warmup_daemon_defaults_follow_workspace_repo_and_socket_env(self):
        with tempfile.TemporaryDirectory() as temp_dir, tempfile.TemporaryDirectory() as repo_root, mock.patch.dict(
            os.environ,
            {
                "OPENCLAW_WORKSPACE": temp_dir,
                "DEEPSEA_NEXUS_ROOT": repo_root,
                "NEXUS_VECTOR_DB": "",
                "NEXUS_COLLECTION": "custom_collection",
                "NEXUS_SOCKET_PATH": "/tmp/custom-nexus.sock",
            },
            clear=False,
        ):
            module = _load_script_module("warmup_daemon")
            self.assertEqual(module.resolve_workspace_root(), Path(temp_dir).resolve())
            self.assertEqual(module.resolve_repo_root(), Path(repo_root).resolve())
            self.assertEqual(
                module.resolve_vector_db_path(),
                (Path(temp_dir).resolve() / "memory" / ".vector_db_restored").resolve(),
            )
            self.assertEqual(module.resolve_collection_name(), "custom_collection")
            self.assertEqual(module.SOCKET_PATH, "/tmp/custom-nexus.sock")

    def test_warmup_service_script_uses_current_repo_defaults(self):
        script_path = REPO_ROOT / "scripts" / "warmup_service.sh"
        contents = script_path.read_text(encoding="utf-8")

        self.assertIn('ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"', contents)
        self.assertIn('SCRIPT_PATH="${NEXUS_WARMUP_SCRIPT:-${ROOT_DIR}/scripts/warmup_daemon.py}"', contents)
        self.assertIn('OPENCLAW_WORKSPACE_DIR="${OPENCLAW_WORKSPACE:-${OPENCLAW_HOME_DIR}/workspace}"', contents)
        self.assertIn('LOG_PATH="${NEXUS_WARMUP_LOG:-${OPENCLAW_WORKSPACE_DIR}/logs/nexus_warmup.log}"', contents)
        self.assertNotIn("/Users/yizhi", contents)

    def test_current_shell_entrypoints_have_valid_syntax(self):
        for relative_path in (
            "scripts/deploy_local_v5.sh",
            "scripts/nexus_doctor_local.sh",
            "scripts/warmup_service.sh",
        ):
            result = subprocess.run(
                ["bash", "-n", str(REPO_ROOT / relative_path)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=f"{relative_path}: {result.stderr}")


class TestContextEngineRuntimeState(unittest.TestCase):
    def test_budget_from_config_reads_context_engine_section(self):
        runtime = context_engine_runtime.ContextEngineRuntimeState()
        budget = runtime.budget_from_config(
            {
                "context_engine": {
                    "max_tokens": 512,
                    "max_items": 3,
                    "max_chars_per_item": 120,
                    "max_lines_total": 12,
                    "include_now": False,
                }
            }
        )

        self.assertEqual(budget.max_tokens, 512)
        self.assertEqual(budget.max_items, 3)
        self.assertEqual(budget.max_chars_per_item, 120)
        self.assertEqual(budget.max_lines_total, 12)
        self.assertFalse(budget.include_now)
        self.assertTrue(budget.include_recent_summary)

    def test_trim_to_budget_records_trim_state(self):
        runtime = context_engine_runtime.ContextEngineRuntimeState()
        trimmed = runtime.trim_to_budget("x" * 1200, max_tokens=100)

        self.assertLess(len(trimmed), 1200)
        self.assertEqual(runtime.last_trim_reason, "token_budget")
        self.assertGreater(runtime.last_trim_before_tokens, 100)


class TestSmartContextRuntimeState(unittest.TestCase):
    def test_maybe_alert_inject_ratio_does_not_auto_tune_by_default(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(json.dumps({"smart_context": {}}, ensure_ascii=False), encoding="utf-8")

            runtime = smart_context_runtime.SmartContextRuntimeState(config_path=str(config_path))
            runtime.prime({"paths": {"base": temp_dir}})
            config = SimpleNamespace(
                inject_ratio_alert_enabled=True,
                inject_ratio_alert_threshold=0.2,
                inject_ratio_alert_streak=1,
                inject_persist_interval_sec=60,
                inject_threshold=0.6,
                inject_max_items=2,
                adaptive_min_threshold=0.35,
                inject_debug=False,
            )

            runtime.maybe_alert_inject_ratio(0.1, 12, config)

            self.assertAlmostEqual(config.inject_threshold, 0.6, places=6)
            self.assertEqual(config.inject_max_items, 2)
            persisted = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["smart_context"], {})

    def test_maybe_alert_inject_ratio_auto_tunes_and_persists_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(json.dumps({"smart_context": {}}, ensure_ascii=False), encoding="utf-8")

            runtime = smart_context_runtime.SmartContextRuntimeState(config_path=str(config_path))
            runtime.prime({"paths": {"base": temp_dir}})
            config = SimpleNamespace(
                inject_ratio_alert_enabled=True,
                inject_ratio_alert_threshold=0.2,
                inject_ratio_alert_streak=1,
                inject_ratio_auto_tune=True,
                inject_ratio_auto_tune_step=0.05,
                inject_ratio_auto_tune_max_items=4,
                inject_persist_interval_sec=60,
                inject_threshold=0.6,
                inject_max_items=2,
                adaptive_min_threshold=0.35,
                inject_debug=False,
            )

            runtime.maybe_alert_inject_ratio(0.1, 12, config)

            self.assertAlmostEqual(config.inject_threshold, 0.55, places=6)
            self.assertEqual(config.inject_max_items, 3)

            persisted = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertAlmostEqual(
                persisted["smart_context"]["inject_threshold"],
                0.55,
                places=6,
            )
            self.assertEqual(persisted["smart_context"]["inject_max_items"], 3)

            metrics_path = Path(temp_dir) / "logs" / "smart_context_metrics.log"
            self.assertTrue(metrics_path.exists())
            events = [
                json.loads(line)["event"]
                for line in metrics_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertIn("inject_ratio_alert", events)
            self.assertIn("inject_auto_tune", events)

    def test_auto_tune_inject_respects_floor_and_cap(self):
        runtime = smart_context_runtime.SmartContextRuntimeState()
        config = SimpleNamespace(
            inject_ratio_auto_tune_step=0.05,
            inject_threshold=0.36,
            adaptive_min_threshold=0.35,
            inject_max_items=5,
            inject_ratio_auto_tune_max_items=5,
            inject_debug=False,
        )

        runtime.auto_tune_inject(0.1, config)

        self.assertAlmostEqual(config.inject_threshold, 0.35, places=6)
        self.assertEqual(config.inject_max_items, 5)


class TestSmartContextPluginOrchestration(unittest.TestCase):
    def test_should_compress_uses_8_20_35_policy_boundaries(self):
        plugin = smart_context_module.SmartContextPlugin()

        self.assertEqual(plugin.should_compress(8), (False, "full"))
        self.assertEqual(plugin.should_compress(12), (True, "summary"))
        self.assertEqual(plugin.should_compress(24), (True, "summary_rounds"))
        self.assertEqual(plugin.should_compress(40), (True, "compress_after_rounds"))

    def test_process_round_reuses_turn_summary_for_topic_switch(self):
        plugin = smart_context_module.SmartContextPlugin()
        plugin._nexus_core = object()
        plugin._append_metrics = mock.Mock()
        plugin._store_context = mock.Mock()
        plugin._store_decision_blocks = mock.Mock()
        plugin._store_topic_blocks = mock.Mock()
        plugin._call_nexus = mock.Mock()
        plugin._extract_decision_blocks = mock.Mock(return_value=["决定保留 FastAPI"])
        plugin._extract_decision_supporting_refs = mock.Mock(
            return_value=(["tests/test_relay.py"], ["pytest -q tests/test_relay.py"])
        )
        plugin._extract_topics = mock.Mock(return_value=["Relay Runtime"])
        plugin._detect_topic_switch = mock.Mock(return_value=True)
        plugin._build_turn_summary = mock.Mock(return_value="Summary: keep FastAPI")
        plugin._estimate_tokens = mock.Mock(return_value=12)
        plugin._context_token_usage = mock.Mock(return_value={"full": 0, "summary": 0, "compressed": 0})
        plugin._decide_status_with_tokens = mock.Mock(return_value=("full", "full"))

        result = plugin.process_round("conv-1", 1, "继续", "决定保留 FastAPI")

        self.assertEqual(plugin._build_turn_summary.call_count, 1)
        self.assertTrue(result["stored"])
        self.assertEqual(plugin._call_nexus.call_count, 2)
        first_call = plugin._call_nexus.call_args_list[0]
        second_call = plugin._call_nexus.call_args_list[1]
        self.assertEqual(first_call.args[0], "add_document")
        self.assertEqual(second_call.args[0], "add_document")
        self.assertIn("摘要卡", first_call.kwargs["title"])
        self.assertIn("话题切换", second_call.kwargs["title"])
        plugin._store_context.assert_called_once()
        plugin._store_decision_blocks.assert_called_once_with(
            "conv-1",
            1,
            ["决定保留 FastAPI"],
            evidence_pointers=["tests/test_relay.py"],
            replay_commands=["pytest -q tests/test_relay.py"],
        )
        plugin._store_topic_blocks.assert_called_once_with("conv-1", 1, ["Relay Runtime"])

    def test_store_decision_blocks_requires_supporting_refs(self):
        plugin = smart_context_module.SmartContextPlugin()
        plugin._append_metrics = mock.Mock()
        plugin._call_nexus = mock.Mock()

        plugin._store_decision_blocks("conv-1", 2, ["决定保留 FastAPI"])

        plugin._call_nexus.assert_not_called()
        plugin._append_metrics.assert_called_once_with(
            {
                "event": "decision_block_skip",
                "reason": "missing_evidence",
                "count": 1,
            }
        )

    def test_inject_memory_skips_when_nexus_core_missing(self):
        plugin = smart_context_module.SmartContextPlugin()
        plugin.should_inject = mock.Mock(return_value=(True, "question"))
        plugin._append_metrics = mock.Mock()

        result = plugin.inject_memory("What did we decide?")

        self.assertEqual(result, [])
        plugin._append_metrics.assert_called_once_with(
            {
                "event": "inject_skip",
                "reason": "nexus_core_missing",
            }
        )

    def test_inject_memory_merges_graph_items_and_records_metrics(self):
        plugin = smart_context_module.SmartContextPlugin()
        plugin._nexus_core = object()
        plugin.should_inject = mock.Mock(return_value=(True, "question"))
        plugin._append_metrics = mock.Mock()
        plugin._record_inject_event = mock.Mock()
        plugin._record_inject_stats = mock.Mock()
        plugin._inject_graph_associations = mock.Mock(
            return_value=[
                {
                    "content": "graph node",
                    "source": "graph",
                    "relevance": 0.7,
                    "score": 0.7,
                }
            ]
        )
        plugin._call_nexus = mock.Mock(
            return_value=[
                SimpleNamespace(
                    content="Alpha memory",
                    source="doc-a",
                    relevance=0.9,
                    metadata={"tags": ["type:summary"]},
                ),
                SimpleNamespace(
                    content="Beta memory",
                    source="doc-b",
                    relevance=0.55,
                    metadata={},
                ),
            ]
        )

        result = plugin.inject_memory("What did we decide?")

        self.assertEqual([item["content"] for item in result], ["Alpha memory", "graph node"])
        plugin._call_nexus.assert_called_once_with("search_recall", "What did we decide?", 5)
        plugin._inject_graph_associations.assert_called_once_with("What did we decide?", "question")
        plugin._record_inject_event.assert_called_once_with("question", 2)
        plugin._record_inject_stats.assert_called_once_with("question", 2, 1, 1, 0.65)
        metric_events = [call.args[0]["event"] for call in plugin._append_metrics.call_args_list]
        self.assertIn("inject", metric_events)
        self.assertIn("graph_inject", metric_events)


class TestSmartContextTextHelpers(unittest.TestCase):
    def test_extract_summary_reports_fallback_and_keeps_entities(self):
        result = smart_context_text.extract_summary(
            "## 📋 总结\n好...\n\n更新了 server.py 并调用 run_task()。",
            min_summary_length=50,
            fallback_max_chars=120,
        )

        self.assertEqual(result.status, "fallback")
        self.assertIn("server.py", result.summary)
        self.assertIn("run_task()", result.summary)

    def test_extract_decision_blocks_dedupes_json_and_lines(self):
        text = (
            "```json\n"
            "{\"本次核心产出\": \"决定保留 FastAPI\", \"决策上下文\": \"采用 service layer\"}\n"
            "```\n"
            "- 决定保留 FastAPI\n"
            "- #GOLD: 采用 service layer\n"
        )

        blocks = smart_context_text.extract_decision_blocks(text, max_items=4)

        self.assertEqual(blocks[0], "决定保留 FastAPI")
        self.assertIn("采用 service layer", blocks)
        self.assertEqual(len(blocks), 2)

    def test_extract_topics_uses_heading_and_keyword_backfill(self):
        text = "## Relay Runtime\nrelay runtime provider metrics\nrouter health checks"

        topics = smart_context_text.extract_topics(
            text,
            topic_max=3,
            topic_min_keywords=2,
            keyword_limit=5,
        )

        self.assertIn("Relay Runtime", topics)
        self.assertTrue(any("relay / runtime / provider" == topic for topic in topics))


class TestSmartContextInjectHelpers(unittest.TestCase):
    def test_trim_injected_items_respects_line_and_char_budget(self):
        items = [
            {"content": "line1\nline2\nline3"},
            {"content": "line4\nline5\nline6"},
            {"content": "line7\nline8\nline9"},
            {"content": "line10\nline11\nline12"},
            {"content": "x" * 120},
            {"content": "extra-1"},
            {"content": "extra-2"},
        ]

        trimmed = smart_context_inject.trim_injected_items(
            items,
            max_chars_per_item=80,
            max_lines_per_item=2,
            max_lines_total=10,
        )

        self.assertEqual(len(trimmed), 6)
        self.assertEqual(trimmed[0]["content"], "line1\nline2")
        self.assertTrue(trimmed[4]["content"].endswith("..."))
        self.assertEqual(trimmed[-1]["content"], "extra-1")

    def test_finalize_injected_items_sorts_topk_then_trims(self):
        final = smart_context_inject.finalize_injected_items(
            [{"content": "alpha", "score": 0.4}, {"content": "beta", "score": 0.9}],
            [{"content": "gamma\ndelta\nepsilon", "score": 0.7}],
            topk_only=True,
            max_items=2,
            max_chars_per_item=40,
            max_lines_per_item=2,
            max_lines_total=10,
        )

        self.assertEqual([item["content"] for item in final], ["beta", "gamma\ndelta"])

    def test_dynamic_inject_params_penalizes_low_signal_items(self):
        max_items, threshold = smart_context_inject.dynamic_inject_params(
            "question",
            [{"tags": [], "source": ""}],
            max_items=3,
            threshold=0.6,
            inject_dynamic_enabled=True,
            dynamic_max_items=5,
            dynamic_low_signal_penalty=1,
            dynamic_high_signal_bonus=1,
        )

        self.assertEqual(max_items, 2)
        self.assertAlmostEqual(threshold, 0.65, places=6)

    def test_dynamic_inject_params_rewards_high_signal_items(self):
        max_items, threshold = smart_context_inject.dynamic_inject_params(
            "question",
            [
                {"tags": ["type:decision_block"], "source": ""},
                {"tags": [], "source": "主题块 test"},
            ],
            max_items=3,
            threshold=0.6,
            inject_dynamic_enabled=True,
            dynamic_max_items=5,
            dynamic_low_signal_penalty=1,
            dynamic_high_signal_bonus=1,
        )

        self.assertEqual(max_items, 4)
        self.assertAlmostEqual(threshold, 0.55, places=6)


class TestSmartContextConvenienceFunctions(unittest.TestCase):
    def test_store_conversation_uses_real_newlines_for_decision_blocks(self):
        writes = []

        def fake_write(content, title, **kwargs):
            writes.append({"content": content, "title": title, "kwargs": kwargs})

        with mock.patch.object(compat_module, "nexus_init", return_value=True), mock.patch.object(
            compat_module,
            "nexus_write",
            side_effect=fake_write,
        ):
            result = smart_context_module.store_conversation(
                "conv-1",
                "继续",
                "决定保留 FastAPI",
            )

        self.assertTrue(result["stored"])
        decision_contents = [
            entry["content"]
            for entry in writes
            if entry["title"].startswith("决策块")
        ]
        self.assertEqual(decision_contents, ["决定保留 FastAPI"])
        self.assertTrue(all("\\n" not in content for content in decision_contents))


class TestSmartContextConversationHelpers(unittest.TestCase):
    def test_build_conversation_store_data_collects_summary_keywords_and_topics(self):
        data = smart_context_conversation.build_conversation_store_data(
            "继续推进 relay audit",
            "## 总结\n决定保留 FastAPI，并完善 relay audit provider metrics。",
            summary_min_length=20,
            summary_fallback_max_chars=120,
            keyword_limit=5,
            decision_max=3,
            topic_max=3,
            topic_min_keywords=2,
        )

        self.assertIn("FastAPI", data.summary)
        self.assertIn("relay", " ".join(data.keywords).lower())
        self.assertTrue(any("决定保留 FastAPI" in item for item in data.decisions))
        self.assertTrue(any("relay" in topic.lower() for topic in data.topics))


class TestSmartContextSummaryHelpers(unittest.TestCase):
    def test_build_turn_summary_returns_plain_summary_when_template_disabled(self):
        result = smart_context_summary.build_turn_summary(
            "继续",
            "保留 FastAPI 并更新 server.py",
            ["决定保留 FastAPI"],
            summary_template_enabled=False,
            summary_template_fields=("summary", "decisions"),
            summary_min_length=20,
            topic_max=3,
            topic_min_keywords=2,
        )

        self.assertEqual(result.text, result.summary_result.summary)
        self.assertIn("FastAPI", result.text)

    def test_build_turn_summary_formats_requested_sections(self):
        result = smart_context_summary.build_turn_summary(
            "Goal: 稳定 relay audit\nStatus: blocked\nConstraint: 不能破坏兼容\n还缺什么？",
            "## Relay Runtime\n保留 FastAPI 并更新 server.py\nBlocker: provider metrics missing\nEvidence: tests/test_relay.py\nReplay: pytest -q tests/test_relay.py\nNext: add tests",
            ["决定保留 FastAPI"],
            summary_template_enabled=True,
            summary_template_fields=(
                "summary",
                "goal",
                "status",
                "decisions",
                "constraints",
                "blockers",
                "topics",
                "next_actions",
                "questions",
                "evidence",
                "replay",
            ),
            summary_min_length=20,
            topic_max=3,
            topic_min_keywords=2,
        )

        self.assertIn("Summary:", result.text)
        self.assertIn("Goal: 稳定 relay audit", result.text)
        self.assertIn("Status: blocked", result.text)
        self.assertIn("Decisions: 决定保留 FastAPI", result.text)
        self.assertIn("Constraints: 不能破坏兼容", result.text)
        self.assertIn("Blockers: provider metrics missing", result.text)
        self.assertIn("Topics: Relay Runtime", result.text)
        self.assertIn("Next: add tests", result.text)
        self.assertIn("Questions: 还缺什么？", result.text)
        self.assertIn("Evidence: tests/test_relay.py", result.text)
        self.assertIn("Replay: pytest -q tests/test_relay.py", result.text)

    def test_build_turn_summary_drops_decisions_without_evidence(self):
        result = smart_context_summary.build_turn_summary(
            "Goal: 稳定 relay audit\nStatus: blocked",
            "决定保留 FastAPI\nNext: add tests",
            ["决定保留 FastAPI"],
            summary_template_enabled=True,
            summary_template_fields=("summary", "decisions", "next_actions"),
            summary_min_length=20,
            topic_max=3,
            topic_min_keywords=2,
        )

        self.assertIn("Summary:", result.text)
        self.assertIn("Next: add tests", result.text)
        self.assertNotIn("Decisions:", result.text)


class TestSmartContextPromptHelpers(unittest.TestCase):
    def test_build_context_prompt_formats_dict_entries(self):
        prompt = smart_context_prompt.build_context_prompt(
            [
                {
                    "source": "doc-a",
                    "relevance": 0.678,
                    "content": "Alpha Beta Gamma",
                }
            ],
            max_chars_per_item=10,
        )

        lines = prompt.splitlines()
        self.assertEqual(lines[0], "## 相关记忆")
        self.assertEqual(lines[2], "【1】(doc-a - 0.68)")
        self.assertEqual(lines[3], "Alpha Beta")

    def test_build_context_prompt_supports_object_entries(self):
        prompt = smart_context_prompt.build_context_prompt(
            [
                SimpleNamespace(
                    source="doc-b",
                    relevance=0.4,
                    content="Structured note",
                )
            ]
        )

        self.assertIn("【1】(doc-b - 0.40)", prompt)
        self.assertIn("Structured note", prompt)


class TestSmartContextDecisionHelpers(unittest.TestCase):
    def test_should_inject_returns_context_starved_first(self):
        should_inject, reason = smart_context_decision.should_inject(
            "继续",
            inject_enabled=True,
            association_enabled=True,
            context_starved_min_chars=16,
            inject_mode="balanced",
        )

        self.assertTrue(should_inject)
        self.assertEqual(reason, "context_starved")

    def test_should_inject_balanced_mode_detects_technical_term(self):
        should_inject, reason = smart_context_decision.should_inject(
            "observability pipeline tuning",
            inject_enabled=True,
            association_enabled=False,
            context_starved_min_chars=16,
            inject_mode="balanced",
        )

        self.assertTrue(should_inject)
        self.assertEqual(reason, "technical_term")

    def test_detect_topic_switch_returns_new_keywords(self):
        switched, keywords = smart_context_decision.detect_topic_switch(
            "ledger settlement audit",
            topic_switch_enabled=True,
            last_keywords=["relay", "provider"],
            topic_switch_keywords_max=8,
            topic_switch_min_overlap_ratio=0.2,
        )

        self.assertTrue(switched)
        self.assertEqual(keywords[:3], ["ledger", "settlement", "audit"])


class TestSmartContextGraphHelpers(unittest.TestCase):
    def test_extract_graph_edges_uses_workspace_subject_without_conversation(self):
        edges = smart_context_graph.extract_graph_edges(
            "采用 FastAPI 并依赖 Redis",
            "",
            4,
        )

        self.assertEqual(edges[0]["subj"], "workspace")
        self.assertEqual(edges[0]["rel"], "uses")
        self.assertEqual(edges[0]["obj"], "FastAPI")
        self.assertEqual(edges[1]["rel"], "depends_on")
        self.assertEqual(edges[1]["obj"], "Redis")

    def test_build_decision_block_operations_includes_document_and_graph_edges(self):
        operations = smart_context_graph.build_decision_block_operations(
            "conv-1",
            3,
            ["采用 FastAPI"],
            evidence_pointers=["tests/test_relay.py"],
            replay_commands=["pytest -q tests/test_relay.py"],
            max_graph_edges=3,
        )

        self.assertEqual(operations[0]["document"]["title"], "决策块 conv-1 - 轮3 (1)")
        self.assertEqual(
            operations[0]["document"]["tags"],
            "type:decision_block,round:3,conversation:conv-1",
        )
        self.assertIn("Decision: 采用 FastAPI", operations[0]["document"]["content"])
        self.assertIn("Evidence: tests/test_relay.py", operations[0]["document"]["content"])
        self.assertIn("Replay: pytest -q tests/test_relay.py", operations[0]["document"]["content"])
        self.assertEqual(operations[0]["graph_edges"][0]["source"], "decision_block:conv-1")
        self.assertEqual(operations[0]["graph_edges"][0]["conversation_id"], "conv-1")

    def test_build_topic_block_operations_caps_graph_obj_to_80_chars(self):
        topic = "t" * 100
        operations = smart_context_graph.build_topic_block_operations(
            "conv-1",
            2,
            [topic],
        )

        self.assertEqual(operations[0]["document"]["title"], "主题块 conv-1 - 轮2 (1)")
        self.assertEqual(len(operations[0]["graph_edges"][0]["obj"]), 80)


class TestSmartContextRescueHelpers(unittest.TestCase):
    def test_collect_rescue_updates_extracts_typed_preservation_fields(self):
        updates = smart_context_rescue.collect_rescue_updates(
            (
                "Goal: 稳定 relay audit\n"
                "Status: blocked\n"
                "Constraint: 不能破坏兼容\n"
                "#GOLD: 保留 FastAPI\n"
                "Blocker: provider 指标缺失\n"
                "Evidence: tests/test_relay.py\n"
                "Replay: pytest -q tests/test_relay.py\n"
                "Next: 先补测试\n"
                "这个问题？后续补测试计划"
            ),
            rescue_gold=True,
            rescue_decisions=True,
            rescue_next_actions=True,
        )

        self.assertEqual(updates["current_goal"], "稳定 relay audit")
        self.assertEqual(updates["current_status"], "blocked")
        self.assertTrue(any("保留 FastAPI" in item for item in updates["decisions"]))
        self.assertEqual(updates["constraints"], ["不能破坏兼容"])
        self.assertEqual(updates["blockers"], ["provider 指标缺失"])
        self.assertEqual(updates["next_actions"], ["先补测试"])
        self.assertEqual(updates["open_questions"], ["后续补测试计划"])
        self.assertEqual(updates["evidence_pointers"], ["tests/test_relay.py"])
        self.assertEqual(updates["replay_commands"], ["pytest -q tests/test_relay.py"])

    def test_apply_rescue_updates_only_counts_new_items(self):
        state = {
            "current_goal": "稳定 relay audit",
            "decisions": ["保留 FastAPI"],
            "constraints": ["不能破坏兼容"],
            "next_actions": [],
            "open_questions": ["后续补测试"],
        }
        result = smart_context_rescue.apply_rescue_updates(
            state,
            {
                "current_goal": "稳定 relay audit v2",
                "current_status": "blocked",
                "decisions": ["保留 FastAPI", "增加回归测试"],
                "constraints": ["不能破坏兼容", "保留 8/20/35"],
                "blockers": ["provider 指标缺失"],
                "next_actions": ["推进重构"],
                "open_questions": ["后续补测试", "确认边界"],
                "evidence_pointers": ["tests/test_relay.py"],
                "replay_commands": ["pytest -q tests/test_relay.py"],
            },
        )

        self.assertEqual(
            result,
            {
                "goal_rescued": 1,
                "status_rescued": 1,
                "decisions_rescued": 1,
                "constraints_rescued": 1,
                "blockers_rescued": 1,
                "next_actions_rescued": 1,
                "goals_rescued": 1,
                "open_questions_rescued": 1,
                "questions_rescued": 1,
                "evidence_rescued": 1,
                "replay_rescued": 1,
            },
        )
        self.assertEqual(state["current_goal"], "稳定 relay audit v2")
        self.assertEqual(state["current_status"], "blocked")
        self.assertIn("增加回归测试", state["decisions"])
        self.assertIn("保留 8/20/35", state["constraints"])
        self.assertIn("provider 指标缺失", state["blockers"])
        self.assertIn("推进重构", state["next_actions"])
        self.assertIn("确认边界", state["open_questions"])
        self.assertIn("tests/test_relay.py", state["evidence_pointers"])
        self.assertIn("pytest -q tests/test_relay.py", state["replay_commands"])


class TestSmartContextNOWHelpers(unittest.TestCase):
    def test_rescue_before_compress_updates_now_state_and_saves(self):
        class FakeNOW:
            def __init__(self):
                self.state = {
                    "decisions": [],
                    "next_actions": [],
                    "open_questions": [],
                }
                self.saved = False

            def save(self):
                self.saved = True

        fake = FakeNOW()
        result = smart_context_now.rescue_before_compress(
            "#GOLD: 保留 FastAPI\n这个问题？后续补测试计划",
            rescue_gold=True,
            rescue_decisions=False,
            rescue_next_actions=True,
            manager_factory=lambda: fake,
        )

        self.assertTrue(result["saved"])
        self.assertEqual(result["decisions_rescued"], 1)
        self.assertEqual(result["questions_rescued"], 1)
        self.assertTrue(fake.saved)
        self.assertEqual(fake.state["decisions"], ["保留 FastAPI"])
        self.assertEqual(fake.state["open_questions"], ["后续补测试计划"])

    def test_get_and_clear_rescue_delegate_to_manager(self):
        class FakeNOW:
            def __init__(self):
                self.cleared = False

            def format_context(self):
                return "rescued-context"

            def clear(self):
                self.cleared = True

        fake = FakeNOW()
        self.assertEqual(
            smart_context_now.get_rescue_context(manager_factory=lambda: fake),
            "rescued-context",
        )
        smart_context_now.clear_rescue(manager_factory=lambda: fake)
        self.assertTrue(fake.cleared)


class TestSmartContextRecallHelpers(unittest.TestCase):
    def test_build_inject_candidates_dedupes_by_signature(self):
        results = [
            SimpleNamespace(
                content="Alpha 12345",
                source="doc-a",
                relevance=0.6,
                metadata={"tags": ["type:summary"]},
            ),
            SimpleNamespace(
                content="alpha 67890",
                source="doc-b",
                relevance=0.9,
                metadata={"tags": ["type:decision_block"]},
            ),
        ]

        items = smart_context_recall.build_inject_candidates(
            results,
            signature_fn=lambda text: text[:5].lower(),
            normalize_tags_fn=smart_context_inject.normalize_tags,
            score_fn=lambda relevance, tags, source: relevance + (0.1 if "type:summary" in tags else 0.0),
        )

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["source"], "doc-a")
        self.assertEqual(items[0]["tags"], ["type:summary"])
        self.assertAlmostEqual(items[0]["score"], 0.7, places=6)

    def test_build_inject_metric_payload_reports_ratio_and_top_score(self):
        payload = smart_context_recall.build_inject_metric_payload(
            reason="question",
            retrieved=4,
            filtered=[{"score": 0.88}, {"score": 0.55}],
            threshold=0.6,
            max_items=3,
            fallback_used=False,
            fallback_reason="",
        )

        self.assertEqual(payload["event"], "inject")
        self.assertEqual(payload["reason"], "question")
        self.assertEqual(payload["retrieved"], 4)
        self.assertEqual(payload["injected"], 2)
        self.assertAlmostEqual(payload["ratio"], 0.5, places=6)
        self.assertAlmostEqual(payload["top_score"], 0.88, places=6)

    def test_select_injected_items_falls_back_to_top1_when_threshold_filters_all(self):
        selected, fallback_used, fallback_reason = smart_context_recall.select_injected_items(
            [
                {"score": 0.3, "content": "a"},
                {"score": 0.5, "content": "b"},
            ],
            threshold=0.8,
        )

        self.assertTrue(fallback_used)
        self.assertEqual(fallback_reason, "fallback_top1")
        self.assertEqual(selected[0]["content"], "b")


class TestSmartContextGraphInjectHelpers(unittest.TestCase):
    def test_should_graph_inject_only_allows_supported_reasons(self):
        self.assertTrue(
            smart_context_graph_inject.should_graph_inject(
                graph_enabled=True,
                graph_inject_enabled=True,
                reason="question",
            )
        )
        self.assertFalse(
            smart_context_graph_inject.should_graph_inject(
                graph_enabled=True,
                graph_inject_enabled=True,
                reason="none",
            )
        )

    def test_build_graph_injected_items_formats_evidence_and_caps_output(self):
        def fake_lookup(keyword, limit, evidence_limit):
            del limit, evidence_limit
            return [
                {
                    "subj": keyword,
                    "rel": "uses",
                    "obj": "FastAPI",
                    "weight": 0.8,
                    "evidence": [{"text": "very long evidence text"}],
                }
            ]

        items = smart_context_graph_inject.build_graph_injected_items(
            ["relay", "audit"],
            edge_lookup_fn=fake_lookup,
            max_items=1,
            evidence_max_chars=4,
        )

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["source"], "graph")
        self.assertEqual(items[0]["relevance"], 0.8)
        self.assertEqual(items[0]["content"], "relay uses FastAPI | 证据: very")


class TestSmartContextStorageHelpers(unittest.TestCase):
    def test_build_round_context_document_uses_status_specific_payload(self):
        summary_doc = smart_context_storage.build_round_context_document(
            "conv-1",
            2,
            {"status": "summary", "summary": "保留 FastAPI"},
        )
        compressed_doc = smart_context_storage.build_round_context_document(
            "conv-1",
            3,
            {"status": "compressed", "summary": "压缩摘要"},
        )

        self.assertEqual(summary_doc["content"], "[摘要] 保留 FastAPI")
        self.assertEqual(summary_doc["title"], "对话 conv-1 - 轮2 (摘要)")
        self.assertEqual(compressed_doc["content"], "[已压缩] 压缩摘要")
        self.assertEqual(compressed_doc["tags"], "type:compressed,round:3,conversation:conv-1")

    def test_build_conversation_store_entries_preserves_order_and_compat_meta(self):
        entries = smart_context_storage.build_conversation_store_entries(
            "conv-2",
            ai_response="原文",
            summary="摘要",
            keywords=["alpha", "beta"],
            decisions=["决定 A"],
            topics=["主题 B"],
        )

        self.assertEqual([entry["title"] for entry in entries], [
            "对话 conv-2 - 原文",
            "对话 conv-2 - 摘要",
            "对话 conv-2 - 关键词",
            "决策块 conv-2 - (1)",
            "主题块 conv-2 - (1)",
        ])
        self.assertEqual(entries[2]["content"], "alpha beta")
        self.assertEqual(entries[3]["compat"]["kind"], "decision")
        self.assertEqual(entries[4]["compat"]["tags"], "type:topic_block")


class TestSmartContextRoundHelpers(unittest.TestCase):
    def test_build_round_result_for_compressed_round_keeps_summary_and_rescue(self):
        result = smart_context_round.build_round_result(
            "conv-1",
            5,
            "compressed",
            combined_text="u\na",
            summary="摘要",
            rescue_result={"saved": True},
        )

        self.assertEqual(result["status"], "compressed")
        self.assertEqual(result["summary"], "摘要")
        self.assertTrue(result["compressed"])
        self.assertEqual(result["rescue"], {"saved": True})

    def test_build_rescue_metric_events_includes_saved_event(self):
        events = smart_context_round.build_rescue_metric_events(
            {
                "saved": True,
                "decisions_rescued": 1,
                "goals_rescued": 2,
                "questions_rescued": 3,
            }
        )

        self.assertEqual([event["event"] for event in events], ["rescue_result", "rescue_saved"])
        self.assertEqual(events[1]["questions"], 3)

    def test_build_round_summary_document_supports_topic_boundary(self):
        doc = smart_context_round.build_round_summary_document(
            "conv-2",
            7,
            "内容",
            topic_boundary=True,
        )

        self.assertEqual(doc["title"], "对话 conv-2 - 话题切换 (轮7)")
        self.assertEqual(doc["tags"], "type:topic_boundary,round:7,conversation:conv-2")

    def test_build_round_process_artifacts_for_compressed_round_includes_rescue_events(self):
        calls = {"summary": 0, "rescue": 0}

        def fake_summary(text):
            calls["summary"] += 1
            self.assertEqual(text, "ai")
            return "摘要"

        def fake_rescue(text):
            calls["rescue"] += 1
            self.assertEqual(text, "user\nai")
            return {"saved": True, "decisions_rescued": 1, "goals_rescued": 0, "questions_rescued": 2}

        artifacts = smart_context_round.build_round_process_artifacts(
            "conv-1",
            4,
            "compressed",
            combined_text="user\nai",
            ai_response="ai",
            extract_summary_fn=fake_summary,
            rescue_before_compress_fn=fake_rescue,
        )

        self.assertEqual(calls, {"summary": 1, "rescue": 1})
        self.assertEqual(artifacts.result["summary"], "摘要")
        self.assertEqual([event["event"] for event in artifacts.metric_events], ["rescue_result", "rescue_saved"])
        self.assertIn("decisions=1", artifacts.rescue_debug_line)

    def test_build_context_history_entry_uses_result_fields(self):
        payload = smart_context_round.build_context_history_entry(
            9,
            {"status": "summary", "summary": "s", "compressed": False},
            created_at="2026-03-13T20:00:00",
        )

        self.assertEqual(
            payload,
            {
                "round_num": 9,
                "status": "summary",
                "content": "",
                "created_at": "2026-03-13T20:00:00",
                "summary": "s",
                "compressed": False,
            },
        )


class TestSmartContextAdaptiveHelpers(unittest.TestCase):
    def test_summarize_inject_stats_aggregates_recent_window(self):
        summary = smart_context_adaptive.summarize_inject_stats(
            [
                {"retrieved": 2, "injected": 1, "graph": 0},
                {"retrieved": 4, "injected": 2, "graph": 1},
            ],
            2,
        )

        self.assertEqual(
            summary,
            {
                "window": 2,
                "retrieved": 6,
                "injected": 3,
                "graph_injected": 1,
                "avg_ratio": 0.5,
            },
        )

    def test_compute_adaptive_threshold_increases_when_recent_success_is_low(self):
        adaptive = smart_context_adaptive.compute_adaptive_threshold(
            [{"count": 0}, {"count": 0}, {"count": 1}],
            adaptive_window=3,
            current_threshold=0.6,
            adaptive_min_threshold=0.35,
            adaptive_max_threshold=0.75,
            adaptive_step=0.05,
        )

        self.assertAlmostEqual(adaptive["ratio"], 1 / 3, places=6)
        self.assertAlmostEqual(adaptive["new_threshold"], 0.65, places=6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
