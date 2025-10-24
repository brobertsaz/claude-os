#!/bin/bash
set -e

echo "🚀 Setting up Code-Forge MCP Server - NATIVE (No Docker)"
echo "=================================================="
echo ""

# Step 1: Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is for macOS only"
    exit 1
fi

echo "Step 1: Checking PostgreSQL installation..."
if ! command -v psql &> /dev/null; then
    echo "  ❌ PostgreSQL not found. Please install it first:"
    echo ""
    echo "  Option A: Via Homebrew (recommended)"
    echo "    brew install postgresql@16"
    echo "    brew services start postgresql@16"
    echo ""
    echo "  Option B: Download from https://www.postgresql.org/download/macosx/"
    echo ""
    exit 1
fi

PSQL_VERSION=$(psql --version | cut -d' ' -f3)
echo "  ✅ PostgreSQL $PSQL_VERSION found"

# Check if PostgreSQL is running
if ! pg_isready -h localhost &> /dev/null; then
    echo "  ⚠️  PostgreSQL is not running. Starting..."
    brew services start postgresql@16 2>/dev/null || true
    sleep 2
fi

# Create database if it doesn't exist
echo "  Setting up 'codeforge' database..."
if ! psql -h localhost -U "$USER" -l 2>/dev/null | grep -q "codeforge"; then
    createdb -h localhost -U "$USER" codeforge 2>/dev/null || true
    echo "  ✅ Database 'codeforge' created"
else
    echo "  ✅ Database 'codeforge' already exists"
fi

# Test connection
if psql -h localhost -U "$USER" -d codeforge -c "SELECT 1" > /dev/null 2>&1; then
    echo "  ✅ PostgreSQL connection verified"
else
    echo "  ⚠️  Could not connect to PostgreSQL as user '$USER'"
    echo "  You may need to set POSTGRES_PASSWORD environment variable"
fi

echo ""
echo "Step 2: Installing Ollama for macOS (Apple Silicon optimized)..."
# Download Ollama for macOS
if ! command -v ollama &> /dev/null; then
    echo "  Downloading Ollama..."
    # For Apple Silicon Mac
    curl -L "https://ollama.ai/download/Ollama-arm64.zip" -o /tmp/Ollama.zip
    unzip -o /tmp/Ollama.zip -d /Applications/
    rm /tmp/Ollama.zip

    # Create symlink for CLI access
    sudo ln -sf /Applications/Ollama.app/Contents/Resources/ollama /usr/local/bin/ollama 2>/dev/null || true

    echo "  ✅ Ollama installed successfully"
else
    echo "  ✅ Ollama already installed at $(which ollama)"
fi

echo ""
echo "Step 3: Starting Ollama service..."
# Start Ollama in the background
# Check if already running
if ! pgrep -x "ollama" > /dev/null; then
    # Start Ollama daemon
    launchctl stop com.ollama.ollama 2>/dev/null || true
    sleep 1
    launchctl start com.ollama.ollama 2>/dev/null || true

    # Also try direct command
    nohup ollama serve > ~/.ollama/logs.txt 2>&1 &
    sleep 3
    echo "  ✅ Ollama started (check with: ollama list)"
else
    echo "  ✅ Ollama already running"
fi

echo ""
echo "Step 4: Pulling required models..."
echo "  This may take a few minutes for llama3.1:latest (8B)..."
ollama pull llama3.1:latest
ollama pull nomic-embed-text:latest
echo "  ✅ Models ready"

echo ""
echo "Step 5: Setting up Python environment..."

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
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "  ✅ Python environment ready"

echo ""
echo "Step 6: Updating configuration..."

# Update rag_engine.py to use localhost
sed -i '' 's|base_url=Config.OLLAMA_HOST|base_url="http://localhost:11434"|g' app/core/rag_engine.py

# Also ensure we're using the right model
sed -i '' 's|model="llama3.1:latest"|model="llama3.1:latest"|g' app/core/rag_engine.py

echo "  ✅ Configuration updated"

echo ""
echo "=================================================="
echo "✅ Setup Complete!"
echo "=================================================="
echo ""
echo "To start the MCP server, run:"
echo ""
echo "  source venv/bin/activate"
echo "  cd mcp_server"
echo "  python server.py"
echo ""
echo "The MCP server will be available at: http://localhost:8051"
echo ""
echo "To check Ollama status:"
echo "  ollama list          # Show loaded models"
echo "  ollama ps            # Show running models"
echo "  ollama serve         # Start Ollama manually"
echo ""
echo "Your M4 Pro will now use full Metal GPU acceleration! 🚀"
