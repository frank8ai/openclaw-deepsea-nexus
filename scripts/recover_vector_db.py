#!/usr/bin/env python3
"""
Archived reference: one-off vector DB recovery helper for an older damaged
collection layout. Keep for manual forensics/recovery only; it is not the
current source of truth for normal v5 runtime operations.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path


def resolve_openclaw_home() -> Path:
    return Path(os.environ.get("OPENCLAW_HOME", "~/.openclaw")).expanduser().resolve()


def resolve_workspace_root() -> Path:
    return Path(
        os.environ.get("OPENCLAW_WORKSPACE", resolve_openclaw_home() / "workspace")
    ).expanduser().resolve()


def resolve_vector_db_path() -> Path:
    override = os.environ.get("NEXUS_RECOVER_VECTOR_DB", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    primary = os.environ.get("NEXUS_VECTOR_DB", "").strip()
    if primary:
        return Path(primary).expanduser().resolve()
    return (resolve_workspace_root() / "memory" / ".vector_db").resolve()


def resolve_backup_collection() -> str:
    return os.environ.get("NEXUS_RECOVER_COLLECTION", "deepsea_nexus_backup").strip() or "deepsea_nexus_backup"


def resolve_segment_id() -> str:
    return os.environ.get(
        "NEXUS_RECOVER_SEGMENT_ID",
        "7c02facf-8a51-4f32-a773-d1decdc2f27b",
    ).strip()


VECTOR_DB_PATH = str(resolve_vector_db_path())
BACKUP_COLLECTION = resolve_backup_collection()
SEGMENT_ID = resolve_segment_id()

def extract_data(limit=None):
    """从 SQLite 提取数据"""
    conn = sqlite3.connect(f"{VECTOR_DB_PATH}/chroma.sqlite3")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT e.embedding_id
        FROM embeddings e
        WHERE e.segment_id = ?
    """, (SEGMENT_ID,))
    embedding_ids = [row[0] for row in cursor.fetchall()]
    print(f"找到 {len(embedding_ids)} 条记录")
    
    documents = []
    metadatas = []
    ids = []
    
    for emb_id in embedding_ids[:limit] if limit else embedding_ids:
        # 获取文档内容
        cursor.execute("""
            SELECT string_value FROM embedding_metadata
            WHERE id = (SELECT id FROM embeddings WHERE embedding_id = ?)
            AND key = 'chroma:document'
        """, (emb_id,))
        doc_row = cursor.fetchone()
        
        if not doc_row:
            continue
            
        # 获取所有 metadata（排除 chroma:document）
        cursor.execute("""
            SELECT key, string_value FROM embedding_metadata
            WHERE id = (SELECT id FROM embeddings WHERE embedding_id = ?)
        """, (emb_id,))
        meta_rows = cursor.fetchall()
        
        documents.append(doc_row[0])
        # 过滤掉 chroma:document 键
        meta = {row[0]: row[1] for row in meta_rows if row[1] and row[0] != 'chroma:document'}
        metadatas.append(meta)
        ids.append(emb_id)
    
    conn.close()
    return ids, documents, metadatas

def recover_to_new_collection(batch_size=100):
    """恢复到新集合"""
    import chromadb

    print("\n" + "=" * 50)
    print("开始恢复数据到新集合")
    print("=" * 50)
    
    # 获取所有数据
    all_ids, all_docs, all_metas = extract_data()
    print(f"准备恢复 {len(all_ids)} 条数据...")
    
    # 连接向量库
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    
    # 创建或获取备份集合
    try:
        coll = client.get_collection(BACKUP_COLLECTION)
        print(f"集合已存在，有 {coll.count()} 条数据")
    except:
        print(f"创建新集合: {BACKUP_COLLECTION}")
        coll = client.create_collection(BACKUP_COLLECTION)
    
    # 批量添加数据
    total = len(all_ids)
    for i in range(0, total, batch_size):
        batch_ids = all_ids[i:i+batch_size]
        batch_docs = all_docs[i:i+batch_size]
        batch_metas = all_metas[i:i+batch_size]
        
        coll.add(
            documents=batch_docs,
            metadatas=batch_metas,
            ids=batch_ids
        )
        
        print(f"进度: {min(i+batch_size, total)}/{total}")
    
    print(f"\n✅ 恢复完成! 共 {coll.count()} 条数据")
    return coll

def test_search():
    """测试搜索"""
    import chromadb

    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    coll = client.get_collection(BACKUP_COLLECTION)
    
    print(f"\n集合 '{BACKUP_COLLECTION}': {coll.count()} 条数据")
    
    # 搜索测试
    results = coll.query(query_texts=["agent forum"], n_results=5)
    print(f"\n搜索 'agent forum': {len(results['documents'][0])} 条结果")
    for doc in results['documents'][0][:3]:
        print(f"  - {doc[:80]}...")

if __name__ == "__main__":
    recover_to_new_collection()
    test_search()
