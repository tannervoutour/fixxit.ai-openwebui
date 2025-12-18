#!/bin/bash

# ==============================================================================
# Fixxit.ai OpenWebUI Server Management Script
# ==============================================================================
# 
# A comprehensive script to reliably start and stop the OpenWebUI development 
# servers (frontend and backend) with proper dependency checks, logging, 
# and error handling.
#
# Usage:
#   ./start_server.sh start    - Start both frontend and backend servers
#   ./start_server.sh stop     - Stop all running servers
#   ./start_server.sh restart  - Restart both servers
#   ./start_server.sh status   - Check server status
#   ./start_server.sh logs     - Show combined logs
#   ./start_server.sh setup    - Install dependencies and prepare environment
#
# ==============================================================================

set -e  # Exit on any error

# Configuration
PROJECT_ROOT="$(dirname "$(readlink -f "$0")")"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT"
LOGS_DIR="$PROJECT_ROOT/logs"
PID_FILE="$LOGS_DIR/server.pid"
BACKEND_LOG="$LOGS_DIR/backend.log"
FRONTEND_LOG="$LOGS_DIR/frontend.log"
COMBINED_LOG="$LOGS_DIR/combined.log"

# Server configuration
BACKEND_PORT=8080
FRONTEND_PORT=5173
BACKEND_HOST="127.0.0.1"
FRONTEND_HOST="localhost"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==============================================================================
# Utility Functions
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

# Check if a port is in use
port_in_use() {
    local port=$1
    netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "
}

# Find process using a port
get_port_process() {
    local port=$1
    lsof -ti:$port 2>/dev/null || netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1
}

# Create necessary directories
setup_directories() {
    mkdir -p "$LOGS_DIR"
    touch "$BACKEND_LOG" "$FRONTEND_LOG" "$COMBINED_LOG"
}

# Check system dependencies
check_dependencies() {
    log "Checking system dependencies..."
    
    # Check for Node.js
    if ! command -v node >/dev/null 2>&1; then
        log_error "Node.js is not installed. Please install Node.js 18+ first."
        exit 1
    fi
    
    local node_version=$(node --version | cut -d'v' -f2)
    log "Found Node.js version: $node_version"
    
    # Check for Python
    if ! command -v python3 >/dev/null 2>&1; then
        log_error "Python 3 is not installed. Please install Python 3.11+ first."
        exit 1
    fi
    
    local python_version=$(python3 --version | cut -d' ' -f2)
    log "Found Python version: $python_version"
    
    # Check for npm
    if ! command -v npm >/dev/null 2>&1; then
        log_error "npm is not installed. Please install npm first."
        exit 1
    fi
    
    log_success "All system dependencies are available"
}

# ==============================================================================
# Backend Management
# ==============================================================================

setup_backend() {
    log "Setting up backend environment..."
    
    cd "$BACKEND_DIR"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        log "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        log "Installing Python dependencies..."
        pip install -r requirements.txt
    else
        log_error "requirements.txt not found in backend directory"
        exit 1
    fi
    
    log_success "Backend environment setup complete"
}

start_backend() {
    log "Starting backend server..."
    
    # Check if backend port is already in use
    if port_in_use $BACKEND_PORT; then
        local existing_pid=$(get_port_process $BACKEND_PORT)
        log_warning "Port $BACKEND_PORT is already in use by process $existing_pid"
        
        # Check if it's our process
        if [ -f "$PID_FILE" ] && grep -q "backend:$existing_pid" "$PID_FILE" 2>/dev/null; then
            log_warning "Backend server is already running (PID: $existing_pid)"
            return 0
        else
            log_error "Port $BACKEND_PORT is occupied by another process. Please stop it first."
            return 1
        fi
    fi
    
    cd "$BACKEND_DIR"
    
    # Activate virtual environment
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        log_error "Backend virtual environment not found. Run setup first."
        return 1
    fi
    
    # Initialize database
    log "Initializing database..."
    if python3 init_database.py >/dev/null 2>&1; then
        log_success "Database initialized successfully"
    else
        log_warning "Database initialization had issues, but continuing..."
    fi
    
    # Set environment variables for proper database path resolution
    export PYTHONPATH="$BACKEND_DIR:$PYTHONPATH"
    export DATA_DIR="$BACKEND_DIR/data"
    export DATABASE_URL="sqlite:///$BACKEND_DIR/data/webui.db"
    export WEBUI_SECRET_KEY="fixxit-development-secret-key-$(date +%s)"
    export DATABASE_PASSWORD_ENCRYPTION_KEY="aEtZV05XcVpuTG03VUNUczc5dlMtalY4WEdleDZheHY0Z0NuZ1I1SnZtaz0="
    
    # Start backend server from project root to avoid module resolution issues
    cd "$PROJECT_ROOT"
    
    # Start backend server in background
    log "Starting backend on $BACKEND_HOST:$BACKEND_PORT..."
    log "Database: $DATABASE_URL"
    nohup "$BACKEND_DIR/venv/bin/python" -m uvicorn open_webui.main:app --host $BACKEND_HOST --port $BACKEND_PORT --reload > "$BACKEND_LOG" 2>&1 &
    local backend_pid=$!
    
    # Wait a moment and check if the process is still running
    sleep 3
    if ! kill -0 $backend_pid 2>/dev/null; then
        log_error "Backend server failed to start. Check logs: $BACKEND_LOG"
        return 1
    fi
    
    # Record PID
    echo "backend:$backend_pid" >> "$PID_FILE"
    
    log_success "Backend server started successfully (PID: $backend_pid)"
    return 0
}

