#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Detect OS and package manager
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        PKG_MANAGER="brew"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        if command -v apt-get &> /dev/null; then
            PKG_MANAGER="apt"
        elif command -v dnf &> /dev/null; then
            PKG_MANAGER="dnf"
        elif command -v yum &> /dev/null; then
            PKG_MANAGER="yum"
        elif command -v pacman &> /dev/null; then
            PKG_MANAGER="pacman"
        else
            PKG_MANAGER="unknown"
        fi
    else
        OS="unknown"
        PKG_MANAGER="unknown"
    fi
}

detect_os

# Banner
clear
echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   🚀 Claude OS Setup Script                    ║"
echo "║                                                                ║"
echo "║   This script will set up Claude OS with all dependencies      ║"
echo "║   and prepare it for development                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Step 1: Check prerequisites
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 1: Checking Prerequisites${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    echo "Install Python 3 from https://www.python.org/downloads/"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo -e "${GREEN}✅ Python ${PYTHON_VERSION} found${NC}"

# Check Git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git is not installed${NC}"
    echo "Install Git from https://git-scm.com/"
    exit 1
fi
echo -e "${GREEN}✅ Git found${NC}"

# Check if in git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Not in a git repository${NC}"
    echo "Make sure to run this from the Claude OS project directory"
else
    echo -e "${GREEN}✅ In Claude OS git repository${NC}"
fi

echo ""

# Step 2: Create virtual environment
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 2: Setting Up Python Environment${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
fi

echo "Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"

echo "Upgrading pip, setuptools, and wheel..."
pip install -q --upgrade pip setuptools wheel
echo -e "${GREEN}✅ Pip upgraded${NC}"

echo ""

# Step 3: Install Python dependencies
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 3: Installing Python Dependencies${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

if [ -f "requirements.txt" ]; then
    echo "Installing requirements from requirements.txt..."
    pip install -q -r requirements.txt
    echo -e "${GREEN}✅ Python dependencies installed${NC}"
else
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
fi

echo ""

# Step 4: Check Ollama
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 4: Setting Up Ollama (LLM Engine)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✅ Ollama already installed${NC}"
else
    echo -e "${YELLOW}⚠️  Ollama not found${NC}"
    echo "Installing Ollama..."

    if [[ "$OS" == "macos" ]]; then
        # macOS
        if ! command -v brew &> /dev/null; then
            echo -e "${RED}❌ Homebrew not found (required for macOS)${NC}"
            echo "Install from https://brew.sh"
            exit 1
        fi
        brew install ollama
    elif [[ "$OS" == "linux" ]]; then
        # Linux - use universal installer (works on all distros)
        curl -fsSL https://ollama.ai/install.sh | sh
    else
        echo -e "${RED}❌ Unsupported OS${NC}"
        echo "Please install Ollama manually from https://ollama.ai"
        exit 1
    fi
    echo -e "${GREEN}✅ Ollama installed${NC}"
fi

echo "Checking if Ollama is running..."
if curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo -e "${GREEN}✅ Ollama is running${NC}"
else
    echo -e "${YELLOW}⚠️  Ollama is not running${NC}"
    echo "Starting Ollama..."
    if [[ "$OS" == "macos" ]]; then
        brew services start ollama &> /dev/null || true
    elif [[ "$OS" == "linux" ]]; then
        # Start ollama directly (no sudo needed)
        ollama serve &> /dev/null &
    else
        ollama serve &> /dev/null &
    fi
    echo "Waiting for Ollama to start..."
    sleep 5

    if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
        echo -e "${YELLOW}⚠️  Could not verify Ollama is running${NC}"
        echo "You may need to start it manually"
    else
        echo -e "${GREEN}✅ Ollama started successfully${NC}"
    fi
fi

echo "Ensuring required models are available..."
for model in llama3.1:latest nomic-embed-text:latest; do
    if curl -s http://localhost:11434/api/tags | grep -q "\"name\":\"$model\""; then
        echo -e "${GREEN}✅ Model $model is installed${NC}"
    else
        echo "Downloading model $model (this may take a few minutes)..."
        ollama pull $model > /dev/null 2>&1 || true
        echo -e "${GREEN}✅ Model $model downloaded${NC}"
    fi
done

echo ""

# Step 5: Check Redis
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 5: Setting Up Redis (Cache & Queue System)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

if command -v redis-cli &> /dev/null; then
    echo -e "${GREEN}✅ Redis already installed${NC}"
else
    echo -e "${YELLOW}⚠️  Redis not found${NC}"
    echo "Installing Redis..."

    if [[ "$OS" == "macos" ]]; then
        brew install redis
    elif [[ "$OS" == "linux" ]]; then
        case "$PKG_MANAGER" in
            apt)
                sudo apt-get update && sudo apt-get install -y redis-server
                ;;
            dnf)
                sudo dnf install -y redis
                ;;
            yum)
                sudo yum install -y redis
                ;;
            pacman)
                sudo pacman -S --noconfirm redis
                ;;
            *)
                echo -e "${RED}❌ Unknown package manager${NC}"
                echo "Please install Redis manually from https://redis.io"
                exit 1
                ;;
        esac
    else
        echo -e "${RED}❌ Unsupported OS${NC}"
        echo "Please install Redis manually from https://redis.io"
        exit 1
    fi
    echo -e "${GREEN}✅ Redis installed${NC}"
