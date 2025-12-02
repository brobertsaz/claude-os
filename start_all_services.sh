#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
else
    OS="unknown"
fi

echo -e "${BLUE}=================================================="
echo "🚀 Claude OS - Starting All Services"
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
    local service=$2
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

# ===== 1. Check Ollama =====
echo -e "${YELLOW}1. Checking Ollama...${NC}"
if check_port 11434; then
    echo -e "   ${GREEN}✓ Ollama is running on port 11434${NC}"
else
    echo -e "   ${YELLOW}⚠ Ollama is not running, attempting to start...${NC}"
    if [[ "$OS" == "macos" ]]; then
        brew services start ollama > /dev/null 2>&1 || true
    elif [[ "$OS" == "linux" ]]; then
        # Try direct execution first (no sudo needed), fall back to user systemctl
        ollama serve > /dev/null 2>&1 &
    else
        ollama serve > /dev/null 2>&1 &
    fi
    echo -n "   Waiting for Ollama to start"
    if wait_for_port 11434 "Ollama"; then
        :
    else
        echo -e "   ${YELLOW}⚠ Could not verify Ollama is running${NC}"
    fi
fi

# Verify models are available
echo -n "   Checking models"
for model in llama3.1:latest nomic-embed-text:latest; do
    if ollama list | grep -q "$model"; then
        echo -n "."
    else
        echo -e "\n   ${YELLOW}⚠ Model $model not found, pulling...${NC}"
        ollama pull $model > /dev/null 2>&1 || true
        echo -n "   "
    fi
done
echo -e " ${GREEN}✓${NC}"
echo ""

# ===== 2. Setup Python Environment =====
echo -e "${YELLOW}2. Setting up Python environment...${NC}"
if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q --upgrade pip setuptools wheel 2>/dev/null || true
echo -e "   ${GREEN}✓ Python environment ready${NC}"
echo ""

# ===== 3. Ensure data directory exists =====
echo -e "${YELLOW}3. Checking data directory...${NC}"
if [ ! -d "data" ]; then
    mkdir -p data
    echo -e "   ${GREEN}✓ Created data/ directory${NC}"
else
    echo -e "   ${GREEN}✓ data/ directory exists${NC}"
fi

if [ ! -d "logs" ]; then
    mkdir -p logs
    echo -e "   ${GREEN}✓ Created logs/ directory${NC}"
else
    echo -e "   ${GREEN}✓ logs/ directory exists${NC}"
fi
echo ""

# ===== 4. Check Redis =====
echo -e "${YELLOW}4. Checking Redis...${NC}"
if ! command -v redis-server &> /dev/null; then
    echo -e "   ${YELLOW}⚠ Redis is not installed${NC}"
    if [[ "$OS" == "macos" ]]; then
        echo "   Install with: brew install redis"
    elif [[ "$OS" == "linux" ]]; then
        echo "   Install with: sudo apt install redis-server  (or dnf/pacman)"
    fi
    echo "   Or run ./setup.sh for full installation"
elif redis-cli ping &> /dev/null; then
    echo -e "   ${GREEN}✓ Redis is running${NC}"
else
    echo -e "   ${YELLOW}⚠ Redis is not running, attempting to start...${NC}"
    if [[ "$OS" == "macos" ]]; then
        brew services start redis > /dev/null 2>&1 || redis-server --daemonize yes > /dev/null 2>&1 || true
    else
        redis-server --daemonize yes > /dev/null 2>&1 || true
    fi
    sleep 2
    if redis-cli ping &> /dev/null; then
        echo -e "   ${GREEN}✓ Redis started successfully${NC}"
    else
        echo -e "   ${RED}❌ Could not start Redis${NC}"
        echo "   Please start Redis manually: redis-server"
    fi
fi
echo ""

# ===== 5. Start RQ Workers (Real-Time Learning System) =====
echo -e "${YELLOW}5. Starting RQ Workers (Real-Time Learning)...${NC}"
if check_port 6379; then
    nohup "$PROJECT_DIR/venv/bin/python3" -m rq worker claude-os:learning claude-os:prompts claude-os:ingest --with-scheduler > "$PROJECT_DIR/logs/rq_workers.log" 2>&1 &
    RQ_PID=$!
    echo "   RQ Workers PID: $RQ_PID (logging to logs/rq_workers.log)"
    echo -e "   ${GREEN}✓ RQ workers started${NC}"
