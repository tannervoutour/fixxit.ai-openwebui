#!/bin/bash

# ==============================================================================
# Deploy Frontend to Lightsail - Build Locally, Deploy Remotely
# ==============================================================================
#
# This script builds the frontend locally and deploys to AWS Lightsail
# Usage:
#   ./deploy-to-lightsail.sh [options]
#
# Options:
#   --host <hostname>    SSH hostname or IP (default: read from config)
#   --user <username>    SSH username (default: read from config)
#   --port <port>        SSH port (default: 22)
#   --key <path>         Path to SSH key (default: ~/.ssh/id_rsa)
#   --remote-path <path> Remote project path (default: same as local)
#   --restart            Restart backend after deployment
#   --skip-build         Skip local build (use existing build directory)
#   --dry-run            Show what would be done without executing
#   --help               Show this help message
#
# Configuration:
#   Create a .deploy-config file with your server settings:
#     DEPLOY_HOST="your-lightsail-instance.amazonaws.com"
#     DEPLOY_USER="ubuntu"
#     DEPLOY_PORT="22"
#     DEPLOY_KEY="~/.ssh/your-key.pem"
#     DEPLOY_REMOTE_PATH="/home/ubuntu/fixxit_projectFiles/fixxitUI_OpenWebUI"
#
# ==============================================================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project paths
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$PROJECT_ROOT/build"
CONFIG_FILE="$PROJECT_ROOT/.deploy-config"

# Default configuration
DEPLOY_HOST=""
DEPLOY_USER=""
DEPLOY_PORT="22"
DEPLOY_KEY="$HOME/.ssh/id_rsa"
DEPLOY_REMOTE_PATH="$PROJECT_ROOT"
RESTART_BACKEND=false
SKIP_BUILD=false
DRY_RUN=false

# ==============================================================================
# Utility Functions
# ==============================================================================

print_header() {
    echo ""
    echo -e "${MAGENTA}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║                                                                ║${NC}"
    echo -e "${MAGENTA}║        Deploy Frontend to AWS Lightsail                      ║${NC}"
    echo -e "${MAGENTA}║                                                                ║${NC}"
    echo -e "${MAGENTA}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_step() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN} $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

show_help() {
    head -n 30 "$0" | tail -n +3 | sed 's/^# //' | sed 's/^#//'
    exit 0
}

# ==============================================================================
# Load Configuration
# ==============================================================================

load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        log "Loading configuration from .deploy-config"
        source "$CONFIG_FILE"
        log_success "Configuration loaded"
    else
        log_warning "No .deploy-config file found"
        log "You can create one with your deployment settings"
    fi
}

# ==============================================================================
# Parse Command Line Arguments
# ==============================================================================

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --host)
                DEPLOY_HOST="$2"
                shift 2
                ;;
            --user)
                DEPLOY_USER="$2"
                shift 2
                ;;
            --port)
                DEPLOY_PORT="$2"
                shift 2
                ;;
            --key)
                DEPLOY_KEY="$2"
                shift 2
                ;;
            --remote-path)
                DEPLOY_REMOTE_PATH="$2"
                shift 2
                ;;
            --restart)
                RESTART_BACKEND=true
                shift
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --help)
                show_help
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

# ==============================================================================
# Validation Functions
# ==============================================================================

validate_config() {
    log_step "Validating Configuration"

    local errors=0

    # Check required settings
    if [ -z "$DEPLOY_HOST" ]; then
        log_error "DEPLOY_HOST not set. Use --host or set in .deploy-config"
        errors=$((errors + 1))
    else
        log_success "Deploy host: $DEPLOY_HOST"
    fi

    if [ -z "$DEPLOY_USER" ]; then
        log_error "DEPLOY_USER not set. Use --user or set in .deploy-config"
        errors=$((errors + 1))
    else
        log_success "Deploy user: $DEPLOY_USER"
    fi

    # Check SSH key
    if [ ! -f "$DEPLOY_KEY" ]; then
        log_error "SSH key not found: $DEPLOY_KEY"
        errors=$((errors + 1))
    else
        log_success "SSH key: $DEPLOY_KEY"
    fi

    # Check if build directory exists (if not skipping build)
    if [ "$SKIP_BUILD" = true ] && [ ! -d "$BUILD_DIR" ]; then
        log_error "Build directory not found: $BUILD_DIR"
        log "Cannot skip build when no build directory exists"
        errors=$((errors + 1))
    fi

    if [ $errors -gt 0 ]; then
        log_error "Configuration validation failed with $errors error(s)"
        exit 1
    fi

    log_success "Configuration valid"
}

