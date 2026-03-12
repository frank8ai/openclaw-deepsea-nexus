import unittest
import importlib
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]


def _load_local_package():
    spec = importlib.util.spec_from_file_location(
        "deepsea_nexus_local_vector_scorer",
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
brain_vector_module = importlib.import_module(f"{deepsea_nexus.__name__}.brain.vector_scorer")
BrainRecord = brain_models_module.BrainRecord
VectorScorer = brain_vector_module.VectorScorer


class TestVectorScorer(unittest.TestCase):
    def test_vector_scorer_orders_more_similar_higher(self):
        scorer = VectorScorer(dim=128)

        r1 = BrainRecord(id="1", kind="fact", priority="P1", source="t", tags=["python"], content="JSONL append only storage")
        r2 = BrainRecord(id="2", kind="fact", priority="P1", source="t", tags=["go"], content="Kubernetes controllers reconcile loops")

        s1 = scorer.score("jsonl storage", r1, mode="facts")
        s2 = scorer.score("jsonl storage", r2, mode="facts")

        self.assertGreaterEqual(s1, s2)

    def test_vector_scorer_empty_query(self):
        scorer = VectorScorer()
        r = BrainRecord(id="1", kind="fact", priority="P1", source="t", content="anything")
        self.assertEqual(scorer.score(" ", r, mode="facts"), 0.0)


if __name__ == "__main__":
    unittest.main()
