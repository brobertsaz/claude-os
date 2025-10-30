#!/bin/bash
# Claude OS Installation Script
# Sets up Claude OS for a new user/machine

set -e  # Exit on error

CLAUDE_OS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_CLAUDE_DIR="${HOME}/.claude"
TEMPLATES_DIR="${CLAUDE_OS_DIR}/templates"

echo "🚀 Claude OS Installation"
echo "========================="
echo ""
echo "Claude OS Directory: ${CLAUDE_OS_DIR}"
echo "User Claude Directory: ${USER_CLAUDE_DIR}"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    echo "   Please install Python 3.8+ and try again"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python ${PYTHON_VERSION} detected"

# Create user .claude directory if it doesn't exist
if [ ! -d "$USER_CLAUDE_DIR" ]; then
    echo "📁 Creating ${USER_CLAUDE_DIR}..."
    mkdir -p "${USER_CLAUDE_DIR}/commands"
    mkdir -p "${USER_CLAUDE_DIR}/skills"
else
    echo "✅ ${USER_CLAUDE_DIR} already exists"
fi

# Create symlinks for commands
echo ""
echo "🔗 Setting up command symlinks..."
for cmd_file in "${TEMPLATES_DIR}"/commands/*.md; do
    if [ -f "$cmd_file" ]; then
        cmd_name=$(basename "$cmd_file")
        dest="${USER_CLAUDE_DIR}/commands/${cmd_name}"

        # Remove existing file/link
        if [ -e "$dest" ] || [ -L "$dest" ]; then
            rm -f "$dest"
        fi

        # Create symlink
        ln -s "$cmd_file" "$dest"
        echo "   ✅ Linked: ${cmd_name}"
    fi
done

# Create symlinks for skills
echo ""
echo "🔗 Setting up skill symlinks..."
for skill_dir in "${TEMPLATES_DIR}"/skills/*/; do
    if [ -d "$skill_dir" ]; then
        skill_name=$(basename "$skill_dir")
        dest="${USER_CLAUDE_DIR}/skills/${skill_name}"

        # Remove existing directory/link
        if [ -e "$dest" ] || [ -L "$dest" ]; then
            rm -rf "$dest"
        fi

        # Create symlink
        ln -s "$skill_dir" "$dest"
        echo "   ✅ Linked: ${skill_name}/"
    fi
done

# Set up Python virtual environment
echo ""
echo "🐍 Setting up Python environment..."
if [ ! -d "${CLAUDE_OS_DIR}/venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv "${CLAUDE_OS_DIR}/venv"
fi

echo "   Installing dependencies..."
source "${CLAUDE_OS_DIR}/venv/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r "${CLAUDE_OS_DIR}/requirements.txt"
echo "   ✅ Dependencies installed"

# Create config file
echo ""
echo "⚙️  Creating configuration..."
CONFIG_FILE="${CLAUDE_OS_DIR}/claude-os-config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    cat > "$CONFIG_FILE" << EOF
{
  "server": {
    "host": "0.0.0.0",
    "port": 8051
  },
  "database": {
    "path": "./data/claude-os.db"
  },
  "embeddings": {
    "model": "all-MiniLM-L6-v2",
    "device": "cpu"
  },
  "installed_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "version": "1.0.0"
}
EOF
    echo "   ✅ Created ${CONFIG_FILE}"
else
    echo "   ✅ Config already exists"
fi

# Update MCP server configuration
echo ""
echo "📡 Configuring MCP server..."
MCP_CONFIG="${USER_CLAUDE_DIR}/mcp-servers/code-forge.json"
MCP_DIR=$(dirname "$MCP_CONFIG")

if [ ! -d "$MCP_DIR" ]; then
    mkdir -p "$MCP_DIR"
fi

cat > "$MCP_CONFIG" << EOF
{
  "name": "code-forge",
  "description": "Claude OS - AI Memory & Knowledge Base System",
  "url": "http://localhost:8051",
  "enabled": true,
  "claude_os_dir": "${CLAUDE_OS_DIR}"
}
EOF
echo "   ✅ MCP configuration updated"

# Create start script
echo ""
echo "🎬 Creating start script..."
START_SCRIPT="${CLAUDE_OS_DIR}/start.sh"
cat > "$START_SCRIPT" << 'EOF'
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

echo "✅ Claude OS is running!"
echo ""
echo "   MCP Server: http://localhost:8051"
echo "   Web UI: http://localhost:8051 (coming soon)"
echo ""
echo "To stop: kill $MCP_PID"
echo "Or use Ctrl+C"
echo ""

# Wait for server to exit
wait $MCP_PID
EOF

chmod +x "$START_SCRIPT"
echo "   ✅ Created start script: ${START_SCRIPT}"

# Summary
echo ""
echo "✨ Installation complete!"
echo ""
echo "📋 What was set up:"
echo "   ✅ Commands linked to ~/.claude/commands/"
echo "   ✅ Skills linked to ~/.claude/skills/"
echo "   ✅ Python virtual environment created"
echo "   ✅ Dependencies installed"
echo "   ✅ MCP server configured"
echo ""
echo "🎯 Next steps:"
echo "   1. Start Claude OS:"
echo "      ./start.sh"
echo ""
echo "   2. In a new terminal, go to your project:"
echo "      cd /path/to/your/project"
echo ""
echo "   3. Initialize your project with Claude OS:"
echo "      /claude-os-init"
echo ""
echo "   4. Start coding with AI memory!"
echo ""
echo "📚 Documentation: ${CLAUDE_OS_DIR}/README.md"
echo "❓ Issues: https://github.com/your-repo/claude-os/issues"
echo ""
