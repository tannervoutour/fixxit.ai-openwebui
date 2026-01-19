#!/bin/bash

# ==============================================================================
# Full Deployment Script - Git + Frontend Build + Server Sync
# ==============================================================================
#
# This script handles the complete deployment workflow:
#   1. Commits and pushes changes to GitHub
#   2. Builds frontend locally
#   3. Syncs server with GitHub (pulls backend changes)
#   4. Deploys built frontend to server
#   5. Restarts backend
#
# Usage:
#   ./deploy-full.sh [options]
#
# Options:
#   --skip-git       Skip git commit/push
#   --skip-build     Skip frontend build (use existing)
#   --skip-sync      Skip server git pull
#   --no-restart     Don't restart backend after deployment
#   --message "msg"  Custom git commit message
#   --dry-run        Show what would be done
#   --help           Show this help
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

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$PROJECT_ROOT/.deploy-config"

# Default options
SKIP_GIT=false
SKIP_BUILD=false
SKIP_SYNC=false
NO_RESTART=false
DRY_RUN=false
COMMIT_MESSAGE=""

# ==============================================================================
# Utility Functions
# ==============================================================================

print_header() {
    echo ""
    echo -e "${MAGENTA}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║                                                                ║${NC}"
    echo -e "${MAGENTA}║            Full Deployment Workflow                           ║${NC}"
    echo -e "${MAGENTA}║        Git → Build → Sync → Deploy → Restart                 ║${NC}"
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
    echo -e "${CYAN} Step: $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

show_help() {
    head -n 25 "$0" | tail -n +3 | sed 's/^# //' | sed 's/^#//'
    exit 0
}

# ==============================================================================
# Parse Arguments
# ==============================================================================

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-git)
                SKIP_GIT=true
                shift
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --skip-sync)
                SKIP_SYNC=true
                shift
                ;;
            --no-restart)
                NO_RESTART=true
                shift
                ;;
            --message|-m)
                COMMIT_MESSAGE="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --help|-h)
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
# Load Configuration
# ==============================================================================

load_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        log_error "Deployment config not found: $CONFIG_FILE"
        log "Run: cp .deploy-config.example .deploy-config"
        exit 1
    fi

    source "$CONFIG_FILE"

    # Validate required config
    if [ -z "$DEPLOY_HOST" ] || [ -z "$DEPLOY_USER" ] || [ -z "$DEPLOY_KEY" ]; then
        log_error "Invalid deployment configuration"
        exit 1
    fi
}

# ==============================================================================
# Git Operations
# ==============================================================================

git_commit_and_push() {
    log_step "1. Git Commit & Push"

    if [ "$SKIP_GIT" = true ]; then
        log "Skipping git operations (--skip-git)"
        return 0
    fi

    cd "$PROJECT_ROOT"

    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "Not a git repository"
        exit 1
    fi

    # Check for uncommitted changes
    if git diff-index --quiet HEAD --; then
        log "No changes to commit"
    else
        # Show changes
        log "Changes to be committed:"
        git status --short | head -20

        if [ -n "$(git status --short | tail -n +21)" ]; then
            echo "... and more"
        fi
        echo ""

        # Get commit message
        if [ -z "$COMMIT_MESSAGE" ]; then
            echo -e "${YELLOW}Enter commit message (or press Ctrl+C to cancel):${NC}"
            read -r COMMIT_MESSAGE

            if [ -z "$COMMIT_MESSAGE" ]; then
                log_error "Commit message cannot be empty"
                exit 1
            fi
        fi

        if [ "$DRY_RUN" = true ]; then
            log "DRY RUN: Would commit with message: $COMMIT_MESSAGE"
        else
            # Commit changes
            log "Committing changes..."
            git add .
            git commit -m "$COMMIT_MESSAGE"
            log_success "Changes committed"
        fi
    fi

    # Push to remote
    local current_branch=$(git branch --show-current)
    log "Current branch: $current_branch"

    if [ "$DRY_RUN" = true ]; then
        log "DRY RUN: Would push to origin $current_branch"
    else
        log "Pushing to GitHub..."
        if git push origin "$current_branch"; then
            log_success "Pushed to GitHub successfully"
        else
            log_error "Failed to push to GitHub"
            exit 1
        fi
    fi
}

# ==============================================================================
# Build Frontend
# ==============================================================================

