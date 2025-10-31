#!/bin/bash
# Start the MCP server natively on macOS with Metal GPU acceleration

echo "🚀 Starting Claude OS MCP Server (Native, no Docker)"
echo "=================================================="
echo ""
echo "System Info:"
echo "  - CPU Cores: $(sysctl -n hw.ncpu)"
echo "  - RAM: $(sysctl -n hw.memsize | awk '{print $0/1024/1024/1024 " GB"}')"
echo "  - Ollama: $(which ollama)"
echo ""

# Get the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "❌ Ollama is not running!"
    echo "Start Ollama with: brew services start ollama"
    exit 1
fi

echo "✅ Ollama is running"
echo ""

# Activate venv
source "$PROJECT_DIR/venv/bin/activate"

echo ""
echo "Starting MCP Server..."
echo "📡 MCP Server will be available at: http://localhost:8051"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the server from the project root with correct database path
export SQLITE_DB_PATH="$PROJECT_DIR/data/claude-os.db"
echo "Database: $SQLITE_DB_PATH"
echo ""

cd "$PROJECT_DIR/mcp_server"
python3 server.py
