#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================="
echo "🛑 Claude OS - Stopping All Services"
echo "=================================================${NC}"
echo ""

# Function to kill processes on a port
kill_port() {
    local port=$1
    local name=$2

    if lsof -i :$port > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping $name (port $port)...${NC}"
        PID=$(lsof -i :$port | grep -v COMMAND | awk '{print $2}' | head -1)
        if [ -n "$PID" ]; then
            kill -9 $PID 2>/dev/null || true
            echo -e "   ${GREEN}✓ $name stopped (PID: $PID)${NC}"
        fi
    else
        echo -e "   ${GREEN}✓ $name not running${NC}"
    fi
}

# Kill services
echo -e "${YELLOW}Stopping Claude OS services...${NC}"
echo ""

# Stop MCP Server and Frontend
kill_port 8051 "🔌 MCP Server"
kill_port 5173 "🎨 React Frontend"

# Stop RQ Workers
echo -e "${YELLOW}Stopping RQ Workers (Real-Time Learning)...${NC}"
pkill -f "rq worker" 2>/dev/null || true
if pgrep -f "rq worker" > /dev/null; then
    echo -e "   ${RED}❌ RQ Workers still running, forcing kill...${NC}"
    pkill -9 -f "rq worker" 2>/dev/null || true
fi
echo -e "   ${GREEN}✓ RQ Workers stopped${NC}"

# Stop Redis
echo -e "${YELLOW}Stopping Redis...${NC}"
if redis-cli ping &> /dev/null; then
    redis-cli shutdown nosave 2>/dev/null || true
    sleep 1
    if ! redis-cli ping &> /dev/null; then
        echo -e "   ${GREEN}✓ Redis stopped${NC}"
    else
        echo -e "   ${YELLOW}⚠ Redis still running${NC}"
    fi
else
    echo -e "   ${GREEN}✓ Redis not running${NC}"
fi

echo ""
echo -e "${GREEN}✅ All Claude OS services stopped${NC}"
echo ""
echo -e "${YELLOW}ℹ️  Note:${NC}"
echo "   - Ollama is NOT stopped (may be used by other apps)"
echo "   - SQLite database (data/claude-os.db) is preserved"
echo "   - Redis can be restarted with: redis-server"
echo ""
echo -e "${YELLOW}To restart:${NC}"
echo "   ./restart_services.sh"
echo ""
echo -e "${YELLOW}To start with full setup:${NC}"
echo "   ./start_all_services.sh"
echo ""
