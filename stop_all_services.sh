#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================="
echo "🛑 Stopping Code-Forge Services"
echo "=================================================${NC}"
echo ""

# Function to kill processes on a port
kill_port() {
    local port=$1
    local name=$2

    if lsof -i :$port > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping $name (port $port)...${NC}"
        lsof -i :$port | grep -v COMMAND | awk '{print $2}' | xargs kill -9 2>/dev/null || true
        echo -e "   ${GREEN}✓ $name stopped${NC}"
    else
        echo -e "   ${GREEN}✓ $name not running${NC}"
    fi
}

# Kill services
kill_port 8051 "MCP Server"
kill_port 5173 "Frontend"

echo ""
echo -e "${GREEN}✅ All services stopped${NC}"
echo ""
echo -e "${YELLOW}Note:${NC} PostgreSQL and Ollama are not stopped"
echo "      (they may be used by other applications)"
echo ""
echo -e "${YELLOW}To restart:${NC} ./start_all_services.sh"