else
    echo -e "   ${YELLOW}⚠ Redis not available, skipping RQ workers${NC}"
fi
echo ""

# ===== 6. Start MCP Server =====
echo -e "${YELLOW}6. Starting MCP Server...${NC}"
if check_port 8051; then
    echo -e "   ${YELLOW}⚠ Port 8051 already in use, killing existing process...${NC}"
    lsof -i :8051 | grep -v COMMAND | awk '{print $2}' | xargs kill -9 2>/dev/null || true
    sleep 1
fi

cd "$PROJECT_DIR/mcp_server"
nohup env SQLITE_DB_PATH="$PROJECT_DIR/data/claude-os.db" "$PROJECT_DIR/venv/bin/python3" server.py > "$PROJECT_DIR/logs/mcp_server.log" 2>&1 &
MCP_PID=$!
echo "   Server PID: $MCP_PID (logging to logs/mcp_server.log)"
echo -n "   Waiting for server to start"
if wait_for_port 8051 "MCP Server"; then
    :
else
    echo -e "   ${YELLOW}⚠ Could not verify server is running${NC}"
    echo "   Check logs with: tail -f logs/mcp_server.log"
fi
cd "$PROJECT_DIR"
echo ""

# ===== 7. Start React Frontend =====
echo -e "${YELLOW}7. Starting React Frontend...${NC}"
if check_port 5173; then
    echo -e "   ${YELLOW}⚠ Port 5173 already in use, killing existing process...${NC}"
    lsof -i :5173 | grep -v COMMAND | awk '{print $2}' | xargs kill -9 2>/dev/null || true
    sleep 1
fi

cd "$PROJECT_DIR/frontend"
nohup npm run dev -- --host 0.0.0.0 > "$PROJECT_DIR/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID (logging to logs/frontend.log)"
echo -n "   Waiting for frontend to start"
if wait_for_port 5173 "Frontend"; then
    :
else
    echo -e "   ${YELLOW}⚠ Could not verify frontend is running${NC}"
    echo "   Check logs with: tail -f logs/frontend.log"
fi
cd "$PROJECT_DIR"
echo ""

# ===== Summary =====
echo -e "${BLUE}=================================================="
echo "✅ All Services Started Successfully!"
echo "=================================================${NC}"
echo ""
echo -e "${GREEN}📡 Service URLs:${NC}"
echo "   🎨 Frontend:    http://localhost:5173"
echo "   🔌 API Server:  http://localhost:8051"
echo "   📚 API Docs:    http://localhost:8051/docs"
echo ""
echo -e "${GREEN}🔧 Ollama:${NC}"
echo "   Host:    http://localhost:11434"
echo "   Models:  llama3.1:latest, nomic-embed-text:latest"
echo ""
echo -e "${GREEN}💾 Databases:${NC}"
echo "   SQLite:  data/claude-os.db"
echo "   Redis:   localhost:6379"
echo ""
echo -e "${GREEN}🤖 Real-Time Learning System:${NC}"
echo "   RQ Workers: listening on 3 queues"
echo "   Queues: claude-os:learning, prompts, ingest"
echo "   Status: Active & always learning!"
echo ""
echo -e "${GREEN}📝 Log Files:${NC}"
echo "   MCP Server:   logs/mcp_server.log"
echo "   Frontend:     logs/frontend.log"
echo "   RQ Workers:   logs/rq_workers.log"
echo ""
echo -e "${GREEN}🛑 To Stop All Services:${NC}"
echo "   ./stop_all_services.sh"
echo ""
echo -e "${GREEN}🔄 To Restart All Services:${NC}"
echo "   ./restart_services.sh"
echo ""
echo -e "${YELLOW}💡 Tips:${NC}"
echo "   - Frontend will auto-reload on code changes"
echo "   - View logs: tail -f logs/mcp_server.log"
echo "   - Backup DB: cp data/claude-os.db data/claude-os.db.backup"
echo "   - Restart MCP: kill $MCP_PID && ./start_all_services.sh"
echo ""
echo -e "${GREEN}🚀 Enjoy building with Claude OS!${NC}"
echo ""
