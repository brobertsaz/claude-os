#!/bin/bash
# ============================================================================
# Claude OS Docker Container Entrypoint
# ============================================================================
# Handles startup, dependency checks, and graceful shutdown
# ============================================================================

set -e

# Colors (optional, for better logging)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ============================================================================
# Banner
# ============================================================================
echo -e "${BLUE}"
cat << "EOF"
   ____  _                 _        ___  ____
  / ___|| | __ _ _   _  __| | ___  / _ \/ ___|
 | |    | |/ _` | | | |/ _` |/ _ \| | | \___ \
 | |___ | | (_| | |_| | (_| |  __/| |_| |___) |
  \____||_|\__,_|\__,_|\__,_|\___| \___/|____/
                                      Docker
EOF
echo -e "${NC}"

log_info "Starting Claude OS container..."
log_info "Provider: ${CLAUDE_OS_PROVIDER:-local}"

# ============================================================================
# Wait for Redis
# ============================================================================
wait_for_redis() {
    local host="${REDIS_HOST:-redis}"
    local port="${REDIS_PORT:-6379}"
    local max_attempts=30
    local attempt=0

    log_info "Waiting for Redis at ${host}:${port}..."

    while [ $attempt -lt $max_attempts ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            log_success "Redis is ready"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done

    log_warn "Redis not available after ${max_attempts} seconds, continuing anyway..."
    return 0
}

# ============================================================================
# Wait for Ollama (if using local provider)
# ============================================================================
wait_for_ollama() {
    if [ "${CLAUDE_OS_PROVIDER}" != "local" ]; then
        log_info "Skipping Ollama check (provider: ${CLAUDE_OS_PROVIDER})"
        return 0
    fi

    local host="${OLLAMA_HOST:-http://ollama:11434}"
    local max_attempts=60
    local attempt=0

    log_info "Waiting for Ollama at ${host}..."

    while [ $attempt -lt $max_attempts ]; do
        if curl -sf "${host}/api/tags" > /dev/null 2>&1; then
            log_success "Ollama is ready"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    log_warn "Ollama not available after $((max_attempts * 2)) seconds"
    log_warn "You may need to pull models manually or check Ollama status"
    return 0
}

# ============================================================================
# Initialize database directory
# ============================================================================
init_database() {
    local db_dir=$(dirname "${CLAUDE_OS_DB_PATH:-/data/claude-os.db}")

    if [ ! -d "$db_dir" ]; then
        log_info "Creating database directory: $db_dir"
        mkdir -p "$db_dir"
    fi

    log_success "Database directory ready: $db_dir"
}

# ============================================================================
# Graceful shutdown handler
# ============================================================================
shutdown_handler() {
    log_info "Received shutdown signal, gracefully stopping..."
    kill -TERM "$child_pid" 2>/dev/null
    wait "$child_pid"
    log_success "Container stopped gracefully"
    exit 0
}

trap shutdown_handler SIGTERM SIGINT

# ============================================================================
# Main startup sequence
# ============================================================================
main() {
    # Initialize database directory
    init_database

    # Wait for dependencies
    wait_for_redis
    wait_for_ollama

    log_success "All dependencies ready!"
    log_info "Starting application: $@"

    # Execute the command
    exec "$@" &
    child_pid=$!

    # Wait for the child process
    wait "$child_pid"
}

# Run main with all arguments passed to the script
main "$@"