build_frontend() {
    log_step "2. Build Frontend Locally"

    if [ "$SKIP_BUILD" = true ]; then
        log "Skipping frontend build (--skip-build)"

        if [ ! -d "$PROJECT_ROOT/build" ]; then
            log_error "Build directory not found and build skipped"
            exit 1
        fi

        return 0
    fi

    cd "$PROJECT_ROOT"

    if [ "$DRY_RUN" = true ]; then
        log "DRY RUN: Would run npm run build"
        return 0
    fi

    log "Building frontend (this may take 2-3 minutes)..."
    local start_time=$(date +%s)

    # Increase Node.js memory limit for build
    export NODE_OPTIONS="--max-old-space-size=8192"

    if npm run build > /tmp/build.log 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))

        local build_size=$(du -sh build | cut -f1)
        log_success "Frontend built in ${duration}s (Size: $build_size)"
    else
        log_error "Frontend build failed!"
        log "Check build log: /tmp/build.log"
        tail -30 /tmp/build.log
        exit 1
    fi
}

# ==============================================================================
# Sync Server with GitHub
# ==============================================================================

sync_server_with_github() {
    log_step "3. Sync Server with GitHub"

    if [ "$SKIP_SYNC" = true ]; then
        log "Skipping server sync (--skip-sync)"
        return 0
    fi

    if [ "$DRY_RUN" = true ]; then
        log "DRY RUN: Would sync server with GitHub"
        return 0
    fi

    log "Pulling latest changes from GitHub on server..."

    local sync_command=$(cat <<'EOF'
cd "$REMOTE_PATH"
echo "Current branch: $(git branch --show-current)"
echo "Pulling changes..."
git fetch origin
git pull origin $(git branch --show-current)
echo "Server synced with GitHub"
EOF
)

    if ssh -i "$DEPLOY_KEY" -p "$DEPLOY_PORT" "$DEPLOY_USER@$DEPLOY_HOST" \
        "REMOTE_PATH='$DEPLOY_REMOTE_PATH'; bash -c '$sync_command'"; then
        log_success "Server synced with GitHub"
    else
        log_error "Failed to sync server with GitHub"
        exit 1
    fi
}

# ==============================================================================
# Deploy Frontend
# ==============================================================================

deploy_frontend() {
    log_step "4. Deploy Frontend to Server"

    if [ "$DRY_RUN" = true ]; then
        log "DRY RUN: Would deploy frontend to server"
        return 0
    fi

    log "Deploying frontend using rsync..."

    local deploy_script="$PROJECT_ROOT/deploy-to-lightsail.sh"

    if [ ! -f "$deploy_script" ]; then
        log_error "Deploy script not found: $deploy_script"
        exit 1
    fi

    local deploy_flags="--skip-build"
    if [ "$NO_RESTART" = false ]; then
        deploy_flags="$deploy_flags --restart"
    fi

    if "$deploy_script" $deploy_flags; then
        log_success "Frontend deployed successfully"
    else
        log_error "Frontend deployment failed"
        exit 1
    fi
}

# ==============================================================================
# Final Summary
# ==============================================================================

print_summary() {
    log_step "Deployment Complete!"

    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                  Deployment Successful! 🎉                    ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    if [ "$DRY_RUN" = true ]; then
        log_warning "DRY RUN - No actual changes were made"
        echo ""
    fi

    log_success "Git changes pushed to GitHub"
    log_success "Frontend built locally"
    log_success "Server synced with GitHub"
    log_success "Frontend deployed to server"

    if [ "$NO_RESTART" = false ]; then
        log_success "Backend restarted"
    fi

    echo ""
    echo -e "${CYAN}Access your application:${NC}"
    echo -e "  ${YELLOW}http://$DEPLOY_HOST:8080${NC}"
    echo ""

    echo -e "${CYAN}Quick checks:${NC}"
    echo -e "  ${YELLOW}ssh -i $DEPLOY_KEY $DEPLOY_USER@$DEPLOY_HOST${NC}"
    echo -e "  ${YELLOW}cd $DEPLOY_REMOTE_PATH && ./start_server.sh status${NC}"
    echo ""
}

# ==============================================================================
# Main Execution
# ==============================================================================

main() {
    print_header

    # Parse arguments
    parse_args "$@"

    # Show configuration
    log "Project: $PROJECT_ROOT"
    if [ "$DRY_RUN" = true ]; then
        log_warning "Running in DRY RUN mode"
    fi
    echo ""

    # Load deployment config
    load_config

    # Execute deployment workflow
    git_commit_and_push
    build_frontend
    sync_server_with_github
    deploy_frontend

    # Show summary
    print_summary
}

# Run main function
main "$@"

exit 0
