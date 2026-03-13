#!/bin/bash
# Legacy deploy wrapper kept for historical compatibility.
# Do not treat this as the current v5 deployment entrypoint.
# Current deploy/runtime docs:
# - README.md
# - docs/README.md
# - docs/LOCAL_DEPLOY.md
# - scripts/deploy_local_v5.sh
# Deep-Sea Nexus v2.0 Deployment Script
# Usage: ./deploy.sh [--rollback]

set -e

# Configuration
PROJECT_NAME="Deep-Sea Nexus v2.0"
VERSION="2.0.0"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${SOURCE_DIR}/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    echo_info "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo_error "Python 3 not found!"
        exit 1
    fi
    
    # Check source files
    if [ ! -f "${SOURCE_DIR}/src/nexus_core.py" ]; then
        echo_error "Core file not found: src/nexus_core.py"
        exit 1
    fi
    
    echo_info "Prerequisites OK"
}

# Create backup
create_backup() {
    echo_info "Creating backup..."
    mkdir -p "${BACKUP_DIR}"
    
    BACKUP_FILE="${BACKUP_DIR}/${PROJECT_NAME}_backup_${TIMESTAMP}.tar.gz"
    tar -czf "${BACKUP_FILE}" \
        --exclude='backups' \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.pytest_cache' \
        -C "${SOURCE_DIR}" .
    
    echo_info "Backup created: ${BACKUP_FILE}"
}

# Run tests
run_tests() {
    echo_info "Running tests..."
    
    cd "${SOURCE_DIR}"
    
    if [ -f "requirements.txt" ]; then
        # Install test dependencies
        pip install pytest -q 2>/dev/null || true
    fi
    
    # Run tests
    python3 -m pytest tests/test_complete.py -v --tb=short
    
    if [ $? -eq 0 ]; then
        echo_info "All tests passed!"
    else
        echo_error "Tests failed!"
        exit 1
    fi
}

# Code quality checks
code_quality() {
    echo_info "Running code quality checks..."
    
    # Python syntax check
    python3 -m py_compile "${SOURCE_DIR}/src/nexus_core.py"
    python3 -m py_compile "${SOURCE_DIR}/src/session_split.py"
    python3 -m py_compile "${SOURCE_DIR}/src/index_rebuild.py"
    python3 -m py_compile "${SOURCE_DIR}/src/migrate.py"
    
    echo_info "Code quality OK"
}

# Deploy
deploy() {
    echo_info "Deploying ${PROJECT_NAME} v${VERSION}..."
    
    # Ensure directories exist
    mkdir -p "${SOURCE_DIR}/memory/00_Inbox"
    mkdir -p "${SOURCE_DIR}/memory/10_Projects"
    mkdir -p "${SOURCE_DIR}/memory/90_Memory/$(date +%Y-%m-%d)"
    
    # Initialize system
    cd "${SOURCE_DIR}"
    python3 src/nexus_core.py --init
    
    echo_info "Deployment complete!"
}

# Main
main() {
    echo "========================================"
    echo "  ${PROJECT_NAME} v${VERSION} Deployment"
    echo "========================================"
    echo
    
    case "${1:-}" in
        --rollback)
            echo_warn "Rollback feature - see rollback.sh"
            ;;
        --check)
            check_prerequisites
            ;;
        --test)
            check_prerequisites
            create_backup
            run_tests
            code_quality
            ;;
        *)
            check_prerequisites
            create_backup
            run_tests
            code_quality
            deploy
            ;;
    esac
}

main "$@"
