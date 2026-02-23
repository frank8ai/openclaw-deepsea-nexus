"""
ChromaDB 向量存储集成
直接使用 ChromaDB，无需额外依赖
"""

import os
import sys
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# 导入 ChromaDB
# Prefer the workspace venv (.venv-nexus) if running under a different Python.
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    # Attempt to add workspace venv site-packages to sys.path.
    try:
        _ws = os.path.expanduser("~/.openclaw/workspace")
        _venv_lib = os.path.join(_ws, ".venv-nexus", "lib")
        if os.path.isdir(_venv_lib):
            for _name in os.listdir(_venv_lib):
                _sp = os.path.join(_venv_lib, _name, "site-packages")
                if os.path.isdir(_sp):
                    sys.path.insert(0, _sp)
        import chromadb  # type: ignore
        from chromadb.config import Settings  # type: ignore
        CHROMA_AVAILABLE = True
    except Exception:
        CHROMA_AVAILABLE = False


@dataclass
class NexusDocument:
    """文档"""
    doc_id: str
    content: str
    metadata: Dict[str, Any]
    embedding: List[float] = None


class VectorStore:
    """ChromaDB 向量存储"""
    
    def __init__(self, 
                 collection_name: str = "deepsea_nexus",
                 persist_path: str = None):
        """
        初始化向量存储
        
        Args:
            collection_name: 集合名称
            persist_path: 持久化路径
        """
        if not CHROMA_AVAILABLE:
            raise ImportError("ChromaDB not installed. Run: pip install chromadb")
        
        self.collection_name = collection_name
        
        # 设置持久化路径
        if persist_path is None:
            persist_path = os.path.expanduser("~/.openclaw/workspace/memory/.vector_db_final")
        else:
            persist_path = os.path.expanduser(str(persist_path))

        persist_path = os.path.abspath(persist_path)
        
        self.persist_path = persist_path
        os.makedirs(persist_path, exist_ok=True)
        
        # 创建客户端
        self.client = chromadb.PersistentClient(
            path=persist_path,
            settings=Settings(anonymized_telemetry=False),
            tenant="default_tenant",
            database="default_database",
        )
        
        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Deep-Sea Nexus Memory"}
        )
    
    def add(self, 
            documents: List[str],
            embeddings: List[List[float]] = None,
            ids: List[str] = None,
            metadatas: List[Dict[str, Any]] = None) -> List[str]:
        """
        添加文档
        
        Args:
            documents: 文档内容列表
            embeddings: 嵌入向量
            ids: 文档 ID
            metadatas: 元数据
            
        Returns:
            List[str]: 添加的 ID
        """
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4())[:8] for _ in documents]
        
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas
        )
        
        return ids
    
    def search(self, 
               query: str,
               n_results: int = 5,
               where: Dict[str, Any] = None) -> List[Dict]:
        """
        搜索
        
        Args:
            query: 查询文本
            n_results: 返回数量
            where: 过滤条件
            
        Returns:
            List[Dict]: 搜索结果
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )
        
        return results
    
    def get(self, 
            ids: List[str] = None,
            where: Dict[str, Any] = None,
            limit: int = 100) -> List[Dict]:
        """
        获取文档
        
        Args:
            ids: 文档 ID
            where: 过滤条件
            limit: 限制数量
            
        Returns:
            List[Dict]: 文档列表
        """
        results = self.collection.get(
            ids=ids,
            where=where,
            limit=limit
        )
        
        return results
    
    def delete(self, ids: List[str]):
        """删除文档"""
        self.collection.delete(ids=ids)
    
    @property
    def count(self) -> int:
        """文档数量"""
        return self.collection.count()


class Embedder:
    """文本嵌入器"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        初始化嵌入器
        
        Args:
            model_name: 模型名称
        """
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            self.available = True
        except ImportError:
            self.available = False
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        生成嵌入向量
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 嵌入向量
        """
        if not self.available:
            return None
        
        return self.model.encode(texts).tolist()


# 便捷函数
def create_vector_store(config: Optional[Dict[str, Any]] = None,
                        collection: str = "deepsea_nexus") -> VectorStore:
    """Create vector store.

    Args:
        config: Optional app config dict; if provided, reads:
            - config['nexus']['vector_db_path'] (persist path)
            - config['nexus']['collection_name'] (collection override)
        collection: Default collection name.
    """
    persist_path = None
    if isinstance(config, dict):
        nexus_cfg = config.get("nexus", {}) if isinstance(config.get("nexus", {}), dict) else {}
        persist_path = nexus_cfg.get("vector_db_path") or persist_path
        collection = nexus_cfg.get("collection_name") or collection

    # Allow env overrides for all agents (main + subagents) to share the same store.
    persist_path = os.environ.get("NEXUS_VECTOR_DB", "").strip() or persist_path
    collection = os.environ.get("NEXUS_COLLECTION", "").strip() or collection

    return VectorStore(collection_name=collection, persist_path=persist_path)


def create_embedder(model: str = "all-MiniLM-L6-v2") -> Embedder:
    """创建嵌入器"""
    return Embedder(model_name=model)


if __name__ == "__main__":
    # 测试
    print("=== VectorStore 测试 ===")
    
    # 创建
    store = VectorStore()
    print(f"集合: {store.collection_name}")
    print(f"文档数: {store.count}")
    
    # 添加测试文档
    docs = [
        "Python 列表推导式很强大",
        "FastAPI 是现代 Web 框架",
        "ChromaDB 用于向量存储"
    ]
    
    ids = store.add(docs, ids=["1", "2", "3"])
    print(f"添加了 {len(ids)} 个文档")
    
    # 搜索
    results = store.search("Python", n_results=2)
    print(f"搜索 Python: {len(results.get('documents', []))} 条结果")
    
    for doc, meta in zip(results.get('documents', []), results.get('metadatas', [])):
        print(f"  - {doc}")
