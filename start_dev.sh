#!/bin/bash

# ==============================================================================
# Fixxit.ai OpenWebUI Development Server Script
# ==============================================================================
# 
# A dedicated script for development workflow with hot reload, file watching,
# and development-optimized settings.
#
# Usage:
#   ./start_dev.sh start     - Start development servers with hot reload
#   ./start_dev.sh stop      - Stop all development servers
#   ./start_dev.sh restart   - Restart development servers
#   ./start_dev.sh status    - Check development server status
#   ./start_dev.sh logs      - Show combined development logs
#   ./start_dev.sh frontend  - Start only frontend (useful for UI development)
#   ./start_dev.sh backend   - Start only backend (useful for API development)
#
# ==============================================================================

set -e  # Exit on any error

# Configuration
PROJECT_ROOT="$(dirname "$(readlink -f "$0")")"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT"
LOGS_DIR="$PROJECT_ROOT/logs"
PID_FILE="$LOGS_DIR/dev-server.pid"
BACKEND_LOG="$LOGS_DIR/dev-backend.log"
FRONTEND_LOG="$LOGS_DIR/dev-frontend.log"
COMBINED_LOG="$LOGS_DIR/dev-combined.log"

# Development server configuration
BACKEND_PORT=8080
FRONTEND_PORT=5173
BACKEND_HOST="127.0.0.1"
FRONTEND_HOST="0.0.0.0"  # Allow external connections for development

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# ==============================================================================
# Utility Functions
# ==============================================================================

log() {
    echo -e "${BLUE}[DEV $(date +'%H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[DEV $(date +'%H:%M:%S')] ✓${NC} $1"
}

log_error() {
    echo -e "${RED}[DEV $(date +'%H:%M:%S')] ✗${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[DEV $(date +'%H:%M:%S')] ⚠${NC} $1"
}

