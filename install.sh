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

# AI Model Configuration
echo ""
echo "🤖 AI Model Configuration (for Agent-OS)"
echo "========================================="
echo ""
echo "Agent-OS can use AI for advanced features like spec generation."
echo "You have two options:"
echo ""
echo "  1. Local Ollama (FREE, requires 8GB+ RAM)"
echo "  2. OpenAI API (Paid, ~\$0.02/request, works on any machine)"
echo "  3. Skip for now (can configure later)"
echo ""
read -p "Which would you like to use? (1/2/3): " ai_choice

AI_PROVIDER="none"
if [ "$ai_choice" = "1" ]; then
    echo ""
    echo "📦 Checking for Ollama..."
    if command -v ollama &> /dev/null; then
        echo "   ✅ Ollama found"
        AI_PROVIDER="ollama"
        # Check if llama2 model is available
        if ollama list | grep -q "llama2"; then
            echo "   ✅ llama2 model available"
        else
            echo "   📥 Pulling llama2 model (this may take a few minutes)..."
            ollama pull llama2
            echo "   ✅ llama2 model ready"
        fi
    else
        echo "   ❌ Ollama not found"
        echo ""
        echo "   To install Ollama:"
        echo "   1. Visit: https://ollama.ai"
        echo "   2. Download and install"
        echo "   3. Run: ollama pull llama2"
        echo ""
        read -p "   Press enter to continue (you can configure Ollama later)..."
        AI_PROVIDER="none"
    fi
elif [ "$ai_choice" = "2" ]; then
    echo ""
    echo "🔑 OpenAI API Configuration"
    echo ""
    read -p "Enter your OpenAI API key: " openai_key
    if [ -n "$openai_key" ]; then
        # Create or append to .env file
        ENV_FILE="${CLAUDE_OS_DIR}/.env"
        if grep -q "OPENAI_API_KEY" "$ENV_FILE" 2>/dev/null; then
            # Update existing key
            sed -i.bak "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$openai_key/" "$ENV_FILE"
        else
            # Add new key
            echo "OPENAI_API_KEY=$openai_key" >> "$ENV_FILE"
        fi
        echo "   ✅ API key saved to .env"
        AI_PROVIDER="openai"
    else
        echo "   ⚠️  No API key provided, skipping"
        AI_PROVIDER="none"
    fi
else
    echo "   ⏭️  Skipping AI configuration (can set up later)"
    AI_PROVIDER="none"
fi

# Agent-OS Integration (Optional)
echo ""
echo "🎯 Agent-OS Integration (Optional)"
echo "===================================="
echo ""
echo "Agent-OS by Builder Methods (CasJam Media LLC) provides 8 specialized"
echo "agents for spec-driven development workflows:"
echo ""
echo "  • spec-initializer    • spec-shaper"
echo "  • spec-writer         • tasks-list-creator"
echo "  • implementer         • implementation-verifier"
echo "  • spec-verifier       • product-planner"
echo ""
echo "Agent-OS is MIT licensed and created by Builder Methods."
echo "Repository: https://github.com/builder-methods/agent-os"
echo ""
read -p "Install Agent-OS? (y/n): " install_agent_os

AGENT_OS_INSTALLED="no"
if [ "$install_agent_os" = "y" ] || [ "$install_agent_os" = "Y" ]; then
    echo ""
    echo "📦 Installing Agent-OS..."
    AGENT_OS_DIR="${USER_CLAUDE_DIR}/agents/agent-os"

    # Create agents directory if needed
    mkdir -p "${USER_CLAUDE_DIR}/agents"

    # Clone or update Agent-OS
    if [ -d "$AGENT_OS_DIR" ]; then
        echo "   📁 Agent-OS directory exists, updating..."
        cd "$AGENT_OS_DIR"
        git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || echo "   ⚠️  Could not update (not a git repo or no connection)"
        cd "$CLAUDE_OS_DIR"
    else
        echo "   📥 Cloning Agent-OS from GitHub..."
        git clone https://github.com/builder-methods/agent-os.git "$AGENT_OS_DIR" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "   ✅ Agent-OS installed successfully"
            AGENT_OS_INSTALLED="yes"
        else
            echo "   ❌ Failed to clone Agent-OS (check internet connection)"
            echo "   You can install it manually later:"
            echo "   git clone https://github.com/builder-methods/agent-os.git ~/.claude/agents/agent-os"
            AGENT_OS_INSTALLED="failed"
        fi
    fi

    if [ -d "$AGENT_OS_DIR" ]; then
        AGENT_OS_INSTALLED="yes"
    fi
else
    echo "   ⏭️  Skipping Agent-OS installation"
    echo ""
    echo "   You can install it later with:"
    echo "   git clone https://github.com/builder-methods/agent-os.git ~/.claude/agents/agent-os"
fi

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
  "ai_provider": "${AI_PROVIDER}",
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
if [ "$AGENT_OS_INSTALLED" = "yes" ]; then
    echo "   ✅ Agent-OS installed (8 agents by Builder Methods)"
else
    echo "   ⏭️  Agent-OS not installed (optional)"
fi
echo "   ✅ Python virtual environment created"
echo "   ✅ Dependencies installed"
echo "   ✅ MCP server configured"
echo "   ✅ AI provider: ${AI_PROVIDER}"
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
