#!/bin/bash

# ==============================================================================
# Fixxit.ai OpenWebUI - Production Setup Script
# ==============================================================================
#
# This script automates the production deployment setup process including:
# - System dependency verification
# - Python environment setup
# - Node.js environment setup
# - Frontend build
# - Environment configuration
# - Security setup
# - Optional systemd service installation
#
# Usage:
#   ./setup_production.sh [--auto] [--no-systemd] [--help]
#
# Options:
#   --auto        Run in non-interactive mode (uses defaults)
#   --no-systemd  Skip systemd service installation
#   --help        Show this help message
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
BACKEND_DIR="$PROJECT_ROOT/backend"
LOGS_DIR="$PROJECT_ROOT/logs"
DATA_DIR="$BACKEND_DIR/data"
AUTO_MODE=false
SKIP_SYSTEMD=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --auto)
            AUTO_MODE=true
            shift
            ;;
        --no-systemd)
            SKIP_SYSTEMD=true
            shift
            ;;
        --help)
            head -n 20 "$0" | tail -n +3 | sed 's/^# //' | sed 's/^#//'
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# ==============================================================================
# Utility Functions
# ==============================================================================

print_header() {
    echo ""
    echo -e "${MAGENTA}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║                                                                ║${NC}"
    echo -e "${MAGENTA}║          Fixxit.ai OpenWebUI Production Setup                ║${NC}"
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

prompt() {
    if [ "$AUTO_MODE" = true ]; then
        return 0
    fi

    local message="$1"
    local default="${2:-y}"

    echo -ne "${YELLOW}[?]${NC} $message "
    if [ "$default" = "y" ]; then
        echo -ne "[Y/n]: "
    else
        echo -ne "[y/N]: "
    fi

    read -r response
    response=${response:-$default}

    if [[ "$response" =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

# ==============================================================================
# System Checks
# ==============================================================================

check_os() {
    log_step "Step 1: Checking Operating System"

    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        log_success "Linux detected"

        if [ -f /etc/os-release ]; then
            . /etc/os-release
            log "Distribution: $NAME $VERSION"
        fi
    else
        log_warning "This script is designed for Linux. Your OS: $OSTYPE"
        if ! prompt "Continue anyway?"; then
            exit 1
        fi
    fi
}

check_dependencies() {
    log_step "Step 2: Checking System Dependencies"

    local missing_deps=()

    # Check Python
    if command -v python3 >/dev/null 2>&1; then
        local python_version=$(python3 --version | cut -d' ' -f2)
        local python_major=$(echo $python_version | cut -d. -f1)
        local python_minor=$(echo $python_version | cut -d. -f2)

        if [ "$python_major" -eq 3 ] && [ "$python_minor" -ge 11 ]; then
            log_success "Python $python_version found"
        else
            log_error "Python 3.11+ required, found $python_version"
            missing_deps+=("python3.11+")
        fi
    else
        log_error "Python 3 not found"
        missing_deps+=("python3")
    fi

    # Check Node.js
    if command -v node >/dev/null 2>&1; then
        local node_version=$(node --version | cut -d'v' -f2)
        local node_major=$(echo $node_version | cut -d. -f1)

        if [ "$node_major" -ge 18 ]; then
            log_success "Node.js $node_version found"
        else
            log_error "Node.js 18+ required, found $node_version"
            missing_deps+=("node18+")
        fi
    else
        log_error "Node.js not found"
        missing_deps+=("nodejs")
    fi

    # Check npm
    if command -v npm >/dev/null 2>&1; then
        local npm_version=$(npm --version)
        log_success "npm $npm_version found"
    else
        log_error "npm not found"
        missing_deps+=("npm")
    fi

    # Check git
    if command -v git >/dev/null 2>&1; then
        local git_version=$(git --version | cut -d' ' -f3)
        log_success "Git $git_version found"
    else
        log_error "Git not found"
        missing_deps+=("git")
    fi

    # Check for build essentials
    if command -v gcc >/dev/null 2>&1; then
        log_success "Build tools found"
    else
        log_warning "Build tools not found (may be needed for some Python packages)"
    fi

    # Check for PostgreSQL client libraries
    if ldconfig -p | grep -q libpq; then
        log_success "PostgreSQL client libraries found"
    else
        log_warning "PostgreSQL client libraries not found (needed for Supabase)"
        log "Install with: sudo apt install libpq-dev"
    fi

    # Report missing dependencies
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log ""
        log "Install them with:"
        log "  sudo apt update"
        log "  sudo apt install python3 python3-pip python3-venv nodejs npm git build-essential libpq-dev"
        exit 1
    fi
}

# ==============================================================================
# Setup Functions
# ==============================================================================

setup_directories() {
    log_step "Step 3: Creating Directories"

    mkdir -p "$LOGS_DIR"
    mkdir -p "$DATA_DIR"

    log_success "Created logs directory: $LOGS_DIR"
    log_success "Created data directory: $DATA_DIR"
}

setup_backend() {
    log_step "Step 4: Setting Up Backend Environment"

    cd "$BACKEND_DIR"

    # Create virtual environment
    if [ ! -d "venv" ]; then
        log "Creating Python virtual environment..."
        python3 -m venv venv
        log_success "Virtual environment created"
    else
        log_warning "Virtual environment already exists, skipping creation"
    fi

    # Activate virtual environment
    log "Activating virtual environment..."
    source venv/bin/activate

    # Upgrade pip
    log "Upgrading pip..."
    pip install --upgrade pip --quiet

    # Install requirements
    if [ -f "requirements.txt" ]; then
        log "Installing Python dependencies (this may take several minutes)..."
        pip install -r requirements.txt --quiet
        log_success "Python dependencies installed"
    else
        log_error "requirements.txt not found!"
        exit 1
    fi

    cd "$PROJECT_ROOT"
}

setup_frontend() {
    log_step "Step 5: Setting Up Frontend Environment"

    cd "$PROJECT_ROOT"

    # Install npm dependencies
    if [ -f "package.json" ]; then
        log "Installing npm dependencies (this may take several minutes)..."
        npm install --legacy-peer-deps --quiet
        log_success "npm dependencies installed"
    else
        log_error "package.json not found!"
        exit 1
    fi

    # Build frontend
    log "Building production frontend (this may take several minutes)..."
    if npm run build; then
        log_success "Frontend built successfully"

        if [ -d "build" ]; then
            log "Build output: $(du -sh build | cut -f1)"
        fi
    else
        log_error "Frontend build failed!"
        exit 1
    fi
}

generate_encryption_key() {
    # Generate Fernet key for database password encryption
    # Fernet.generate_key() already returns a base64-encoded key
    python3 -c "from cryptography.fernet import Fernet; key = Fernet.generate_key(); print(key.decode())"
}

setup_environment() {
    log_step "Step 7: Configuring Environment"

    local env_file="$PROJECT_ROOT/.env"

    if [ -f "$env_file" ] && [ "$AUTO_MODE" = false ]; then
        log_warning ".env file already exists"
        if ! prompt "Overwrite existing .env file?" "n"; then
            log "Keeping existing .env file"
            return
        fi
    fi

    # Generate encryption key
    log "Generating DATABASE_PASSWORD_ENCRYPTION_KEY..."
    local encryption_key=$(generate_encryption_key)

    # Create .env file from template
    if [ -f "$PROJECT_ROOT/.env.production.template" ]; then
        cp "$PROJECT_ROOT/.env.production.template" "$env_file"

        # Replace placeholder with actual encryption key
        if grep -q "REPLACE_WITH_GENERATED_KEY" "$env_file"; then
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s|REPLACE_WITH_GENERATED_KEY|$encryption_key|" "$env_file"
            else
                sed -i "s|REPLACE_WITH_GENERATED_KEY|$encryption_key|" "$env_file"
            fi
        fi

        log_success ".env file created from template"
    else
        log_error ".env.production.template not found!"
        log "Creating basic .env file..."

        cat > "$env_file" << EOF
# Fixxit.ai OpenWebUI Production Configuration
# Generated on $(date)

# CRITICAL: Database Password Encryption Key
DATABASE_PASSWORD_ENCRYPTION_KEY="$encryption_key"

# Server Configuration
HOST="0.0.0.0"
PORT="8080"

# Environment
ENV="production"
DEBUG_MODE="false"

# Add your OpenAI API key here
OPENAI_API_KEY=""

# Add your domain here
WEBUI_URL="http://localhost:8080"
EOF
    fi

    # Set secure permissions
    chmod 600 "$env_file"
    log_success "Set secure permissions on .env (600)"

    echo ""
    log_warning "IMPORTANT: Generated encryption key has been added to .env"
    log_warning "You MUST also configure:"
    log "  1. OPENAI_API_KEY (for AI-enhanced logs)"
    log "  2. WEBUI_URL (your domain/IP)"
    log "  3. Other optional settings as needed"
    echo ""

    if [ "$AUTO_MODE" = false ]; then
        prompt "Open .env file for editing now?" && ${EDITOR:-nano} "$env_file"
    fi
}

setup_systemd() {
    log_step "Step 8: Setting Up Systemd Service (Optional)"

    if [ "$SKIP_SYSTEMD" = true ]; then
        log "Skipping systemd setup (--no-systemd flag)"
        return
    fi

    if [ "$AUTO_MODE" = false ]; then
        if ! prompt "Install systemd service for auto-start?" "y"; then
            log "Skipping systemd setup"
            return
        fi
    fi

    # Check if running with sudo/root
    if [ "$EUID" -ne 0 ]; then
        log_warning "Systemd service installation requires root privileges"
        log "Run the following command manually:"
        echo ""
        cat << 'EOF'
sudo bash -c 'cat > /etc/systemd/system/openwebui.service << EOSERVICE
[Unit]
Description=Fixxit.ai OpenWebUI Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD/backend
Environment="PATH=$PWD/backend/venv/bin"
EnvironmentFile=$PWD/.env
ExecStart=$PWD/backend/venv/bin/python -m uvicorn open_webui.main:app --host 0.0.0.0 --port 8080 --workers 4
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOSERVICE

systemctl daemon-reload
systemctl enable openwebui
'
EOF
        return
    fi

    # Create systemd service file
    local service_file="/etc/systemd/system/openwebui.service"
    local current_user="${SUDO_USER:-$USER}"

    cat > "$service_file" << EOF
[Unit]
Description=Fixxit.ai OpenWebUI Server
After=network.target

[Service]
Type=simple
User=$current_user
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$BACKEND_DIR/venv/bin"
EnvironmentFile=$PROJECT_ROOT/.env
ExecStart=$BACKEND_DIR/venv/bin/python -m uvicorn open_webui.main:app --host 0.0.0.0 --port 8080 --workers 4
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable openwebui

    log_success "Systemd service installed and enabled"
    log "Start with: sudo systemctl start openwebui"
    log "View logs with: sudo journalctl -u openwebui -f"
}

# ==============================================================================
# Final Steps
# ==============================================================================

print_summary() {
    log_step "Setup Complete!"

    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    Setup Successful! 🎉                       ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    log_success "Backend environment configured"
    log_success "Frontend built successfully"
    log_success "Environment file created"
    log_success "Encryption key generated"

    echo ""
    echo -e "${CYAN}Next Steps:${NC}"
    echo ""
    echo "  1. Review and update your .env file:"
    echo -e "     ${YELLOW}nano .env${NC}"
    echo ""
    echo "  2. Start the server:"
    echo -e "     ${YELLOW}./start_server.sh start${NC}"
    echo "     OR"
    echo -e "     ${YELLOW}sudo systemctl start openwebui${NC} (if systemd installed)"
    echo ""
    echo "  3. Verify deployment:"
    echo -e "     ${YELLOW}./health_check.sh${NC}"
    echo ""
    echo "  4. Access the application:"
    echo -e "     ${YELLOW}http://localhost:8080${NC}"
    echo ""
    echo "  5. Configure Supabase for logs:"
    echo "     - Login as admin"
    echo "     - Go to Admin → Users → Groups"
    echo "     - Configure database connections"
    echo ""

    echo -e "${CYAN}Documentation:${NC}"
    echo "  - Production Guide: PRODUCTION_DEPLOYMENT.md"
    echo "  - Quick Start: QUICKSTART.md"
    echo "  - Health Checks: ./health_check.sh"
    echo ""

    log_warning "IMPORTANT: Make sure to configure your .env file before starting!"
}

# ==============================================================================
# Main Execution
# ==============================================================================

main() {
    print_header

    log "Running in ${AUTO_MODE:+AUTO}${AUTO_MODE:-INTERACTIVE} mode"
    log "Project root: $PROJECT_ROOT"
    echo ""

    # Run setup steps
    check_os
    check_dependencies
    setup_directories
    setup_backend
    setup_frontend
    setup_environment
    setup_systemd

    # Print summary
    print_summary
}

# Run main function
main "$@"

exit 0