log_dev() {
    echo -e "${MAGENTA}[DEV $(date +'%H:%M:%S')] 🚀${NC} $1"
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
setup_dev_directories() {
    mkdir -p "$LOGS_DIR"
    touch "$BACKEND_LOG" "$FRONTEND_LOG" "$COMBINED_LOG"
}

# ==============================================================================
# Development Backend Management
# ==============================================================================

start_dev_backend() {
    log_dev "Starting development backend server..."
    
    # Check if backend port is already in use
    if port_in_use $BACKEND_PORT; then
        local existing_pid=$(get_port_process $BACKEND_PORT)
        log_warning "Port $BACKEND_PORT is already in use by process $existing_pid"
        
        # Check if it's our process
        if [ -f "$PID_FILE" ] && grep -q "backend:$existing_pid" "$PID_FILE" 2>/dev/null; then
            log_warning "Development backend server is already running (PID: $existing_pid)"
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
        log_error "Backend virtual environment not found. Run './start_server.sh setup' first."
        return 1
    fi
    
    # Initialize database
    log "Initializing database..."
    if python3 init_database.py >/dev/null 2>&1; then
        log_success "Database initialized successfully"
    else
        log_warning "Database initialization had issues, but continuing..."
    fi
    
    # Set development environment variables
    export PYTHONPATH="$BACKEND_DIR:$PYTHONPATH"
    export DATA_DIR="$BACKEND_DIR/data"
    export DATABASE_URL="sqlite:///$BACKEND_DIR/data/webui.db"
    export WEBUI_SECRET_KEY="fixxit-development-secret-key"
    export ENV="development"
    export CORS_ALLOW_ORIGIN="*"
    export ENABLE_SIGNUP="true"
    
    # Development-specific settings
    export GLOBAL_LOG_LEVEL="DEBUG"
    export WEBUI_AUTH_TRUSTED_EMAIL_HEADER=""  # Disable for development
    
    # Start development backend server from project root
    cd "$PROJECT_ROOT"
    
    # Start with auto-reload for development
    log_dev "Starting backend with auto-reload on $BACKEND_HOST:$BACKEND_PORT..."
    log "Environment: development mode with debug logging"
    log "Database: $DATABASE_URL"
    nohup "$BACKEND_DIR/venv/bin/python" -m uvicorn open_webui.main:app \
        --host $BACKEND_HOST \
        --port $BACKEND_PORT \
        --reload \
        --reload-dir "$BACKEND_DIR/open_webui" \
        --log-level debug \
        > "$BACKEND_LOG" 2>&1 &
    local backend_pid=$!
    
    # Wait a moment and check if the process is still running
    sleep 3
    if ! kill -0 $backend_pid 2>/dev/null; then
        log_error "Development backend server failed to start. Check logs: $BACKEND_LOG"
        return 1
    fi
    
    # Record PID
    echo "backend:$backend_pid" >> "$PID_FILE"
    
    log_success "Development backend server started successfully (PID: $backend_pid)"
    log_dev "Backend auto-reload enabled for: $BACKEND_DIR/open_webui"
    return 0
}

# ==============================================================================
# Development Frontend Management  
# ==============================================================================

start_dev_frontend() {
    log_dev "Starting development frontend server..."
    
    # Check if frontend port is already in use
    if port_in_use $FRONTEND_PORT; then
        local existing_pid=$(get_port_process $FRONTEND_PORT)
        log_warning "Port $FRONTEND_PORT is already in use by process $existing_pid"
        
        # Check if it's our process
        if [ -f "$PID_FILE" ] && grep -q "frontend:$existing_pid" "$PID_FILE" 2>/dev/null; then
            log_warning "Development frontend server is already running (PID: $existing_pid)"
            return 0
        else
            log_error "Port $FRONTEND_PORT is occupied by another process. Please stop it first."
            return 1
        fi
    fi
    
    cd "$FRONTEND_DIR"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        log_error "node_modules not found. Run './start_server.sh setup' first."
        return 1
    fi
    
    # Start development frontend server with Vite
    log_dev "Starting Vite development server on $FRONTEND_HOST:$FRONTEND_PORT..."
    log_dev "Hot Module Replacement (HMR) enabled for instant UI updates"
    log_dev "File watching enabled for: src/, static/, *.config.*"
    
    # Use development command with additional dev settings
    nohup npm run dev -- --port $FRONTEND_PORT --host $FRONTEND_HOST > "$FRONTEND_LOG" 2>&1 &
    local frontend_pid=$!
    
    # Wait a moment and check if the process is still running
    sleep 3
    if ! kill -0 $frontend_pid 2>/dev/null; then
        log_error "Development frontend server failed to start. Check logs: $FRONTEND_LOG"
        return 1
    fi
    
    # Record PID
    echo "frontend:$frontend_pid" >> "$PID_FILE"
    
    log_success "Development frontend server started successfully (PID: $frontend_pid)"
    log_dev "Vite HMR ready - UI changes will appear instantly!"
    return 0
}

# ==============================================================================
# Server Control Functions
# ==============================================================================

start_dev_servers() {
    log_dev "Starting Fixxit.ai OpenWebUI development servers..."
    log "Development mode: Hot reload enabled for both frontend and backend"
    setup_dev_directories
    
    # Start backend first
    if start_dev_backend; then
        # Wait a moment for backend to fully initialize
        sleep 2
        
        # Start frontend
        if start_dev_frontend; then
            log_success "Both development servers started successfully!"
            echo ""
            log_dev "🎯 Development Environment Ready:"
            echo -e "   ${GREEN}Backend:${NC}  http://$BACKEND_HOST:$BACKEND_PORT (FastAPI with auto-reload)"
            echo -e "   ${GREEN}Frontend:${NC} http://$FRONTEND_HOST:$FRONTEND_PORT (Vite with HMR)"
            echo -e "   ${BLUE}Logs:${NC}     $LOGS_DIR"
            echo ""
            log_dev "💡 Pro Tips:"
            echo "   • Edit files in src/ for instant UI updates"
            echo "   • Edit backend files in backend/open_webui/ for API auto-reload"
            echo "   • Run './start_dev.sh logs' to watch all changes in real-time"
            echo "   • Use './start_dev.sh restart' to quickly restart both servers"
        else
            log_error "Frontend failed to start. Stopping backend..."
            stop_dev_backend
            return 1
        fi
    else
        log_error "Backend failed to start. Not starting frontend."
        return 1
    fi
}

stop_dev_backend() {
    if [ -f "$PID_FILE" ]; then
        local backend_pid=$(grep "^backend:" "$PID_FILE" 2>/dev/null | cut -d':' -f2)
        if [ -n "$backend_pid" ] && kill -0 "$backend_pid" 2>/dev/null; then
            log "Stopping development backend server (PID: $backend_pid)..."
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
            
            log_success "Development backend server stopped"
        fi
    fi
}

stop_dev_frontend() {
    if [ -f "$PID_FILE" ]; then
        local frontend_pid=$(grep "^frontend:" "$PID_FILE" 2>/dev/null | cut -d':' -f2)
        if [ -n "$frontend_pid" ] && kill -0 "$frontend_pid" 2>/dev/null; then
            log "Stopping development frontend server (PID: $frontend_pid)..."
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
            
            log_success "Development frontend server stopped"
        fi
    fi
}

stop_dev_servers() {
    log_dev "Stopping development servers..."
    
    stop_dev_frontend
    stop_dev_backend
    
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
    
    log_success "All development servers stopped"
}

restart_dev_servers() {
    log_dev "Restarting development servers..."
    stop_dev_servers
    sleep 2
    start_dev_servers
}

show_dev_status() {
    log_dev "Checking development server status..."
    
    local backend_running=false
    local frontend_running=false
    
    # Check backend
    if port_in_use $BACKEND_PORT; then
        local backend_pid=$(get_port_process $BACKEND_PORT)
        log_success "Development backend is running on port $BACKEND_PORT (PID: $backend_pid)"
        echo -e "   ${GREEN}URL:${NC} http://$BACKEND_HOST:$BACKEND_PORT"
        echo -e "   ${GREEN}Mode:${NC} Development with auto-reload"
        backend_running=true
    else
        log_error "Development backend is not running on port $BACKEND_PORT"
    fi
    
    echo ""
    
    # Check frontend  
    if port_in_use $FRONTEND_PORT; then
        local frontend_pid=$(get_port_process $FRONTEND_PORT)
        log_success "Development frontend is running on port $FRONTEND_PORT (PID: $frontend_pid)"
        echo -e "   ${GREEN}URL:${NC} http://$FRONTEND_HOST:$FRONTEND_PORT"
        echo -e "   ${GREEN}Mode:${NC} Vite development server with HMR"
        frontend_running=true
    else
        log_error "Development frontend is not running on port $FRONTEND_PORT"
    fi
    
    echo ""
    
    # Show PID file status
    if [ -f "$PID_FILE" ]; then
        log "Development PID file: $PID_FILE"
        cat "$PID_FILE" | while read line; do
            echo "   $line"
        done
    else
        log "No development PID file found"
    fi
    
    if [ "$backend_running" = true ] && [ "$frontend_running" = true ]; then
        echo ""
        log_dev "🎯 Development environment is fully operational!"
        log_dev "Make changes to your code and see them instantly reflected"
    fi
}

show_dev_logs() {
    log_dev "Showing development server logs (Ctrl+C to exit)..."
    
    # Create combined log if it doesn't exist
    touch "$COMBINED_LOG"
    
    # Start tailing logs in background with prefixes
    (tail -f "$BACKEND_LOG" 2>/dev/null | sed 's/^/[BACKEND] /' &) | \
    (tail -f "$FRONTEND_LOG" 2>/dev/null | sed 's/^/[FRONTEND] /' &) | \
    while read line; do
        echo "[$(date +'%H:%M:%S')] $line" | tee -a "$COMBINED_LOG"
    done
}

# ==============================================================================
# Main Script Logic
# ==============================================================================

case "${1:-}" in
    start)
        start_dev_servers
        ;;
    stop)
        stop_dev_servers
        ;;
    restart)
        restart_dev_servers
        ;;
    status)
        show_dev_status
        ;;
    logs)
        show_dev_logs
        ;;
    frontend)
        log_dev "Starting frontend development server only..."
        setup_dev_directories
        start_dev_frontend
        if [ $? -eq 0 ]; then
            log_dev "Frontend-only development mode ready!"
            echo -e "   ${GREEN}Frontend:${NC} http://$FRONTEND_HOST:$FRONTEND_PORT"
        fi
        ;;
    backend)
        log_dev "Starting backend development server only..."
        setup_dev_directories
        start_dev_backend
        if [ $? -eq 0 ]; then
            log_dev "Backend-only development mode ready!"
            echo -e "   ${GREEN}Backend:${NC} http://$BACKEND_HOST:$BACKEND_PORT"
        fi
        ;;
    *)
        echo "Fixxit.ai OpenWebUI Development Server Manager"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|frontend|backend}"
        echo ""
        echo "Commands:"
        echo "  start     - Start both development servers with hot reload"
        echo "  stop      - Stop all development servers"
        echo "  restart   - Restart both development servers"
        echo "  status    - Check development server status"
        echo "  logs      - Show combined development logs (real-time)"
        echo "  frontend  - Start only frontend (for UI development)"
        echo "  backend   - Start only backend (for API development)"
        echo ""
        echo "Development Features:"
        echo "  • Hot Module Replacement (HMR) for instant UI updates"
        echo "  • Backend auto-reload on code changes"
        echo "  • Debug logging enabled"
        echo "  • File watching for real-time development"
        echo ""
        echo "Server Configuration:"
        echo "  Backend:  $BACKEND_HOST:$BACKEND_PORT (FastAPI with uvicorn --reload)"
        echo "  Frontend: $FRONTEND_HOST:$FRONTEND_PORT (Vite development server)"
        echo "  Logs:     $LOGS_DIR"
        echo ""
        exit 1
        ;;
esac

exit 0