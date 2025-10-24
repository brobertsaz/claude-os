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

echo "Step 1: Installing Ollama for macOS (Apple Silicon optimized)..."
# Download Ollama for macOS
if ! command -v ollama &> /dev/null; then
    echo "  Downloading Ollama..."
    # Use the direct download URL
    OLLAMA_VERSION=$(curl -s https://api.github.com/repos/ollama/ollama/releases/latest | grep -o '"tag_name": "[^"]*' | cut -d'"' -f4)

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
echo "Step 2: Starting Ollama service..."
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
echo "Step 3: Pulling required models..."
echo "  This may take a few minutes for llama3.1:latest (8B)..."
ollama pull llama3.1:latest
ollama pull nomic-embed-text:latest
echo "  ✅ Models ready"

echo ""
echo "Step 4: Setting up Python environment..."

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
echo "Step 5: Updating configuration..."

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
