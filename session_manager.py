"""
Session 管理模块

功能：
- 创建/管理对话会话
- 会话边界追踪
- 会话级元数据

F1. Session 管理
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import yaml


@dataclass
class SessionInfo:
    """会话信息"""
    session_id: str
    topic: str
    created_at: str
    last_active: str
    status: str  # active, paused, archived
    chunk_count: int = 0
    gold_count: int = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SessionInfo':
        return cls(**data)


def get_session_manager(*args, **kwargs) -> "SessionManager":
    """Backward-compatible accessor used by tests and scripts."""
    return SessionManager(*args, **kwargs)


def start_session(topic: str, *args, **kwargs) -> str:
    """Module-level convenience wrapper for backward compatibility."""
    return SessionManager(*args, **kwargs).start_session(topic)


def close_session(session_id: str, *args, **kwargs) -> None:
    """Module-level convenience wrapper for backward compatibility."""
    return SessionManager(*args, **kwargs).close_session(session_id)


class SessionManager:
    """会话管理器"""
    
    def __init__(self, base_path: str = None):
        """
        初始化会话管理器
        
        Args:
            base_path: 记忆库根路径
        """
        if base_path is None:
            self.base_path = os.path.expanduser("~/.openclaw/workspace/memory")
        else:
            self.base_path = base_path
        
        # 会话索引文件
        self.index_file = os.path.join(self.base_path, "_sessions_index.json")
        
        # 确保目录存在
        os.makedirs(self.base_path, exist_ok=True)
        
        # 加载索引
        self.sessions: Dict[str, SessionInfo] = self._load_index()
    
    def _load_index(self) -> Dict[str, SessionInfo]:
        """加载会话索引"""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {
                        sid: SessionInfo.from_dict(info) 
                        for sid, info in data.items()
                    }
            except Exception as e:
                print(f"加载会话索引失败: {e}")
                return {}
        return {}
    
    def _save_index(self):
        """保存会话索引"""
        try:
            data = {
                sid: info.to_dict() 
                for sid, info in self.sessions.items()
            }
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存会话索引失败: {e}")
    
    def start_session(self, topic: str, auto_create: bool = True) -> str:
        """
        创建新会话
        
        Args:
            topic: 会话话题
            auto_create: 是否自动创建
            
        Returns:
            session_id: 格式 "HHMM_Topic"
        """
        # 生成 session_id
        now = datetime.now()
        time_str = now.strftime("%H%M")
        # 清理话题中的特殊字符
        clean_topic = "".join(c for c in topic if c.isalnum() or c in "_- ")
        safe_topic = clean_topic[:20].strip() if clean_topic else "Unknown"
        session_id = f"{time_str}_{safe_topic}"
        
        # 如果已存在，添加序号
        original_id = session_id
        counter = 1
        while session_id in self.sessions:
            session_id = f"{original_id}_{counter}"
            counter += 1
        
        # 创建会话
        now_str = datetime.now().isoformat()
        self.sessions[session_id] = SessionInfo(
            session_id=session_id,
            topic=topic,
            created_at=now_str,
            last_active=now_str,
            status="active"
        )
        
        self._save_index()
        print(f"✓ 会话创建: {session_id}")
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """获取会话信息"""
        return self.sessions.get(session_id)
    
    def update_activity(self, session_id: str):
        """更新会话活跃时间"""
        if session_id in self.sessions:
            self.sessions[session_id].last_active = datetime.now().isoformat()
            self._save_index()
    
    def close_session(self, session_id: str):
        """关闭会话"""
        if session_id in self.sessions:
            self.sessions[session_id].status = "paused"
            self.sessions[session_id].last_active = datetime.now().isoformat()
            self._save_index()
            print(f"✓ 会话已关闭: {session_id}")
    
    def archive_session(self, session_id: str):
        """归档会话"""
        if session_id in self.sessions:
            self.sessions[session_id].status = "archived"
            self.sessions[session_id].last_active = datetime.now().isoformat()
            self._save_index()
            print(f"✓ 会话已归档: {session_id}")
    
    def list_active_sessions(self) -> List[SessionInfo]:
        """列出活跃会话"""
        return [
            info for info in self.sessions.values()
            if info.status == "active"
        ]
    
    def list_recent_sessions(self, days: int = 7) -> List[SessionInfo]:
        """列出最近会话"""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        return [
            info for info in self.sessions.values()
            if info.created_at > cutoff_str
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取会话统计"""
        active = len([s for s in self.sessions.values() if s.status == "active"])
        paused = len([s for s in self.sessions.values() if s.status == "paused"])
        archived = len([s for s in self.sessions.values() if s.status == "archived"])
        
        return {
            "total_sessions": len(self.sessions),
            "active": active,
            "paused": paused,
            "archived": archived
        }
    
    def add_chunk(self, session_id: str):
        """为会话添加 chunk 计数"""
        if session_id in self.sessions:
            self.sessions[session_id].chunk_count += 1
            self.update_activity(session_id)
    
    def add_gold(self, session_id: str):
        """为会话添加 gold 计数"""
        if session_id in self.sessions:
            self.sessions[session_id].gold_count += 1


# 测试
if __name__ == "__main__":
    manager = SessionManager()
    
    # 创建会话
    sid = manager.start_session("Python 学习")
    print(f"创建会话: {sid}")
    
    # 列出活跃会话
    print("\n活跃会话:")
    for s in manager.list_active_sessions():
        print(f"  - {s.session_id}: {s.topic}")
    
    # 统计
    print(f"\n统计: {manager.get_stats()}")
