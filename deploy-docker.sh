#!/bin/bash

# ==============================================================================
# Fixxit.ai OpenWebUI - Docker Deployment Script
# ==============================================================================
# This script deploys the Fixxit.ai OpenWebUI to your production server
#
# Usage:
#   ./deploy-docker.sh              # Deploy latest version
#   ./deploy-docker.sh v1.0.0       # Deploy specific version
#   ./deploy-docker.sh pull         # Pull from GitHub and rebuild
#   ./deploy-docker.sh stop         # Stop running containers
#   ./deploy-docker.sh restart      # Restart containers
#   ./deploy-docker.sh logs         # View logs
#   ./deploy-docker.sh status       # Check status
# ==============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(dirname "$(readlink -f "$0")")"
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.production.local"
IMAGE_NAME="fixxit-openwebui"

# ==============================================================================
# Helper Functions
# ==============================================================================

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠${NC} $1"
}

show_usage() {
    cat << EOF
Usage: $0 [COMMAND] [VERSION]

Commands:
  deploy [version]   Deploy the application (default: latest)
  pull              Pull latest code from GitHub and rebuild
  stop              Stop all containers
  restart           Restart containers
  logs              View container logs (real-time)
  status            Check deployment status
  backup            Backup application data
  help              Show this help message

Examples:
  $0 deploy              # Deploy latest version
  $0 deploy v1.0.0       # Deploy specific version
  $0 pull                # Pull from GitHub and rebuild
  $0 logs                # View logs
EOF
}

# ==============================================================================
# Pre-deployment Checks
# ==============================================================================

check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker is not installed"
        exit 1
    fi
    if ! docker compose version >/dev/null 2>&1; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
}

check_env_file() {
    if [ ! -f "$PROJECT_ROOT/$ENV_FILE" ]; then
        log_error "Environment file not found: $ENV_FILE"
        log "Please copy .env.production to .env.production.local and configure it"
        log "  cp .env.production .env.production.local"
        log "  nano .env.production.local  # Edit with your settings"
        exit 1
    fi
}

check_data_directory() {
    # Load environment to get DATA_VOLUME_PATH
    source "$PROJECT_ROOT/$ENV_FILE"

    if [ -n "$DATA_VOLUME_PATH" ] && [ ! -d "$DATA_VOLUME_PATH" ]; then
        log_warning "Data directory does not exist: $DATA_VOLUME_PATH"
        read -p "Create it now? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            mkdir -p "$DATA_VOLUME_PATH"
            log_success "Created data directory: $DATA_VOLUME_PATH"
        else
            log_error "Cannot proceed without data directory"
            exit 1
        fi
    fi
}

# ==============================================================================
# Deployment Functions
# ==============================================================================

deploy() {
    local version=${1:-latest}

    log "======================================================================"
    log "Fixxit.ai OpenWebUI - Deployment"
    log "======================================================================"
    log "Version:        ${version}"
    log "Compose file:   ${COMPOSE_FILE}"
    log "Environment:    ${ENV_FILE}"
    log "======================================================================"

    check_docker
    check_env_file
    check_data_directory

    cd "$PROJECT_ROOT"

    # Export version for docker-compose
    export BUILD_HASH="${version}"

    log "Pulling Docker image: ${IMAGE_NAME}:${version}"
    if ! docker pull "${IMAGE_NAME}:${version}" 2>/dev/null; then
        log_warning "Could not pull image from registry, using local image"
    fi

    log "Starting deployment..."
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

    log "Waiting for services to be healthy..."
    sleep 5

    if docker compose -f "$COMPOSE_FILE" ps | grep -q "healthy\|Up"; then
        log_success "Deployment successful!"
        show_status
    else
        log_error "Deployment may have issues. Check logs with: $0 logs"
        exit 1
    fi
}