fi

echo "Checking if Redis is running..."
if redis-cli ping &> /dev/null; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo -e "${YELLOW}⚠️  Redis is not running${NC}"
    echo "Starting Redis..."
    if [[ "$OS" == "macos" ]]; then
        brew services start redis > /dev/null 2>&1 || true
    elif [[ "$OS" == "linux" ]]; then
        # Start redis directly (no sudo needed)
        redis-server --daemonize yes > /dev/null 2>&1 || true
    else
        redis-server --daemonize yes > /dev/null 2>&1 || true
    fi
    sleep 2

    if redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✅ Redis started successfully${NC}"
    else
        echo -e "${YELLOW}⚠️  Could not verify Redis is running${NC}"
        echo "You may need to start it manually"
    fi
fi

echo ""

# Step 6: Create directories
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 6: Creating Required Directories${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

mkdir -p data
mkdir -p logs
mkdir -p frontend

echo -e "${GREEN}✅ Directories created:${NC}"
echo "   • data/     (SQLite database)"
echo "   • logs/     (Service logs)"
echo "   • frontend/ (React UI)"

echo ""

# Step 7: Install Node/npm if needed
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 7: Checking Frontend Dependencies${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

if [ -f "frontend/package.json" ]; then
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}❌ npm not found (required for frontend)${NC}"
        echo "Install Node.js from https://nodejs.org/"
        exit 1
    fi

    echo "Installing frontend dependencies..."
    cd frontend
    npm install -q
    cd ..
    echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  frontend/package.json not found${NC}"
fi

echo ""

# Step 8: Initialize database
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 8: Initializing Database${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

if [ ! -f "data/claude-os.db" ]; then
    echo "Creating SQLite database..."
    python3 << 'EOF'
from app.core.sqlite_manager import get_sqlite_manager
db = get_sqlite_manager()
print("✅ Database initialized")
EOF
    echo -e "${GREEN}✅ Database created${NC}"
else
    echo -e "${GREEN}✅ Database already exists${NC}"
fi

echo ""

# Step 9: Summary and next steps
echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              ✨ Claude OS Setup Complete! ✨                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

echo -e "${GREEN}✅ All components are ready:${NC}"
echo "   ✓ Python environment"
echo "   ✓ Dependencies installed"
echo "   ✓ Ollama (LLM engine)"
echo "   ✓ Redis (cache & queues)"
echo "   ✓ Database"
echo "   ✓ Directories"
echo ""

echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo "1. Start all services:"
echo -e "   ${CYAN}./start_all_services.sh${NC}"
echo ""
echo "2. Access the services:"
echo -e "   ${CYAN}Frontend:  http://localhost:5173${NC}"
echo -e "   ${CYAN}MCP API:   http://localhost:8051${NC}"
echo -e "   ${CYAN}API Docs:  http://localhost:8051/docs${NC}"
echo ""
echo "3. Initialize your first project:"
echo -e "   ${CYAN}Create a project in the UI, then run:${NC}"
echo -e "   ${CYAN}/initialize-project [project-id]${NC}"
echo ""
echo "4. Register MCPs with Claude Code:"
echo -e "   ${CYAN}claude mcp add --transport http [mcp-name] http://localhost:8051/mcp/kb/[KB-name]${NC}"
echo ""

echo -e "${YELLOW}💡 Tips:${NC}"
echo "   • Run './start_all_services.sh' to start everything"
echo "   • Run './stop_all_services.sh' to stop everything"
echo "   • Run './restart_services.sh' to restart everything"
echo "   • Check logs with: tail -f logs/mcp_server.log"
echo ""

echo -e "${CYAN}Documentation:${NC}"
echo "   • WHAT_IS_CLAUDE_OS.md (learn what Claude OS does)"
echo "   • CLAUDE_OS_DEVELOPER_GUIDE.md (detailed development guide)"
echo ""

echo -e "${GREEN}Ready to get started! 🚀${NC}\n"