test_ssh_connection() {
    log_step "Testing SSH Connection"

    if [ "$DRY_RUN" = true ]; then
        log "DRY RUN: Would test SSH connection to $DEPLOY_USER@$DEPLOY_HOST"
        return 0
    fi

    log "Connecting to $DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PORT..."

    if ssh -i "$DEPLOY_KEY" -p "$DEPLOY_PORT" -o ConnectTimeout=10 -o BatchMode=yes \
        "$DEPLOY_USER@$DEPLOY_HOST" "echo 'SSH connection successful'" > /dev/null 2>&1; then
        log_success "SSH connection successful"
    else
        log_error "SSH connection failed"
        log "Please check your credentials and network connection"
        exit 1
    fi
}

check_dependencies() {
    log_step "Checking Dependencies"

    local missing=()

    if ! command -v node &> /dev/null; then
        missing+=("node")
    else
        log_success "Node.js $(node --version) found"
    fi

    if ! command -v npm &> /dev/null; then
        missing+=("npm")
    else
        log_success "npm $(npm --version) found"
    fi

    if ! command -v rsync &> /dev/null; then
        log_warning "rsync not found, will use scp (slower)"
    else
        log_success "rsync found (will use for faster transfers)"
    fi

    if ! command -v ssh &> /dev/null; then
        missing+=("ssh")
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing required dependencies: ${missing[*]}"
        exit 1
    fi
}

# ==============================================================================
# Build Functions
# ==============================================================================

build_frontend() {
    log_step "Building Frontend Locally"

    if [ "$SKIP_BUILD" = true ]; then
        log "Skipping build (--skip-build flag)"
        log_warning "Using existing build directory: $BUILD_DIR"
        return 0
    fi

    if [ "$DRY_RUN" = true ]; then
        log "DRY RUN: Would build frontend with 'npm run build'"
        return 0
    fi

    cd "$PROJECT_ROOT"

    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        log "node_modules not found, running npm install..."
        npm install --legacy-peer-deps
        log_success "Dependencies installed"
    fi

    # Build the frontend
    log "Running npm run build (this may take a few minutes)..."
    local start_time=$(date +%s)

    if npm run build; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log_success "Frontend built successfully in ${duration}s"

        if [ -d "$BUILD_DIR" ]; then
            local build_size=$(du -sh "$BUILD_DIR" | cut -f1)
            log "Build size: $build_size"
            log "Build location: $BUILD_DIR"
        fi
    else
        log_error "Frontend build failed!"
        exit 1
    fi
}

# ==============================================================================
# Deployment Functions
# ==============================================================================

deploy_frontend() {
    log_step "Deploying Frontend to Lightsail"

    if [ ! -d "$BUILD_DIR" ]; then
        log_error "Build directory not found: $BUILD_DIR"
        exit 1
    fi

    local remote_build_dir="$DEPLOY_REMOTE_PATH/build"

    log "Local build:  $BUILD_DIR"
    log "Remote path:  $remote_build_dir"

    if [ "$DRY_RUN" = true ]; then
        log "DRY RUN: Would deploy files to $DEPLOY_USER@$DEPLOY_HOST:$remote_build_dir"
        return 0
    fi

    # Create remote directory if it doesn't exist
    log "Ensuring remote directory exists..."
    ssh -i "$DEPLOY_KEY" -p "$DEPLOY_PORT" "$DEPLOY_USER@$DEPLOY_HOST" \
        "mkdir -p $DEPLOY_REMOTE_PATH"

    # Use rsync if available, otherwise fall back to scp
    if command -v rsync &> /dev/null; then
        log "Using rsync for fast incremental transfer..."

        # Sync the build directory
        if rsync -avz --delete \
            -e "ssh -i $DEPLOY_KEY -p $DEPLOY_PORT" \
            "$BUILD_DIR/" \
            "$DEPLOY_USER@$DEPLOY_HOST:$remote_build_dir/"; then
            log_success "Files transferred successfully (rsync)"
        else
            log_error "Rsync transfer failed"
            exit 1
        fi
    else
        log "Using scp for transfer..."

        # First, remove old build directory on remote
        ssh -i "$DEPLOY_KEY" -p "$DEPLOY_PORT" "$DEPLOY_USER@$DEPLOY_HOST" \
            "rm -rf $remote_build_dir"

        # Create remote build directory
        ssh -i "$DEPLOY_KEY" -p "$DEPLOY_PORT" "$DEPLOY_USER@$DEPLOY_HOST" \
            "mkdir -p $remote_build_dir"

        # Transfer files
        if scp -i "$DEPLOY_KEY" -P "$DEPLOY_PORT" -r \
            "$BUILD_DIR/"* \
            "$DEPLOY_USER@$DEPLOY_HOST:$remote_build_dir/"; then
            log_success "Files transferred successfully (scp)"
        else
            log_error "SCP transfer failed"
            exit 1
        fi
    fi

    # Verify deployment
    log "Verifying deployment..."
    local remote_file_count=$(ssh -i "$DEPLOY_KEY" -p "$DEPLOY_PORT" \
        "$DEPLOY_USER@$DEPLOY_HOST" \
        "find $remote_build_dir -type f | wc -l")

    log_success "Deployment complete: $remote_file_count files on remote server"
}