pull_and_rebuild() {
    log "======================================================================"
    log "Pulling latest code from GitHub and rebuilding"
    log "======================================================================"

    check_docker
    cd "$PROJECT_ROOT"

    # Check if git repo
    if [ ! -d ".git" ]; then
        log_error "Not a git repository. Please use 'git clone' first."
        exit 1
    fi

    # Stash any local changes
    log "Checking for local changes..."
    if ! git diff-index --quiet HEAD --; then
        log_warning "Local changes detected. Stashing them..."
        git stash save "Auto-stash before pull - $(date)"
    fi

    # Pull latest
    log "Pulling latest code from origin..."
    CURRENT_BRANCH=$(git branch --show-current)
    git pull origin "$CURRENT_BRANCH" || {
        log_error "Failed to pull from GitHub"
        exit 1
    }

    # Get commit hash
    BUILD_HASH=$(git rev-parse --short HEAD)
    log_success "Pulled latest code (commit: ${BUILD_HASH})"

    # Build new image
    log "Building Docker image..."
    docker compose -f "$COMPOSE_FILE" build --build-arg BUILD_HASH="${BUILD_HASH}" || {
        log_error "Docker build failed"
        exit 1
    }

    log_success "Build complete"

    # Deploy
    read -p "Deploy the new build now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        deploy "${BUILD_HASH}"
    else
        log "Deployment skipped. Deploy later with: $0 deploy ${BUILD_HASH}"
    fi
}

stop_containers() {
    log "Stopping containers..."
    cd "$PROJECT_ROOT"
    docker compose -f "$COMPOSE_FILE" down
    log_success "Containers stopped"
}

restart_containers() {
    log "Restarting containers..."
    cd "$PROJECT_ROOT"
    docker compose -f "$COMPOSE_FILE" restart
    log_success "Containers restarted"
}

show_logs() {
    cd "$PROJECT_ROOT"
    log "Showing logs (Ctrl+C to exit)..."
    docker compose -f "$COMPOSE_FILE" logs -f
}

show_status() {
    cd "$PROJECT_ROOT"
    log "======================================================================"
    log "Deployment Status"
    log "======================================================================"

    docker compose -f "$COMPOSE_FILE" ps

    echo ""
    log "Container health:"
    docker inspect fixxit-openwebui --format='{{.State.Health.Status}}' 2>/dev/null || echo "No health check info"

    echo ""
    log "Resource usage:"
    docker stats --no-stream fixxit-openwebui 2>/dev/null || log_warning "Container not running"

    echo ""
    log "Access the application:"
    source "$ENV_FILE" 2>/dev/null
    log "  Internal: http://localhost:${WEBUI_PORT:-3000}"
    if [ -n "$WEBUI_URL" ]; then
        log "  External: ${WEBUI_URL}"
    fi
}

backup_data() {
    source "$PROJECT_ROOT/$ENV_FILE"

    BACKUP_DIR="${PROJECT_ROOT}/backups"
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    BACKUP_FILE="${BACKUP_DIR}/fixxit-backup-${TIMESTAMP}.tar.gz"

    mkdir -p "$BACKUP_DIR"

    log "Creating backup..."
    log "Source: ${DATA_VOLUME_PATH:-./data}"
    log "Target: ${BACKUP_FILE}"

    tar -czf "$BACKUP_FILE" -C "$(dirname "${DATA_VOLUME_PATH:-./data}")" "$(basename "${DATA_VOLUME_PATH:-./data}")" || {
        log_error "Backup failed"
        exit 1
    }

    log_success "Backup created: ${BACKUP_FILE}"

    # Show backup size
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "Backup size: ${BACKUP_SIZE}"

    # Cleanup old backups (keep last 7)
    log "Cleaning up old backups (keeping last 7)..."
    ls -t "${BACKUP_DIR}"/fixxit-backup-*.tar.gz | tail -n +8 | xargs -r rm
    log_success "Backup complete"
}

# ==============================================================================
# Main Script
# ==============================================================================

COMMAND=${1:-deploy}
VERSION=${2:-latest}

case "$COMMAND" in
    deploy)
        deploy "$VERSION"
        ;;
    pull)
        pull_and_rebuild
        ;;
    stop)
        stop_containers
        ;;
    restart)
        restart_containers
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    backup)
        backup_data
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac
