import tempfile
import unittest
import importlib
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]


def _load_local_package():
    spec = importlib.util.spec_from_file_location(
        "deepsea_nexus_local_brain_units",
        ROOT / "__init__.py",
        submodule_search_locations=[str(ROOT)],
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


deepsea_nexus = _load_local_package()
brain_models_module = importlib.import_module(f"{deepsea_nexus.__name__}.brain.models")
brain_store_module = importlib.import_module(f"{deepsea_nexus.__name__}.brain.store")
BrainRecord = brain_models_module.BrainRecord
JSONLBrainStore = brain_store_module.JSONLBrainStore


class TestBrainUnits(unittest.TestCase):
    def test_record_hash_and_dedupe_key(self):
        r1 = BrainRecord(
            id="1",
            kind="fact",
            priority="P1",
            source="unit",
            tags=["Python", "Memory"],
            content="Use jsonl for append-only storage",
        )
        r2 = BrainRecord(
            id="2",
            kind="fact",
            priority="P1",
            source="unit",
            tags=["memory", "python"],
            content="Use jsonl for append-only storage",
        )
        self.assertEqual(r1.hash, r2.hash)

    def test_jsonl_append_and_read(self):
        with tempfile.TemporaryDirectory() as td:
            store = JSONLBrainStore(base_path=td)
            store.write(BrainRecord(id="1", kind="fact", priority="P0", source="t", content="alpha"))
            store.write(BrainRecord(id="2", kind="strategy", priority="P2", source="t", content="beta"))

            records = store.read_all()
            self.assertEqual(len(records), 2)
            self.assertEqual(records[0].content, "alpha")

    def test_checkpoint_compaction(self):
        with tempfile.TemporaryDirectory() as td:
            store = JSONLBrainStore(base_path=td)
            store.write(BrainRecord(id="1", kind="fact", priority="P1", source="t", content="dup"))
            store.write(BrainRecord(id="2", kind="fact", priority="P1", source="t", content="dup"))
            store.write(BrainRecord(id="3", kind="strategy", priority="P1", source="t", content="uniq"))

            stats = store.checkpoint()
            self.assertTrue(stats.get("version"))
            self.assertEqual(stats["snapshot_count"], 2)
            self.assertEqual(stats["compacted_from"], 3)

    def test_list_versions_from_snapshots_and_changelog(self):
        with tempfile.TemporaryDirectory() as td:
            store = JSONLBrainStore(base_path=td)
            snapshots = store.snapshots_dir
            (snapshots / "20260214T100000Z.jsonl").write_text("{}\n", encoding="utf-8")
            (snapshots / "20260214T120000Z.jsonl").write_text("{}\n", encoding="utf-8")
            with store.changelog_path.open("w", encoding="utf-8") as f:
                f.write('{"event":"checkpoint","version":"20260214T110000Z"}\n')
                f.write('{"event":"rollback","version":"20260214T120000Z"}\n')

            versions = store.list_versions()
            self.assertEqual(
                versions,
                ["20260214T120000Z", "20260214T110000Z", "20260214T100000Z"],
            )

    def test_checkpoint_retention_deletes_old_snapshots(self):
        with tempfile.TemporaryDirectory() as td:
            store = JSONLBrainStore(base_path=td, max_snapshots=2)

            for idx in range(3):
                store.write(BrainRecord(id=str(idx), kind="fact", priority="P1", source="t", content=f"c{idx}"))
                store.checkpoint()
                # Ensure version filenames differ on fast machines
                import time
                time.sleep(1.0)

            snapshot_files = sorted(p.name for p in store.snapshots_dir.glob("*.jsonl"))
            self.assertEqual(len(snapshot_files), 2)

            events = list(store._iter_jsonl(store.changelog_path))
            cleanup_events = [e for e in events if e.get("event") == "retention_cleanup"]
            self.assertTrue(cleanup_events)
            self.assertTrue(cleanup_events[-1].get("deleted_versions"))

    def test_rollback_clears_append_log_by_archiving_records(self):
        with tempfile.TemporaryDirectory() as td:
            store = JSONLBrainStore(base_path=td)
            store.write(BrainRecord(id="1", kind="fact", priority="P1", source="t", content="base"))
            stats = store.checkpoint()
            version = stats["version"]

            store.write(BrainRecord(id="2", kind="fact", priority="P1", source="t", content="new append"))
            self.assertGreater(store.records_path.stat().st_size, 0)

            ok = store.rollback(version)
            self.assertTrue(ok)
            self.assertTrue(store.records_path.exists())
            self.assertEqual(store.records_path.stat().st_size, 0)

            archived = list(store.snapshots_dir.glob("records_before_rollback_*.jsonl"))
            self.assertTrue(archived)

    def test_dedupe_on_write_skips_recent_duplicates(self):
        with tempfile.TemporaryDirectory() as td:
            store = JSONLBrainStore(base_path=td, dedupe_on_write=True, dedupe_recent_max=10)
            r1 = BrainRecord(id="1", kind="fact", priority="P1", source="t", content="dup")
            r2 = BrainRecord(id="2", kind="fact", priority="P1", source="t", content="dup")
            store.write(r1)
            store.write(r2)

            lines = list(store._iter_jsonl(store.records_path))
            self.assertEqual(len(lines), 1)

    def test_usage_promotion_on_checkpoint(self):
        with tempfile.TemporaryDirectory() as td:
            store = JSONLBrainStore(base_path=td)
            rec = BrainRecord(id="u1", kind="fact", priority="P2", source="t", content="frequent")
            store.write(rec)
            # simulate usage hits
            store.log_usage(["u1", "u1", "u1", "u1"])

            stats = store.checkpoint()
            self.assertTrue(stats.get("version"))

            records = store.read_all()
            self.assertEqual(len(records), 1)
            out = records[0]
            self.assertEqual(out.priority, "P1")
            self.assertGreaterEqual(int(out.metadata.get("usage_count", 0)), 4)

    def test_decay_on_checkpoint(self):
        with tempfile.TemporaryDirectory() as td:
            store = JSONLBrainStore(
                base_path=td,
                decay_on_checkpoint_days=1,
                decay_floor=0.1,
                decay_step=0.05,
            )
            rec = BrainRecord(id="d1", kind="fact", priority="P1", source="t", content="old")
            rec.updated_at = "2020-01-01T00:00:00+00:00"
            store.write(rec)

            store.checkpoint()
            out = store.read_all()[0]
            self.assertLessEqual(out.decay, 0.95)


if __name__ == "__main__":
    unittest.main()
