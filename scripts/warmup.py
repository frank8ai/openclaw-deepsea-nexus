#!/usr/bin/env python3
"""
DeepSea Nexus 预热脚本
预加载模型和向量库，避免首次搜索延迟
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()


def resolve_repo_root() -> Path:
    override = os.environ.get("DEEPSEA_NEXUS_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return SCRIPT_PATH.parent.parent.resolve()


REPO_ROOT = resolve_repo_root()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime_paths import resolve_openclaw_workspace


def resolve_workspace_root() -> Path:
    return Path(resolve_openclaw_workspace()).expanduser().resolve()


def resolve_vector_db_path() -> Path:
    override = os.environ.get("NEXUS_VECTOR_DB", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return (resolve_workspace_root() / "memory" / ".vector_db_restored").resolve()


def resolve_collection_name() -> str:
    return (
        os.environ.get("NEXUS_COLLECTION")
        or os.environ.get("NEXUS_PRIMARY_COLLECTION")
        or "deepsea_nexus_restored"
    )


def bootstrap_repo_paths() -> None:
    vector_store_path = REPO_ROOT / "vector_store"
    retrieval_path = REPO_ROOT / "src" / "retrieval"

    for path in (REPO_ROOT, vector_store_path, retrieval_path):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


bootstrap_repo_paths()


def warmup():
    """预热所有组件"""
    print("🔥 DeepSea Nexus 预热中...")
    
    # 1. 预加载 embedding 模型
    print("  📦 加载 embedding 模型...")
    from sentence_transformers import SentenceTransformer
    embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    _ = embedder.encode(["warmup"])  # 触发实际加载
    print("    ✓ 模型加载完成")
    
    # 2. 初始化 ChromaDB
    print("  🗄️  连接向量库...")
    import chromadb
    from chromadb.config import Settings
    
    path = resolve_vector_db_path()
    client = chromadb.PersistentClient(
        path=str(path),
        settings=Settings(anonymized_telemetry=False),
    )
    collection = client.get_or_create_collection(name=resolve_collection_name())
    print(f"    ✓ 向量库连接成功 ({collection.count()} 文档)")
    
    # 3. 测试检索
    print("  🔍 测试检索...")
    query_embedding = embedder.encode(["test query"]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=1)
    print(f"    ✓ 检索测试成功")
    
    print("\n✅ 预热完成！现在 /recall 命令会快很多。")
    
    # 返回初始化好的组件供后续使用
    return {
        'embedder': embedder,
        'client': client,
        'collection': collection
    }


if __name__ == '__main__':
    warmup()
