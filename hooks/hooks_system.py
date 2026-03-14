#!/usr/bin/env python3
"""
Deep-Sea Nexus Hooks System
事件驱动的AI感知系统

参考 TELOS Hooks 设计，实现：
- pre-prompt: 用户提问前触发
- post-response: AI回复后触发  
- tool-call: 工具调用时触发
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime


class HooksSystem:
    """Nexus Hooks 管理系统"""
    
    def __init__(self, base_path: str = None):
        self.base_path = base_path or Path(__file__).parent
        self.hooks = {
            "pre-prompt": self.base_path / "pre-prompt",
            "post-response": self.base_path / "post-response",
            "tool-call": self.base_path / "tool-call"
        }
    
    def run_hooks(self, hook_type: str, context: Dict = None) -> Dict:
        """执行指定类型的hooks"""
        hook_dir = self.hooks.get(hook_type)
        if not hook_dir or not hook_dir.exists():
            return {"status": "no_hooks", "results": []}
        
        results = []
        context = context or {}
        context["timestamp"] = datetime.now().isoformat()
        
        # 按字母顺序执行所有hooks
        for hook_file in sorted(hook_dir.glob("*")):
            if hook_file.is_file() and not hook_file.name.startswith("."):
                try:
                    result = self._execute_hook(hook_file, context)
                    results.append({
                        "hook": hook_file.name,
                        "status": "success",
                        "output": result
                    })
                except Exception as e:
                    results.append({
                        "hook": hook_file.name,
                        "status": "error",
                        "error": str(e)
                    })
        
        return {
            "status": "completed",
            "hook_type": hook_type,
            "results": results
        }
    
    def _execute_hook(self, hook_file: Path, context: Dict) -> str:
        """执行单个hook脚本"""
        if hook_file.suffix == ".py":
            # Python 脚本
            env = os.environ.copy()
            env["NEXUS_HOOK_CONTEXT"] = json.dumps(context)
            result = subprocess.run(
                ["python3", str(hook_file)],
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )
            return result.stdout or result.stderr
        elif hook_file.suffix == ".sh":
            # Shell 脚本
            env = os.environ.copy()
            env["NEXUS_HOOK_CONTEXT"] = json.dumps(context)
            result = subprocess.run(
                ["bash", str(hook_file)],
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )
            return result.stdout or result.stderr
        else:
            return f"Unknown hook type: {hook_file.suffix}"


# 示例 Hooks

EXAMPLE_HOOKS = {
    "git_status": {
        "description": "显示当前Git状态",
        "trigger": "pre-prompt",
        "content": '''#!/bin/bash
# Git Status Hook - pre-prompt
# 显示当前工作目录的Git状态

cd "${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}" 2>/dev/null || exit 0

echo "=== Git Status ==="
git status --short 2>/dev/null || echo "Not a git repo"

echo "=== Current Branch ==="
git branch --show-current 2>/dev/null || echo "Unknown"

echo "=== Recent Commits ==="
git log --oneline -3 2>/dev/null || echo "No commits"
'''
    },
    "log_interaction": {
        "description": "记录AI交互日志",
        "trigger": "post-response",
        "content": '''#!/usr/bin/env python3
"""记录AI交互到日志文件"""
import os
import json
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.openclaw/logs/ai-interactions.log")

def main():
    context_json = os.environ.get("NEXUS_HOOK_CONTEXT", "{}")
    context = json.loads(context_json)
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "hook_type": "post-response",
        "context": context
    }
    
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\\n")

if __name__ == "__main__":
    main()
'''
    },
    "workspace_sync": {
        "description": "同步工作区状态",
        "trigger": "tool-call",
        "content": '''#!/bin/bash
# Workspace Sync Hook - tool-call
# 同步工作区状态

echo "=== Workspace Status ==="
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"

# 检查运行中的进程
echo "=== Running Processes ==="
ps aux | grep -E "python|node" | grep -v grep | head -5

# 检查内存使用
echo "=== Memory Usage ==="
free -h 2>/dev/null || echo "Memory info not available"
'''
    }
}


def install_example_hooks():
    """安装示例hooks"""
    for name, config in EXAMPLE_HOOKS.items():
        hook_type = config["trigger"]
        content = config["content"]
        
        hook_dir = Path(__file__).parent / "hooks" / hook_type
        hook_file = hook_dir / name
        
        with open(hook_file, "w") as f:
            f.write(content)
        
        os.chmod(hook_file, 0o755)
        print(f"Installed: {hook_file}")


if __name__ == "__main__":
    print("Deep-Sea Nexus Hooks System")
    print("=" * 40)
    
    hooks = HooksSystem()
    print(f"Hooks base path: {hooks.base_path}")
    print(f"Available hook types: {list(hooks.hooks.keys())}")
    
    print("\\nInstalling example hooks...")
    install_example_hooks()
    
    print("\\nExample hooks installed successfully!")
