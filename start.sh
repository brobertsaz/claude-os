#!/bin/bash
# Start Claude OS services

CLAUDE_OS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$CLAUDE_OS_DIR"

echo "🚀 Starting Claude OS..."
echo ""

# Activate virtual environment
source venv/bin/activate

# Start the MCP server
echo "📡 Starting MCP server on http://localhost:8051"
python3 mcp_server/server.py &
MCP_PID=$!

echo "✅ Claude OS MCP Server is running!"
echo ""
echo "   📡 MCP Server: http://localhost:8051"
echo "      (For Claude Code integration - do NOT open in browser)"
echo ""
echo "To stop MCP server: kill \$MCP_PID or press Ctrl+C"
echo ""
echo "════════════════════════════════════════"
echo "💡 Want the full experience?"
echo "════════════════════════════════════════"
echo ""
echo "This script only starts the MCP server."
echo ""
echo "To start ALL services (MCP + Frontend + Workers):"
echo "   ./start_all_services.sh"
echo ""
echo "This will give you:"
echo "   • MCP Server (port 8051) - For Claude Code"
echo "   • Web UI (port 5173) - Visual interface"
echo "   • Redis + Workers - Real-time learning"
echo "   • Ollama - Local AI models"
echo ""

# Wait for server to exit
wait $MCP_PID
