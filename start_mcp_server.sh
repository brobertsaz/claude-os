#!/bin/bash
# Start the MCP server natively on macOS with Metal GPU acceleration

echo "🚀 Starting Code-Forge MCP Server (Native, no Docker)"
echo "=================================================="
echo ""
echo "System Info:"
echo "  - CPU Cores: $(sysctl -n hw.ncpu)"
echo "  - RAM: $(sysctl -n hw.memsize | awk '{print $0/1024/1024/1024 " GB"}')"
echo "  - Ollama: $(which ollama)"
echo ""

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "❌ Ollama is not running!"
    echo "Start Ollama with: brew services start ollama"
    exit 1
fi

echo "✅ Ollama is running"
echo ""

# Activate venv
source venv/bin/activate

# Check PostgreSQL connection
echo "Checking PostgreSQL connection..."
if ! psql -h localhost -U $USER -d codeforge -c "SELECT 1" &> /dev/null; then
    echo "⚠️  Warning: Could not connect to PostgreSQL"
    echo "   Make sure PostgreSQL is running and accessible"
fi

echo ""
echo "Starting MCP Server..."
echo "📡 MCP Server will be available at: http://localhost:8051"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the server
cd mcp_server
python server.py
