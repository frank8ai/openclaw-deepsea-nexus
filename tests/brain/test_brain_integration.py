import tempfile
import unittest
import importlib
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]


def _load_local_package():
    spec = importlib.util.spec_from_file_location(
        "deepsea_nexus_local_brain_integration",
        ROOT / "__init__.py",
        submodule_search_locations=[str(ROOT)],
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


deepsea_nexus = _load_local_package()
brain_api_module = importlib.import_module(f"{deepsea_nexus.__name__}.brain.api")
brain_vector_module = importlib.import_module(f"{deepsea_nexus.__name__}.brain.vector_scorer")
configure_brain = brain_api_module.configure_brain
brain_write = brain_api_module.brain_write
brain_retrieve = brain_api_module.brain_retrieve
checkpoint = brain_api_module.checkpoint
rollback = brain_api_module.rollback
backfill_embeddings = brain_api_module.backfill_embeddings
VectorScorer = brain_vector_module.VectorScorer


class TestBrainIntegration(unittest.TestCase):
    def test_write_attaches_embedding_when_vector_enabled(self):
        class _FakeEmb:
            def __init__(self, vec):
                self._vec = vec

            def tolist(self):
                return list(self._vec)

        class _FakeModel:
            def encode(self, texts, normalize_embeddings=True):
                return [_FakeEmb([0.1, 0.2, 0.3])]

        with tempfile.TemporaryDirectory() as td:
            scorer = VectorScorer(dim=3, use_sentence_transformers=False)
            scorer._st_model = _FakeModel()
            scorer.use_sentence_transformers = True

            configure_brain(enabled=True, base_path=td, scorer=scorer)
            rec = brain_write(
                {
                    "id": "emb1",
                    "kind": "fact",
                    "priority": "P1",
                    "source": "itest",
                    "tags": ["embed"],
                    "content": "Embedding should be stored",
                }
            )
            self.assertIsNotNone(rec)
            meta = rec.metadata
            self.assertIsInstance(meta.get("embedding"), list)
            self.assertEqual(meta.get("embedding_dim"), 3)
            self.assertEqual(meta.get("embedding_kind"), "sentence-transformers")
            self.assertEqual(meta.get("embedding_hash"), rec.hash)

    def test_write_skips_embedding_when_hashed_vector(self):
        with tempfile.TemporaryDirectory() as td:
            configure_brain(enabled=True, base_path=td, scorer_type="hashed-vector")
            rec = brain_write(
                {
                    "id": "emb2",
                    "kind": "fact",
                    "priority": "P1",
                    "source": "itest",
                    "tags": ["embed"],
                    "content": "Hashed vector should not be stored",
                }
            )
            self.assertIsNotNone(rec)
            self.assertFalse("embedding" in (rec.metadata or {}))

    def test_write_then_retrieve_smoke(self):
        with tempfile.TemporaryDirectory() as td:
            configure_brain(enabled=True, base_path=td)
            brain_write(
                {
                    "id": "a1",
                    "kind": "fact",
                    "priority": "P0",
                    "source": "itest",
                    "tags": ["python", "jsonl"],
                    "content": "JSONL append is cheap and robust",
                }
            )
            brain_write(
                {
                    "id": "a2",
                    "kind": "strategy",
                    "priority": "P1",
                    "source": "itest",
                    "tags": ["pipeline"],
                    "content": "Checkpoint periodically to compact records",
                }
            )
            stats = checkpoint()

            out = brain_retrieve("jsonl robust", mode="facts", limit=3, min_score=0.1)
            self.assertTrue(len(out) >= 1)
            self.assertEqual(out[0]["kind"], "fact")

            # rollback should succeed to the last checkpoint version
            self.assertTrue(stats.get("version"))
            self.assertTrue(rollback(stats["version"]))

    def test_tiered_recall_respects_priority_order(self):
        with tempfile.TemporaryDirectory() as td:
            configure_brain(
                enabled=True,
                base_path=td,
                tiered_recall=True,
                tiered_order=["P0", "P1", "P2"],
                tiered_limits=[1, 1, 1],
            )
            brain_write(
                {
                    "id": "p2",
                    "kind": "fact",
                    "priority": "P2",
                    "source": "itest",
                    "content": "common term",
                }
            )
            brain_write(
                {
                    "id": "p0",
                    "kind": "fact",
                    "priority": "P0",
                    "source": "itest",
                    "content": "common term",
                }
            )
            brain_write(
                {
                    "id": "p1",
                    "kind": "fact",
                    "priority": "P1",
                    "source": "itest",
                    "content": "common term",
                }
            )

            out = brain_retrieve("common term", mode="facts", limit=3, min_score=0.0)
            self.assertEqual([r["priority"] for r in out], ["P0", "P1", "P2"])

    def test_backfill_embeddings_appends_updates(self):
        class _FakeEmb:
            def __init__(self, vec):
                self._vec = vec

            def tolist(self):
                return list(self._vec)

        class _FakeModel:
            def encode(self, texts, normalize_embeddings=True):
                return [_FakeEmb([0.2, 0.1, 0.0])]

        with tempfile.TemporaryDirectory() as td:
            # First run with hashed-vector (no embedding stored)
            configure_brain(enabled=True, base_path=td, scorer_type="hashed-vector")
            rec = brain_write(
                {
                    "id": "bf1",
                    "kind": "fact",
                    "priority": "P1",
                    "source": "itest",
                    "content": "Backfill me",
                }
            )
            self.assertIsNotNone(rec)
            self.assertFalse("embedding" in (rec.metadata or {}))

            # Reconfigure with real vector scorer and backfill
            scorer = VectorScorer(dim=3, use_sentence_transformers=False)
            scorer._st_model = _FakeModel()
            scorer.use_sentence_transformers = True
            configure_brain(enabled=True, base_path=td, scorer=scorer)

            stats = backfill_embeddings()
            self.assertGreaterEqual(stats.get("updated", 0), 1)

            out = brain_retrieve("backfill", mode="facts", limit=3, min_score=0.0)
            self.assertTrue(any("embedding" in (r.get("metadata") or {}) for r in out))

    def test_novelty_gate_skips_duplicate_writes(self):
        with tempfile.TemporaryDirectory() as td:
            configure_brain(
                enabled=True,
                base_path=td,
                scorer_type="keyword",
                novelty_enabled=True,
                novelty_min_similarity=0.85,
                novelty_window_seconds=3600,
            )
            brain_write(
                {
                    "id": "n1",
                    "kind": "fact",
                    "priority": "P1",
                    "source": "itest",
                    "tags": ["dup"],
                    "content": "Same content should be skipped",
                }
            )
            brain_write(
                {
                    "id": "n2",
                    "kind": "fact",
                    "priority": "P1",
                    "source": "itest",
                    "tags": ["dup"],
                    "content": "Same content should be skipped",
                }
            )
            records_path = Path(td) / "brain" / "records.jsonl"
            with records_path.open("r", encoding="utf-8") as f:
                lines = [line for line in f if line.strip()]
            self.assertEqual(len(lines), 1)

            brain_write(
                {
                    "id": "n3",
                    "kind": "fact",
                    "priority": "P1",
                    "source": "itest",
                    "tags": ["uniq"],
                    "content": "Different content should be stored",
                }
            )
            with records_path.open("r", encoding="utf-8") as f:
                lines = [line for line in f if line.strip()]
            self.assertEqual(len(lines), 2)


if __name__ == "__main__":
    unittest.main()
