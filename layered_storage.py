#!/usr/bin/env python3
"""
Layered Storage - 简化的分层记忆存储

为 context_injector.py 提供依赖

功能：
- HOT (热记忆): 最近活跃
- WARM (温记忆): 最近使用
- COLD (冷记忆): 历史归档
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from runtime_paths import resolve_openclaw_workspace


def resolve_default_base_path() -> str:
    return os.path.join(resolve_openclaw_workspace(), "memory")


class MemoryTier(Enum):
    """记忆层级"""
    HOT = "hot"    # 最近活跃
    WARM = "warm"   # 最近使用
    COLD = "cold"   # 历史归档


@dataclass
class MemoryItem:
    """记忆条目"""
    content: str
    title: str
    tier: MemoryTier
    created_at: str = ""
    accessed_at: str = ""
    access_count: int = 0
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.accessed_at:
            self.accessed_at = self.created_at
    
    def touch(self):
        """更新访问时间"""
        self.accessed_at = datetime.now().isoformat()
        self.access_count += 1


class LayeredStorage:
    """
    分层记忆存储管理器
    
    使用方法:
    storage = LayeredStorage()
    
    # 添加
    storage.add(content, title, tier=MemoryTier.HOT)
    
    # 获取
    item = storage.get(title)
    
    # 搜索
    results = storage.search(query)
    """
    
    def __init__(self, base_path: str = None):
        """
        初始化
        
        Args:
            base_path: 记忆文件根路径
        """
        self.base_path = os.path.expanduser(base_path) if base_path else resolve_default_base_path()
        self.index: Dict[str, MemoryItem] = {}
        
        # 创建目录
        os.makedirs(self.base_path, exist_ok=True)
        
        # 加载现有记忆
        self._load_all()
    
    def _load_all(self):
        """加载所有记忆"""
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                if file.endswith('.md'):
                    self._load_file(os.path.join(root, file))
    
    def _load_file(self, filepath: str):
        """加载单个文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取标题
            title = Path(filepath).stem
            if title.startswith('session_'):
                title = title[8:]
            
            # 解析 YAML frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 2:
                    # 跳过 frontmatter
                    content = parts[-1] if len(parts) > 2 else content
            
            # 清理内容
            content = content.strip()
            if len(content) > 500:
                content = content[:500] + "..."
            
            # 添加到索引
            item = MemoryItem(
                content=content,
                title=title,
                tier=MemoryTier.COLD,
                metadata={"source": filepath}
            )
            self.index[title] = item
            
        except Exception as e:
            print(f"加载失败 {filepath}: {e}")
    
    def add(self, content: str, title: str, tier: MemoryTier = MemoryTier.WARM,
            tags: List[str] = None):
        """
        添加记忆
        
        Args:
            content: 记忆内容
            title: 标题
            tier: 层级
            tags: 标签列表
        """
        item = MemoryItem(
            content=content,
            title=title,
            tier=tier,
            metadata={"tags": tags or []}
        )
        self.index[title] = item
        return item
    
    def get(self, title: str) -> Optional[MemoryItem]:
        """获取记忆"""
        item = self.index.get(title)
        if item:
            item.touch()
        return item
    
    def search(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """
        搜索记忆
        
        Args:
            query: 查询词
            limit: 返回数量
            
        Returns:
            匹配的记忆列表
        """
        query_lower = query.lower()
        results = []
        
        for item in self.index.values():
            if query_lower in item.content.lower() or query_lower in item.title.lower():
                results.append(item)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_hot(self, limit: int = 10) -> List[MemoryItem]:
        """获取热记忆（最近访问）"""
        sorted_items = sorted(
            self.index.values(),
            key=lambda x: x.accessed_at,
            reverse=True
        )
        return sorted_items[:limit]
    
    def get_by_tier(self, tier: MemoryTier) -> List[MemoryItem]:
        """按层级获取"""
        return [item for item in self.index.values() if item.tier == tier]
    
    def upgrade_tier(self, title: str, new_tier: MemoryTier) -> bool:
        """
        提升层级
        
        Args:
            title: 记忆标题
            new_tier: 新层级
            
        Returns:
            是否成功
        """
        item = self.index.get(title)
        if item:
            item.tier = new_tier
            return True
        return False
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            "total": len(self.index),
            "hot": len(self.get_by_tier(MemoryTier.HOT)),
            "warm": len(self.get_by_tier(MemoryTier.WARM)),
            "cold": len(self.get_by_tier(MemoryTier.COLD)),
        }


# 便捷函数
def create_layered_storage(base_path: str = None) -> LayeredStorage:
    """创建分层存储实例"""
    return LayeredStorage(base_path)


if __name__ == "__main__":
    # 测试
    storage = LayeredStorage()
    
    # 添加测试数据
    storage.add("Python 列表推导式学习", "Python列表", MemoryTier.HOT)
    storage.add("FastAPI 项目配置", "FastAPI配置", MemoryTier.WARM)
    
    # 搜索
    results = storage.search("Python")
    print(f"搜索 'Python': {len(results)} 条")
    
    for item in results:
        print(f"  [{item.tier.value}] {item.title}: {item.content[:50]}...")
    
    # 统计
    stats = storage.get_stats()
    print(f"\n统计: {stats}")
