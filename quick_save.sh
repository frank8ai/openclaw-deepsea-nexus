#!/bin/bash
# Legacy summary capture helper kept for historical local workflows.
# It is not the current v5 summary/runtime entrypoint.
# Current docs:
# - docs/README.md
# - docs/API_CURRENT.md
# - docs/LOCAL_DEPLOY.md
# 智能摘要快速保存脚本 - 简化版
# 用法: ./quick_save.sh "对话ID" "回复内容"

NEXUS_DIR="/Users/yizhi/.openclaw/workspace/skills/deepsea-nexus"
LOG_DIR="$HOME/.openclaw/logs/summaries"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 参数检查
if [ $# -lt 2 ]; then
    echo "❌ 用法: $0 <对话ID> <回复内容>"
    exit 1
fi

CONV_ID="$1"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 将内容保存到临时文件
TMP_FILE=$(mktemp)
echo "$2" > "$TMP_FILE"

# 检查是否包含摘要格式
if grep -q "## 📋 总结" "$TMP_FILE"; then
    echo "✅ 检测到摘要格式，保存中..."
    
    # 保存完整内容到文本文件
    SAFE_ID=$(echo "$CONV_ID" | tr '/' '_')
    SAVE_FILE="$LOG_DIR/${SAFE_ID}.txt"
    cp "$TMP_FILE" "$SAVE_FILE"
    
    echo "✅ 已保存到: $SAVE_FILE"
    echo "📝 内容长度: $(wc -c < "$SAVE_FILE") 字节"
    
else
    echo "ℹ️ 未检测到 ## 📋 总结 格式，跳过保存"
fi

# 清理临时文件
rm -f "$TMP_FILE"
