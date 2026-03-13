#!/bin/bash
# Deep-Sea Nexus rollback script

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Config
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_DIR="${NEXUS_PROJECT_DIR:-${DEEPSEA_NEXUS_ROOT:-${DEFAULT_PROJECT_DIR}}}"
BACKUP_DIR="${NEXUS_ROLLBACK_BACKUP_DIR:-${PROJECT_DIR}/backups}"

# Parse arguments
TARGET=""
AUTO_YES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --target)
            TARGET="$2"
            shift 2
            ;;
        --yes)
            AUTO_YES=true
            shift
            ;;
        --help)
            echo "用法: rollback.sh [选项]"
            echo ""
            echo "选项:"
            echo "  --target VERSION  指定回滚版本 (tag 或 commit)"
            echo "  --yes             自动确认 (非交互模式)"
            echo "  --help            显示帮助"
            echo ""
            echo "示例:"
            echo "  ./rollback.sh --target HEAD~1 --yes"
            echo "  ./rollback.sh --target a210b64"
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            exit 1
            ;;
    esac
done

echo -e "${YELLOW}🔙 Deep-Sea Nexus Rollback${NC}"
echo ""

# Check if git is available
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git not found${NC}"
    exit 1
fi

if [ ! -d "${PROJECT_DIR}" ]; then
    echo -e "${RED}❌ 项目目录不存在: ${PROJECT_DIR}${NC}"
    exit 1
fi

if ! git -C "${PROJECT_DIR}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo -e "${RED}❌ 不是 git 仓库: ${PROJECT_DIR}${NC}"
    exit 1
fi

cd "${PROJECT_DIR}"

# Get available tags
echo "📋 可用的回滚点:"
git tag -l | tail -10

# Check target
if [ -z "$TARGET" ]; then
    echo ""
    read -p "输入要回滚到的版本 (tag 或 commit): " TARGET
fi

# Check if target exists
if ! git rev-parse --verify "${TARGET}" &> /dev/null; then
    echo -e "${RED}❌ 版本不存在: ${TARGET}${NC}"
    exit 1
fi

# Create backup before rollback
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="rollback_${TIMESTAMP}"
echo -e "${YELLOW}📦 创建备份: ${BACKUP_NAME}${NC}"

mkdir -p "${BACKUP_DIR}"
mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"
git archive HEAD | tar -x -C "${BACKUP_DIR}/${BACKUP_NAME}"

# Show what will change
echo ""
echo -e "${YELLOW}⚠️  将要回滚到: ${TARGET}${NC}"
echo "变更的文件:"
git diff --name-only "${TARGET}" HEAD 2>/dev/null || echo "(首次部署，无历史变更)"

# Confirm
if [ "$AUTO_YES" = false ]; then
    echo ""
    read -p "确认回滚? (y/n): " CONFIRM
else
    echo ""
    echo "⚠️  自动确认模式"
    CONFIRM="y"
fi

if [ "${CONFIRM}" != "y" ] && [ "${CONFIRM}" != "Y" ]; then
    echo "已取消"
    exit 0
fi

# Perform rollback
echo -e "${GREEN}🔄 执行回滚...${NC}"

git reset --hard "${TARGET}"
echo -e "${GREEN}✅ 已回滚到 ${TARGET}${NC}"

echo ""
echo -e "${GREEN}✅ 回滚完成!${NC}"
echo -e "备份位置: ${BACKUP_DIR}/${BACKUP_NAME}"
echo ""
echo "如需恢复备份:"
echo "  cd ${PROJECT_DIR}"
echo "  git reset --hard HEAD"