restart_backend() {
    log_step "Restarting Backend Server"

    if [ "$RESTART_BACKEND" = false ]; then
        log "Skipping backend restart (use --restart to enable)"
        return 0
    fi

    if [ "$DRY_RUN" = true ]; then
        log "DRY RUN: Would restart backend server"
        return 0
    fi

    log "Attempting to restart backend..."

    # Try multiple restart methods
    local restart_command=$(cat <<'EOF'
cd "$DEPLOY_REMOTE_PATH"

# Method 1: Try start_server.sh restart
if [ -f "./start_server.sh" ]; then
    echo "Using start_server.sh restart..."
    ./start_server.sh restart
    exit 0
fi

# Method 2: Try systemd
if command -v systemctl &> /dev/null; then
    if systemctl is-active --quiet openwebui; then
        echo "Using systemctl restart..."
        sudo systemctl restart openwebui
        exit 0
    fi
fi

# Method 3: Manual restart via kill and start
echo "Manual restart not implemented in this script"
exit 1
EOF
)

    if ssh -i "$DEPLOY_KEY" -p "$DEPLOY_PORT" "$DEPLOY_USER@$DEPLOY_HOST" \
        "DEPLOY_REMOTE_PATH='$DEPLOY_REMOTE_PATH'; bash -c '$restart_command'"; then
        log_success "Backend restarted successfully"
    else
        log_warning "Backend restart failed or not configured"
        log "You may need to restart manually"
    fi
}

# ==============================================================================
# Summary Functions
# ==============================================================================

print_summary() {
    log_step "Deployment Summary"

    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                   Deployment Complete! 🚀                     ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    if [ "$DRY_RUN" = true ]; then
        log_warning "DRY RUN - No actual changes were made"
        echo ""
    fi

    log_success "Frontend built locally"
    log_success "Files transferred to $DEPLOY_HOST"

    if [ "$RESTART_BACKEND" = true ]; then
        log_success "Backend restart attempted"
    fi

    echo ""
    echo -e "${CYAN}Next Steps:${NC}"
    echo ""
    echo "  1. Verify deployment:"
    echo -e "     ${YELLOW}ssh -i $DEPLOY_KEY $DEPLOY_USER@$DEPLOY_HOST${NC}"
    echo ""
    echo "  2. Check if backend is running:"
    echo -e "     ${YELLOW}cd $DEPLOY_REMOTE_PATH && ./health_check.sh${NC}"
    echo ""
    echo "  3. View backend logs:"
    echo -e "     ${YELLOW}tail -f $DEPLOY_REMOTE_PATH/logs/backend.log${NC}"
    echo "     OR"
    echo -e "     ${YELLOW}sudo journalctl -u openwebui -f${NC} (if using systemd)"
    echo ""
    echo "  4. Test the application in your browser"
    echo ""

    if [ "$RESTART_BACKEND" = false ]; then
        log_warning "Backend was not restarted. Restart manually if needed:"
        echo "  ssh to server and run: ./start_server.sh restart"
        echo ""
    fi
}

# ==============================================================================
# Main Execution
# ==============================================================================

main() {
    print_header

    # Parse arguments
    parse_args "$@"

    # Load config file
    load_config

    # Show configuration
    log "Project root: $PROJECT_ROOT"
    if [ "$DRY_RUN" = true ]; then
        log_warning "Running in DRY RUN mode - no changes will be made"
    fi
    echo ""

    # Run deployment steps
    check_dependencies
    validate_config
    test_ssh_connection
    build_frontend
    deploy_frontend
    restart_backend

    # Show summary
    print_summary
}

# Run main function
main "$@"

exit 0