# ==============================================================================
# Frontend Management
# ==============================================================================

setup_frontend() {
    log "Setting up frontend environment..."
    
    cd "$FRONTEND_DIR"
    
    # Install npm dependencies
    if [ -f "package.json" ]; then
        log "Installing npm dependencies..."
        npm install --legacy-peer-deps
    else
        log_error "package.json not found in frontend directory"
        exit 1
    fi
    
    log_success "Frontend environment setup complete"
}

start_frontend() {
    log "Starting frontend server..."
    
    # Check if frontend port is already in use
    if port_in_use $FRONTEND_PORT; then
        local existing_pid=$(get_port_process $FRONTEND_PORT)
        log_warning "Port $FRONTEND_PORT is already in use by process $existing_pid"
        
        # Check if it's our process
        if [ -f "$PID_FILE" ] && grep -q "frontend:$existing_pid" "$PID_FILE" 2>/dev/null; then
            log_warning "Frontend server is already running (PID: $existing_pid)"
            return 0
        else
            log_error "Port $FRONTEND_PORT is occupied by another process. Please stop it first."
            return 1
        fi
    fi
    
    cd "$FRONTEND_DIR"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        log_error "node_modules not found. Run setup first."
        return 1
    fi
    
    # Start frontend server in background
    log "Starting frontend on $FRONTEND_HOST:$FRONTEND_PORT..."
    nohup npm run dev > "$FRONTEND_LOG" 2>&1 &
    local frontend_pid=$!
    
    # Wait a moment and check if the process is still running
    sleep 3
    if ! kill -0 $frontend_pid 2>/dev/null; then
        log_error "Frontend server failed to start. Check logs: $FRONTEND_LOG"
        return 1
    fi
    
    # Record PID
    echo "frontend:$frontend_pid" >> "$PID_FILE"
    
    log_success "Frontend server started successfully (PID: $frontend_pid)"
    return 0
}

# ==============================================================================
# Server Control Functions
# ==============================================================================

start_servers() {
    log "Starting Fixxit.ai OpenWebUI servers..."
    setup_directories
    
    # Start backend first
    if start_backend; then
        # Wait a moment for backend to fully initialize
        sleep 2
        
        # Start frontend
        if start_frontend; then
            log_success "Both servers started successfully!"
            log "Backend: http://$BACKEND_HOST:$BACKEND_PORT"
            log "Frontend: http://$FRONTEND_HOST:$FRONTEND_PORT"
            log "Logs directory: $LOGS_DIR"
        else
            log_error "Frontend failed to start. Stopping backend..."
            stop_backend
            return 1
        fi
    else
        log_error "Backend failed to start. Not starting frontend."
        return 1
    fi
}

stop_backend() {
    if [ -f "$PID_FILE" ]; then
        local backend_pid=$(grep "^backend:" "$PID_FILE" 2>/dev/null | cut -d':' -f2)
        if [ -n "$backend_pid" ] && kill -0 "$backend_pid" 2>/dev/null; then
            log "Stopping backend server (PID: $backend_pid)..."
            kill -TERM "$backend_pid" 2>/dev/null || true
            
            # Wait for graceful shutdown
            local count=0
            while kill -0 "$backend_pid" 2>/dev/null && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # Force kill if still running
            if kill -0 "$backend_pid" 2>/dev/null; then
                log_warning "Backend didn't stop gracefully, force killing..."
                kill -9 "$backend_pid" 2>/dev/null || true
            fi
            
            log_success "Backend server stopped"
        fi
    fi
}

