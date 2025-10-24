#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================="
echo "🚀 Code-Forge Native Services Startup"
echo "=================================================${NC}"
echo ""

# Get the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Function to check if a port is in use
check_port() {
    local port=$1
    if nc -z localhost $port 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to wait for a service to be ready
wait_for_port() {
    local port=$1
    local max_attempts=30
    local attempt=0

    while ! check_port $port && [ $attempt -lt $max_attempts ]; do
        echo -n "."
        sleep 1
        ((attempt++))
    done

    if check_port $port; then
        echo -e " ${GREEN}✓${NC}"
        return 0
    else
        echo -e " ${RED}✗${NC}"
        return 1
    fi
}

# ===== 1. Check PostgreSQL =====
echo -e "${YELLOW}1. Checking PostgreSQL...${NC}"
if check_port 5432; then
    echo -e "   ${GREEN}✓ PostgreSQL is running on port 5432${NC}"
else
    echo -e "   ${RED}✗ PostgreSQL is not running!${NC}"
    echo "   Please start PostgreSQL first"
    echo "   On macOS: brew services start postgresql"
    exit 1
fi
echo ""

# ===== 2. Check/Start Ollama =====
echo -e "${YELLOW}2. Checking Ollama...${NC}"
if check_port 11434; then
    echo -e "   ${GREEN}✓ Ollama is running on port 11434${NC}"
else
    echo -e "   ${YELLOW}⚠ Ollama is not running, starting...${NC}"
    brew services start ollama > /dev/null 2>&1 || true
    echo -n "   Waiting for Ollama to start"
    wait_for_port 11434
fi

# Verify models are available
echo -n "   Checking models"
for model in llama3.1:latest nomic-embed-text:latest; do
    if ollama list | grep -q "$model"; then
        echo -n "."
    else
        echo -e "\n   ${YELLOW}⚠ Model $model not found, pulling...${NC}"
        ollama pull $model > /dev/null
        echo -n "   "
    fi
done
echo -e " ${GREEN}✓${NC}"
echo ""

# ===== 3. Setup Python Environment =====
echo -e "${YELLOW}3. Setting up Python environment...${NC}"
if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q --upgrade pip setuptools wheel 2>/dev/null || true
echo -e "   ${GREEN}✓ Python environment ready${NC}"
echo ""

# ===== 4. Start MCP Server =====
echo -e "${YELLOW}4. Starting MCP Server...${NC}"
if check_port 8051; then
    echo -e "   ${YELLOW}⚠ Port 8051 already in use, killing existing process...${NC}"
    lsof -i :8051 | grep -v COMMAND | awk '{print $2}' | xargs kill -9 2>/dev/null || true
    sleep 1
fi

cd "$PROJECT_DIR/mcp_server"
nohup python server.py > "$PROJECT_DIR/logs/mcp_server.log" 2>&1 &
MCP_PID=$!
echo "   Server PID: $MCP_PID"
echo -n "   Waiting for server to start"
wait_for_port 8051
cd "$PROJECT_DIR"
echo ""

# ===== 5. Start React Frontend =====
echo -e "${YELLOW}5. Starting React Frontend...${NC}"
if check_port 5173; then
    echo -e "   ${YELLOW}⚠ Port 5173 already in use, killing existing process...${NC}"
    lsof -i :5173 | grep -v COMMAND | awk '{print $2}' | xargs kill -9 2>/dev/null || true
    sleep 1
fi

cd "$PROJECT_DIR/frontend"
nohup npm run dev -- --host 0.0.0.0 > "$PROJECT_DIR/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"
echo -n "   Waiting for frontend to start"
wait_for_port 5173
cd "$PROJECT_DIR"
echo ""

# ===== Summary =====
echo -e "${BLUE}=================================================="
echo "✅ All Services Started Successfully!"
echo "=================================================${NC}"
echo ""
echo -e "${GREEN}📡 Service URLs:${NC}"
echo "   Frontend:    http://localhost:5173"
echo "   MCP Server:  http://localhost:8051"
echo "   API:         http://localhost:8051/api"
echo ""
echo -e "${GREEN}📝 Log Files:${NC}"
echo "   MCP Server:  logs/mcp_server.log"
echo "   Frontend:    logs/frontend.log"
echo ""
echo -e "${GREEN}🛑 To Stop All Services:${NC}"
echo "   ./stop_all_services.sh"
echo ""
echo -e "${YELLOW}💡 Tips:${NC}"
echo "   - Frontend will auto-reload on code changes"
echo "   - MCP Server may need restart for Python changes"
echo "   - View logs with: tail -f logs/mcp_server.log"
echo ""
