#!/bin/bash

# ============================================================================
# Code-Forge Docker Container Entrypoint
# ============================================================================
# This script runs inside the Docker container and starts the MCP server.
# ============================================================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Print functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Banner
echo -e "${PURPLE}"
cat << "EOF"
   ____          _        _____
  / ___|___   __| | ___  |  ___|__  _ __ __ _  ___
 | |   / _ \ / _` |/ _ \ | |_ / _ \| '__/ _` |/ _ \
 | |__| (_) | (_| |  __/ |  _| (_) | | | (_| |  __/
  \____\___/ \__,_|\___| |_|  \___/|_|  \__, |\___|
                                        |___/
         MCP Server Container
EOF
echo -e "${NC}"

print_status "Starting Code-Forge MCP Server..."

# ============================================================================
# Wait for Dependencies
# ============================================================================
print_status "Waiting for dependencies to be ready..."

# Wait for PostgreSQL
print_status "Checking PostgreSQL connection..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if python3 -c "import psycopg2; psycopg2.connect(host='${POSTGRES_HOST}', port=${POSTGRES_PORT}, dbname='${POSTGRES_DB}', user='${POSTGRES_USER}')" 2>/dev/null; then
        print_success "PostgreSQL is ready"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        print_error "PostgreSQL is not available after ${MAX_RETRIES} attempts"
        exit 1
    fi
    echo -n "."
    sleep 1
done

# Wait for Ollama
print_status "Checking Ollama connection..."
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s "${OLLAMA_HOST}/api/tags" > /dev/null 2>&1; then
        print_success "Ollama is ready"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        print_warning "Ollama is not available, but continuing anyway..."
        break
    fi
    echo -n "."
    sleep 1
done

# ============================================================================
# Start MCP Server
# ============================================================================
print_success "All dependencies ready!"
print_status "Starting MCP Server on port ${MCP_SERVER_PORT}..."

# Start the MCP server
exec python3 mcp_server/server.py