stop_frontend() {
    if [ -f "$PID_FILE" ]; then
        local frontend_pid=$(grep "^frontend:" "$PID_FILE" 2>/dev/null | cut -d':' -f2)
        if [ -n "$frontend_pid" ] && kill -0 "$frontend_pid" 2>/dev/null; then
            log "Stopping frontend server (PID: $frontend_pid)..."
            kill -TERM "$frontend_pid" 2>/dev/null || true
            
            # Wait for graceful shutdown
            local count=0
            while kill -0 "$frontend_pid" 2>/dev/null && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # Force kill if still running
            if kill -0 "$frontend_pid" 2>/dev/null; then
                log_warning "Frontend didn't stop gracefully, force killing..."
                kill -9 "$frontend_pid" 2>/dev/null || true
            fi
            
            log_success "Frontend server stopped"
        fi
    fi
}

stop_servers() {
    log "Stopping Fixxit.ai OpenWebUI servers..."
    
    stop_frontend
    stop_backend
    
    # Clean up PID file
    if [ -f "$PID_FILE" ]; then
        rm "$PID_FILE"
    fi
    
    # Also kill any remaining processes on our ports
    local backend_proc=$(get_port_process $BACKEND_PORT)
    local frontend_proc=$(get_port_process $FRONTEND_PORT)
    
    if [ -n "$backend_proc" ]; then
        log_warning "Killing remaining process on backend port $BACKEND_PORT (PID: $backend_proc)"
        kill -9 "$backend_proc" 2>/dev/null || true
    fi
    
    if [ -n "$frontend_proc" ]; then
        log_warning "Killing remaining process on frontend port $FRONTEND_PORT (PID: $frontend_proc)"
        kill -9 "$frontend_proc" 2>/dev/null || true
    fi
    
    log_success "All servers stopped"
}

restart_servers() {
    log "Restarting servers..."
    stop_servers
    sleep 2
    start_servers
}

show_status() {
    log "Checking server status..."
    
    local backend_running=false
    local frontend_running=false
    
    # Check backend
    if port_in_use $BACKEND_PORT; then
        local backend_pid=$(get_port_process $BACKEND_PORT)
        log_success "Backend server is running on port $BACKEND_PORT (PID: $backend_pid)"
        backend_running=true
    else
        log_error "Backend server is not running on port $BACKEND_PORT"
    fi
    
    # Check frontend  
    if port_in_use $FRONTEND_PORT; then
        local frontend_pid=$(get_port_process $FRONTEND_PORT)
        log_success "Frontend server is running on port $FRONTEND_PORT (PID: $frontend_pid)"
        frontend_running=true
    else
        log_error "Frontend server is not running on port $FRONTEND_PORT"
    fi
    
    # Show URLs if running
    if [ "$backend_running" = true ]; then
        log "Backend URL: http://$BACKEND_HOST:$BACKEND_PORT"
    fi
    
    if [ "$frontend_running" = true ]; then
        log "Frontend URL: http://$FRONTEND_HOST:$FRONTEND_PORT"
    fi
    
    # Show PID file status
    if [ -f "$PID_FILE" ]; then
        log "PID file exists: $PID_FILE"
        cat "$PID_FILE"
    else
        log "No PID file found"
    fi
}

show_logs() {
    log "Showing combined server logs (Ctrl+C to exit)..."
    
    # Create combined log if it doesn't exist
    touch "$COMBINED_LOG"
    
    # Start tailing logs in background
    tail -f "$BACKEND_LOG" "$FRONTEND_LOG" 2>/dev/null | while read line; do
        echo "[$(date +'%H:%M:%S')] $line" | tee -a "$COMBINED_LOG"
    done
}

setup_environment() {
    log "Setting up complete development environment..."
    
    check_dependencies
    setup_directories
    setup_backend
    setup_frontend
    
    log_success "Environment setup complete! You can now start the servers with './start_server.sh start'"
}

# ==============================================================================
# Main Script Logic
# ==============================================================================

case "${1:-}" in
    start)
        start_servers
        ;;
    stop)
        stop_servers
        ;;
    restart)
        restart_servers
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    setup)
        setup_environment
        ;;
    *)
        echo "Fixxit.ai OpenWebUI Server Management"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|setup}"
        echo ""
        echo "Commands:"
        echo "  start    - Start both frontend and backend servers"
        echo "  stop     - Stop all running servers"
        echo "  restart  - Restart both servers"
        echo "  status   - Check server status"
        echo "  logs     - Show combined logs (real-time)"
        echo "  setup    - Install dependencies and prepare environment"
        echo ""
        echo "Configuration:"
        echo "  Backend:  $BACKEND_HOST:$BACKEND_PORT"
        echo "  Frontend: $FRONTEND_HOST:$FRONTEND_PORT"
        echo "  Logs:     $LOGS_DIR"
        echo ""
        exit 1
        ;;
esac

exit 0