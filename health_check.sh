#!/bin/bash

# ==============================================================================
# Fixxit.ai OpenWebUI - Health Check Script
# ==============================================================================
#
# This script performs comprehensive health checks on the OpenWebUI deployment
# including server status, API endpoints, database connectivity, and more.
#
# Usage:
#   ./health_check.sh [--silent] [--json] [--url=http://localhost:8080]
#
# Options:
#   --silent  Only output errors (exit code 0 = healthy, 1 = unhealthy)
#   --json    Output results in JSON format
#   --url     Custom server URL (default: http://localhost:8080)
#
# Exit Codes:
#   0 - All checks passed
#   1 - One or more checks failed
#
# ==============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SERVER_URL="${SERVER_URL:-http://localhost:8080}"
SILENT=false
JSON_OUTPUT=false
CHECKS_PASSED=0
CHECKS_FAILED=0
RESULTS=()

# Parse arguments
for arg in "$@"; do
    case $arg in
        --silent)
            SILENT=true
            ;;
        --json)
            JSON_OUTPUT=true
            ;;
        --url=*)
            SERVER_URL="${arg#*=}"
            ;;
        --help)
            head -n 20 "$0" | tail -n +3 | sed 's/^# //' | sed 's/^#//'
            exit 0
            ;;
    esac
done

# ==============================================================================
# Utility Functions
# ==============================================================================

log() {
    if [ "$SILENT" = false ] && [ "$JSON_OUTPUT" = false ]; then
        echo -e "${BLUE}[INFO]${NC} $1"
    fi
}

log_success() {
    if [ "$SILENT" = false ] && [ "$JSON_OUTPUT" = false ]; then
        echo -e "${GREEN}[✓]${NC} $1"
    fi
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
    RESULTS+=("PASS: $1")
}

log_error() {
    if [ "$JSON_OUTPUT" = false ]; then
        echo -e "${RED}[✗]${NC} $1" >&2
    fi
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
    RESULTS+=("FAIL: $1")
}

log_warning() {
    if [ "$SILENT" = false ] && [ "$JSON_OUTPUT" = false ]; then
        echo -e "${YELLOW}[⚠]${NC} $1"
    fi
}

