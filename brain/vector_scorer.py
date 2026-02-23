from __future__ import annotations

import hashlib
import math
from typing import Dict, Optional

from .models import BrainRecord
from .scoring import Scorer


def _tokenize(text: str) -> list[str]:
    return [t for t in text.lower().split() if t]


class VectorScorer(Scorer):
    """Vector-like scorer with optional real embeddings.

    - If sentence-transformers is available, uses a lightweight ST model.
    - Otherwise falls back to a dependency-free hashed bag-of-words embedding.

    This keeps production stable while allowing gradual upgrades.
    """

    def __init__(
        self,
        dim: int = 256,
        use_sentence_transformers: bool = True,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        if dim <= 0:
            raise ValueError("dim must be positive")
        self.dim = dim
        self.model_name = model_name
        env_disable = str(__import__('os').environ.get('NEXUS_DISABLE_SENTENCE_TRANSFORMERS', '')).strip().lower() in {'1','true','yes'}
        self.use_sentence_transformers = bool(use_sentence_transformers) and (not env_disable)
        self._cache: Dict[str, list[float]] = {}

        self._st_model = None
        if self.use_sentence_transformers:
            try:
                from sentence_transformers import SentenceTransformer

                # Lazy-ish init: construct once, reuse, and keep fallback path.
                self._st_model = SentenceTransformer(self.model_name)
            except Exception:
                self._st_model = None

    def _hash_token(self, token: str) -> int:
        h = hashlib.sha256(token.encode("utf-8")).digest()
        return int.from_bytes(h[:4], "big")

    def embed(self, text: str) -> list[float]:
        key = f"{self.model_name}:{self.dim}:{text}"
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        # Prefer real embeddings when available.
        if self._st_model is not None:
            emb = self._st_model.encode([text], normalize_embeddings=True)
            vec = [float(x) for x in emb[0].tolist()]
            self._cache[key] = vec
            return vec

        # Fallback: hashed bag-of-words embedding
        vec = [0.0] * self.dim
        for tok in _tokenize(text):
            idx = self._hash_token(tok) % self.dim
            vec[idx] += 1.0

        # L2 normalize
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        vec = [v / norm for v in vec]
        self._cache[key] = vec
        return vec

    def record_text(self, record: BrainRecord) -> str:
        return " ".join(
            [
                record.kind,
                record.source,
                record.content,
                " ".join(record.tags),
            ]
        ).strip()

    def cosine(self, a: list[float], b: list[float]) -> float:
        # Both embeddings are normalized; cosine reduces to dot product.
        dot = 0.0
        for i in range(min(len(a), len(b))):
            dot += a[i] * b[i]
        return dot

    def score(self, query: str, record: BrainRecord, mode: str) -> float:
        if not query.strip():
            return 0.0

        record_text = self.record_text(record)
        qv = self.embed(query)

        rv = None
        meta = record.metadata or {}
        emb = meta.get("embedding")
        if isinstance(emb, list) and emb:
            rv = [float(x) for x in emb]
        if rv is None:
            rv = self.embed(record_text)
        base = max(0.0, min(1.0, self.cosine(qv, rv)))

        mode_bonus = 0.0
        kind = (record.kind or "").strip().lower()
        if mode == "facts" and kind in {"fact", "facts"}:
            mode_bonus = 0.05
        if mode == "strategy" and kind in {"strategy", "plan"}:
            mode_bonus = 0.05

        priority_weight = {"P0": 1.2, "P1": 1.0, "P2": 0.85}.get(record.priority, 1.0)
        decay_weight = record.decay if record.decay > 0 else 0.1

        return min(1.0, (base + mode_bonus) * priority_weight * math.sqrt(decay_weight))
