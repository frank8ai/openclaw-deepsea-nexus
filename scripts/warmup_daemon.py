#!/usr/bin/env python3
"""
DeepSea Nexus 后台预热服务 (带 Socket 接口)
保持模型和向量库常驻内存，避免重复加载延迟
"""

from __future__ import annotations

import json
import os
import signal
import socket
import sys
import threading
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
SOCKET_PATH = os.environ.get("NEXUS_SOCKET_PATH", "/tmp/nexus_warmup.sock")


class NexusWarmupService:
    """预热服务"""
    
    def __init__(self):
        self.embedder = None
        self.client = None
        self.collection = None
        self.running = False
        self.server = None
        
    def initialize(self):
        """初始化所有组件"""
        print("🔥 DeepSea Nexus 预热服务启动中...", flush=True)
        
        # 1. 加载 embedding 模型
        print("  📦 加载 embedding 模型...", flush=True)
        from sentence_transformers import SentenceTransformer
        self.embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print("    ✓ 模型加载完成", flush=True)
        
        # 2. 连接向量库
        print("  🗄️  连接向量库...", flush=True)
        import chromadb
        from chromadb.config import Settings
        
        path = resolve_vector_db_path()
        self.client = chromadb.PersistentClient(
            path=str(path),
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(name=resolve_collection_name())
        print(f"    ✓ 向量库连接成功 ({self.collection.count()} 文档)", flush=True)
        
        # 3. 创建 Unix Socket
        print("  🔌 创建 Socket 接口...", flush=True)
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server.bind(SOCKET_PATH)
        self.server.listen(5)
        os.chmod(SOCKET_PATH, 0o666)
        print(f"    ✓ Socket: {SOCKET_PATH}", flush=True)
        
        self.running = True
        print("\n✅ 预热完成！服务已就绪。\n", flush=True)
        
    def handle_client(self, conn):
        """处理客户端请求"""
        try:
            data = conn.recv(65536).decode()
            request = json.loads(data)
            
            query = request.get("query", "")
            n = request.get("n", 5)
            
            if not query:
                response = {"error": "Empty query"}
            else:
                query_embedding = self.embedder.encode([query]).tolist()
                results = self.collection.query(
                    query_embeddings=query_embedding, 
                    n_results=n
                )
                
                formatted = []
                for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                    formatted.append({
                        "content": doc,
                        "source": meta.get('title', 'unknown'),
                        "relevance": 0.9
                    })
                response = {"results": formatted}
            
            conn.send(json.dumps(response).encode())
        except Exception as e:
            conn.send(json.dumps({"error": str(e)}).encode())
        finally:
            conn.close()
    
    def run(self):
        """运行服务"""
        self.initialize()
        
        while self.running:
            try:
                conn, _ = self.server.accept()
                thread = threading.Thread(target=self.handle_client, args=(conn,))
                thread.daemon = True
                thread.start()
            except Exception as e:
                if self.running:
                    print(f"Socket error: {e}", flush=True)
    
    def shutdown(self):
        """关闭服务"""
        self.running = False
        if self.server:
            self.server.close()
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)
        print("\n👋 预热服务已关闭", flush=True)


def main():
    print("🚀 启动 DeepSea Nexus 后台预热服务...", flush=True)
    
    # 信号处理
    def handle_signal(signum, frame):
        service.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    
    # 启动服务
    global service
    service = NexusWarmupService()
    
    try:
        service.run()
    except KeyboardInterrupt:
        service.shutdown()


if __name__ == '__main__':
    main()