log_section() {
    if [ "$SILENT" = false ] && [ "$JSON_OUTPUT" = false ]; then
        echo ""
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${BLUE} $1${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
    fi
}

# ==============================================================================
# Health Check Functions
# ==============================================================================

check_server_running() {
    log_section "Server Status"

    # Check if server is responding
    if curl -f -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$SERVER_URL" > /dev/null 2>&1; then
        log_success "Server is responding at $SERVER_URL"
        return 0
    else
        log_error "Server is NOT responding at $SERVER_URL"
        return 1
    fi
}

check_health_endpoint() {
    log_section "Health Endpoint"

    local response=$(curl -s --connect-timeout 5 "$SERVER_URL/health" 2>/dev/null)

    if echo "$response" | grep -q "ok\|healthy"; then
        log_success "Health endpoint returned: $response"
        return 0
    else
        log_error "Health endpoint check failed"
        return 1
    fi
}

check_api_endpoints() {
    log_section "API Endpoints"

    # Check if API docs are accessible
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$SERVER_URL/docs" 2>/dev/null)

    if [ "$status_code" = "200" ]; then
        log_success "API documentation accessible"
    else
        log_warning "API documentation returned status $status_code"
    fi

    # Check auth endpoint
    status_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$SERVER_URL/api/v1/auths/signin" 2>/dev/null)

    if [ "$status_code" = "422" ] || [ "$status_code" = "200" ]; then
        log_success "Auth endpoint is responding"
    else
        log_error "Auth endpoint returned unexpected status: $status_code"
    fi
}

check_database() {
    log_section "Database"

    local project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local db_file="$project_root/backend/data/webui.db"

    if [ -f "$db_file" ]; then
        log_success "Database file exists: $db_file"

        # Check if database is readable
        if [ -r "$db_file" ]; then
            log_success "Database file is readable"

            # Check database size
            local db_size=$(du -h "$db_file" | cut -f1)
            log "Database size: $db_size"
        else
            log_error "Database file is not readable"
        fi
    else
        log_warning "Database file not found (may be using different location)"
    fi
}

check_encryption_key() {
    log_section "Encryption Key"

    local project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    if [ -f "$project_root/.env" ]; then
        if grep -q "DATABASE_PASSWORD_ENCRYPTION_KEY" "$project_root/.env"; then
            local key_value=$(grep "DATABASE_PASSWORD_ENCRYPTION_KEY" "$project_root/.env" | cut -d'=' -f2 | tr -d '"' | tr -d ' ')

            if [ ! -z "$key_value" ] && [ "$key_value" != "REPLACE_WITH_GENERATED_KEY" ]; then
                log_success "Encryption key is configured"
            else
                log_error "Encryption key is not properly configured"
            fi
        else
            log_error "Encryption key not found in .env"
        fi
    else
        log_warning ".env file not found"
    fi
}

check_python_environment() {
    log_section "Python Environment"

    local project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local venv_path="$project_root/backend/venv"

    if [ -d "$venv_path" ]; then
        log_success "Virtual environment exists"

        # Check if venv has required packages
        if [ -f "$venv_path/bin/python" ]; then
            local python_version=$("$venv_path/bin/python" --version 2>&1 | cut -d' ' -f2)
            log "Python version: $python_version"

            # Check for key packages
            if "$venv_path/bin/python" -c "import fastapi" 2>/dev/null; then
                log_success "FastAPI installed"
            else
                log_error "FastAPI not installed"
            fi

            if "$venv_path/bin/python" -c "import asyncpg" 2>/dev/null; then
                log_success "asyncpg installed (Supabase support)"
            else
                log_warning "asyncpg not installed (needed for Supabase)"
            fi
        fi
    else
        log_error "Virtual environment not found"
    fi
}

check_frontend_build() {
    log_section "Frontend Build"

    local project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local build_dir="$project_root/build"

    if [ -d "$build_dir" ]; then
        log_success "Frontend build directory exists"

        # Check if build has content
        local file_count=$(find "$build_dir" -type f | wc -l)
        if [ "$file_count" -gt 0 ]; then
            log_success "Frontend build contains $file_count files"

            # Check build size
            local build_size=$(du -sh "$build_dir" 2>/dev/null | cut -f1)
            log "Build size: $build_size"
        else
            log_error "Frontend build directory is empty"
        fi
    else
        log_warning "Frontend build not found (may be using different location)"
    fi
}

check_logs_directory() {
    log_section "Logs"

    local project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local logs_dir="$project_root/logs"

    if [ -d "$logs_dir" ]; then
        log_success "Logs directory exists"

        # Check if logs are being written
        if [ "$(find "$logs_dir" -type f -name "*.log" -mtime -1 | wc -l)" -gt 0 ]; then
            log_success "Recent log files found"
        else
            log_warning "No recent log files (server may not be logging)"
        fi

        # Check log sizes
        for log_file in "$logs_dir"/*.log; do
            if [ -f "$log_file" ]; then
                local log_size=$(du -h "$log_file" 2>/dev/null | cut -f1)
                log "$(basename "$log_file"): $log_size"
            fi
        done
    else
        log_warning "Logs directory not found"
    fi
}

check_disk_space() {
    log_section "Disk Space"

    local project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local disk_usage=$(df -h "$project_root" | tail -1 | awk '{print $5}' | sed 's/%//')

    if [ "$disk_usage" -lt 80 ]; then
        log_success "Disk usage: ${disk_usage}% (healthy)"
    elif [ "$disk_usage" -lt 90 ]; then
        log_warning "Disk usage: ${disk_usage}% (getting high)"
    else
        log_error "Disk usage: ${disk_usage}% (critical!)"
    fi
}

check_memory() {
    log_section "Memory"

    if command -v free >/dev/null 2>&1; then
        local mem_usage=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')
        log "Memory usage: ${mem_usage}%"

        if [ "$(echo "$mem_usage < 80" | bc)" -eq 1 ]; then
            log_success "Memory usage is healthy"
        elif [ "$(echo "$mem_usage < 90" | bc)" -eq 1 ]; then
            log_warning "Memory usage is getting high"
        else
            log_error "Memory usage is critical!"
        fi
    else
        log_warning "Memory check not available (free command not found)"
    fi
}

# ==============================================================================
# Output Functions
# ==============================================================================

print_summary() {
    if [ "$JSON_OUTPUT" = false ]; then
        echo ""
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${BLUE} Health Check Summary${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo -e "  ${GREEN}Passed:${NC} $CHECKS_PASSED"
        echo -e "  ${RED}Failed:${NC} $CHECKS_FAILED"
        echo ""

        if [ "$CHECKS_FAILED" -eq 0 ]; then
            echo -e "${GREEN}✓ All health checks passed!${NC}"
        else
            echo -e "${RED}✗ Some health checks failed${NC}"
        fi
        echo ""
    fi
}

print_json() {
    local status="healthy"
    if [ "$CHECKS_FAILED" -gt 0 ]; then
        status="unhealthy"
    fi

    cat << EOF
{
  "status": "$status",
  "timestamp": "$(date -Iseconds)",
  "server_url": "$SERVER_URL",
  "checks": {
    "passed": $CHECKS_PASSED,
    "failed": $CHECKS_FAILED
  },
  "results": [
$(printf '    "%s"' "${RESULTS[@]}" | paste -sd ',' -)
  ]
}
EOF
}

# ==============================================================================
# Main Execution
# ==============================================================================

main() {
    if [ "$SILENT" = false ] && [ "$JSON_OUTPUT" = false ]; then
        echo ""
        echo -e "${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
        echo -e "${BLUE}║       Fixxit.ai OpenWebUI Health Check               ║${NC}"
        echo -e "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}"
        echo ""
        log "Checking server at: $SERVER_URL"
    fi

    # Run all health checks
    check_server_running || true
    check_health_endpoint || true
    check_api_endpoints || true
    check_database || true
    check_encryption_key || true
    check_python_environment || true
    check_frontend_build || true
    check_logs_directory || true
    check_disk_space || true
    check_memory || true

    # Output results
    if [ "$JSON_OUTPUT" = true ]; then
        print_json
    else
        print_summary
    fi

    # Exit with appropriate code
    if [ "$CHECKS_FAILED" -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
}

# Run main function
main "$@"
