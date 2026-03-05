#!/bin/bash
# 后台预热服务 - 一次性预热后保持进程存活

VENV="${NEXUS_PYTHON_PATH:-/Users/yizhi/miniconda3/envs/openclaw-nexus/bin/python}"
SCRIPT="/Users/yizhi/.openclaw/workspace/deepsea-nexus/scripts/warmup.py"
LOG="/tmp/nexus_warmup.log"

echo "$(date): 启动预热..." >> $LOG
$VENV $SCRIPT >> $LOG 2>&1
echo "$(date): 预热完成，进程保持..." >> $LOG

# 保持进程存活（无限循环）
while true; do
    sleep 3600
done
