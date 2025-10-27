#!/bin/bash
set -e

echo "🚀 Claude OS Setup - NATIVE (No Docker, No PostgreSQL)"
echo "=================================================="
echo ""

# Step 1: Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is for macOS only"
    exit 1
fi

echo "Step 1: Checking Ollama installation..."
if ! command -v ollama &> /dev/null; then
    echo "  ❌ Ollama not found. Please install it first:"
    echo ""
    echo "  Option A: Via Homebrew (recommended)"
    echo "    brew install ollama"
    echo "    brew services start ollama"
    echo ""
    echo "  Option B: Download from https://ollama.ai"
    echo ""
    exit 1
fi

OLLAMA_VERSION=$(ollama --version 2>/dev/null | cut -d' ' -f2)
echo "  ✅ Ollama found"

# Check if Ollama is running
echo "  Checking if Ollama is running..."
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "  ⚠️  Ollama is not running. Starting..."
    brew services start ollama 2>/dev/null || true
    sleep 3
fi

if curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "  ✅ Ollama is running on port 11434"
else
    echo "  ⚠️  Could not verify Ollama is running"
fi

echo ""
echo "Step 2: Pulling required models..."
echo "  This may take a few minutes (first time only)..."

# Pull llama3.1 model
if ! ollama list | grep -q "llama3.1"; then
    echo "  📥 Pulling llama3.1:latest (8B model)..."
    ollama pull llama3.1:latest
else
    echo "  ✅ llama3.1:latest already available"
fi

# Pull embedding model
if ! ollama list | grep -q "nomic-embed-text"; then
    echo "  📥 Pulling nomic-embed-text (embeddings)..."
    ollama pull nomic-embed-text:latest
else
    echo "  ✅ nomic-embed-text already available"
fi

echo "  ✅ Models ready"

echo ""
echo "Step 3: Setting up Python environment..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "  ❌ Python 3 not found. Please install Python 3.11+ first"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "  ✅ Python $PYTHON_VERSION found"

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

echo "  Installing Python dependencies..."
pip install -q --upgrade pip setuptools wheel
pip install -q -r requirements.txt

echo "  ✅ Python environment ready"

echo ""
echo "Step 4: Creating data directory..."

# Create data directory for SQLite database
if [ ! -d "data" ]; then
    mkdir -p data
    echo "  ✅ Created data/ directory"
else
    echo "  ✅ data/ directory already exists"
fi

# Create logs directory
if [ ! -d "logs" ]; then
    mkdir -p logs
    echo "  ✅ Created logs/ directory"
else
    echo "  ✅ logs/ directory already exists"
fi

echo ""
echo "Step 5: Initializing SQLite database..."

# The database will be created automatically on first run
# But we can verify the schema will be set up
if [ -f "app/db/schema.sqlite" ]; then
    echo "  ✅ SQLite schema file found"
    echo "  💾 Database will be created at: data/claude-os.db"
else
    echo "  ⚠️  Schema file not found, but database will auto-initialize"
fi

echo ""
echo "Step 6: Setting up Node.js frontend..."

# Check if Node is installed
if ! command -v node &> /dev/null; then
    echo "  ⚠️  Node.js not found. Install from https://nodejs.org"
    echo "  Frontend setup skipped (you can set it up later)"
else
    NODE_VERSION=$(node --version)
    echo "  ✅ Node.js $NODE_VERSION found"

    if [ -d "frontend" ]; then
        echo "  Installing frontend dependencies..."
        cd frontend
        npm install > /dev/null 2>&1 || true
        cd ..
        echo "  ✅ Frontend dependencies ready"
    fi
fi

echo ""
echo "=================================================="
echo "✅ Claude OS Setup Complete!"
echo "=================================================="
echo ""
echo "🎯 Next Steps:"
echo ""
echo "1. Start Claude OS:"
echo "   ./start_all_services.sh"
echo ""
echo "2. Access the UI:"
echo "   Frontend: http://localhost:5173"
echo "   API:      http://localhost:8051"
echo ""
echo "3. Manage services:"
echo "   Restart: ./restart_services.sh"
echo "   Stop:    ./stop_all_services.sh"
echo ""
echo "📚 Database:"
echo "   Type:     SQLite (single file)"
echo "   Location: data/claude-os.db"
echo "   Backup:   cp data/claude-os.db data/claude-os.db.backup"
echo ""
echo "🚀 You're all set! Let's build something amazing!"
echo ""
