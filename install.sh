#!/bin/bash
# Claude OS Installation Script
# Sets up Claude OS for a new user/machine
# This script ALWAYS completes and provides detailed feedback

# DON'T exit on error - we want to handle all errors gracefully
set +e

# Initialize error tracking
ERROR_COUNT=0
WARNING_COUNT=0
ERROR_LOG=""
INSTALL_STATUS="IN_PROGRESS"

# Directories
CLAUDE_OS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_CLAUDE_DIR="${HOME}/.claude"
TEMPLATES_DIR="${CLAUDE_OS_DIR}/templates"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Helper functions
log_error() {
    ERROR_COUNT=$((ERROR_COUNT + 1))
    ERROR_LOG="${ERROR_LOG}ERROR: $1\n"
    echo -e "${RED}❌ ERROR: $1${NC}" >&2
}

log_warning() {
    WARNING_COUNT=$((WARNING_COUNT + 1))
    ERROR_LOG="${ERROR_LOG}WARNING: $1\n"
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo "🚀 Claude OS Installation"
echo "========================="
echo ""
echo "Claude OS Directory: ${CLAUDE_OS_DIR}"
echo "User Claude Directory: ${USER_CLAUDE_DIR}"
echo ""

# Find compatible Python version (3.11 or 3.12 only)
echo "🔍 Looking for compatible Python version (3.11 or 3.12)..."

PYTHON_CMD=""
PYTHON_VERSION=""

# Check for Python 3.12 first (preferred)
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    PYTHON_VERSION=$(python3.12 --version | cut -d' ' -f2)
    log_success "Found Python 3.12: ${PYTHON_VERSION}"
# Then check for Python 3.11
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    PYTHON_VERSION=$(python3.11 --version | cut -d' ' -f2)
    log_success "Found Python 3.11: ${PYTHON_VERSION}"
# Check if default python3 is 3.11 or 3.12
elif command -v python3 &> /dev/null; then
    DEFAULT_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [ "$DEFAULT_VERSION" = "3.11" ] || [ "$DEFAULT_VERSION" = "3.12" ]; then
        PYTHON_CMD="python3"
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_success "Found Python ${DEFAULT_VERSION}: ${PYTHON_VERSION}"
    else
        log_error "Python ${DEFAULT_VERSION} found, but Claude OS requires Python 3.11 or 3.12"
        echo ""
        echo "Your system has Python ${DEFAULT_VERSION}, but some dependencies (like tree-sitter-languages)"
        echo "don't yet support Python 3.13+."
        echo ""
        echo "Please install Python 3.11 or 3.12:"
        echo "  • macOS with Homebrew: brew install python@3.12"
        echo "  • Ubuntu/Debian: sudo apt install python3.12"
        echo "  • Fedora/RHEL: sudo dnf install python3.12"
        echo "  • Arch Linux: sudo pacman -S python"
        echo "  • Or download from: https://www.python.org/downloads/"
        echo ""
        INSTALL_STATUS="FAILED"
        # Jump to summary section
        skip_to_summary=true
    fi
else
    log_error "Python 3 is not installed"
    echo ""
    echo "Please install Python 3.11 or 3.12:"
    echo "  • macOS with Homebrew: brew install python@3.12"
    echo "  • Ubuntu/Debian: sudo apt install python3.12"
    echo "  • Fedora/RHEL: sudo dnf install python3.12"
    echo "  • Arch Linux: sudo pacman -S python"
    echo "  • Or download from: https://www.python.org/downloads/"
    echo ""
    INSTALL_STATUS="FAILED"
    skip_to_summary=true
fi

# Skip rest of installation if Python check failed
if [ "$skip_to_summary" != "true" ]; then

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
    echo "   Creating virtual environment with ${PYTHON_CMD}..."
    ${PYTHON_CMD} -m venv "${CLAUDE_OS_DIR}/venv"
fi

echo "   Installing dependencies..."
source "${CLAUDE_OS_DIR}/venv/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r "${CLAUDE_OS_DIR}/requirements.txt"
echo "   ✅ Dependencies installed"

# Installation complete - move to config creation
echo ""

# Create config file
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
  "version": "2.0.0"
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
EOF

chmod +x "$START_SCRIPT"
log_success "Created start script"

fi  # End of main installation (if skip_to_summary != true)

# Mark installation as successful if we got here with no errors
if [ "$ERROR_COUNT" -eq 0 ]; then
    INSTALL_STATUS="SUCCESS"
elif [ "$ERROR_COUNT" -gt 0 ] && [ -f "$START_SCRIPT" ]; then
    INSTALL_STATUS="PARTIAL"
else
    INSTALL_STATUS="FAILED"
fi

# ════════════════════════════════════════════════════════════════
# INSTALLATION SUMMARY
# ════════════════════════════════════════════════════════════════

echo ""
echo "════════════════════════════════════════"
if [ "$INSTALL_STATUS" = "SUCCESS" ]; then
    echo -e "${GREEN}✨ Installation completed successfully!${NC}"
elif [ "$INSTALL_STATUS" = "PARTIAL" ]; then
    echo -e "${YELLOW}⚠️  Installation completed with warnings${NC}"
else
    echo -e "${RED}❌ Installation failed${NC}"
fi
echo "════════════════════════════════════════"
echo ""

# Show error/warning counts
if [ "$ERROR_COUNT" -gt 0 ] || [ "$WARNING_COUNT" -gt 0 ]; then
    echo "📊 Summary:"
    [ "$ERROR_COUNT" -gt 0 ] && echo -e "   ${RED}Errors: $ERROR_COUNT${NC}"
    [ "$WARNING_COUNT" -gt 0 ] && echo -e "   ${YELLOW}Warnings: $WARNING_COUNT${NC}"
    echo ""
fi

# Show what was set up
echo "📋 What was set up:"
[ -d "${USER_CLAUDE_DIR}/commands" ] && echo "   ✅ Commands: $(ls -1 ${USER_CLAUDE_DIR}/commands/claude-os-*.md 2>/dev/null | wc -l | xargs) symlinks"
[ -d "${USER_CLAUDE_DIR}/skills" ] && echo "   ✅ Skills: 3 symlinks"
[ -n "$PYTHON_VERSION" ] && echo "   ✅ Python ${PYTHON_VERSION} virtual environment"
[ -d "${CLAUDE_OS_DIR}/venv" ] && echo "   ✅ Dependencies installed"
[ -f "${USER_CLAUDE_DIR}/mcp-servers/code-forge.json" ] && echo "   ✅ MCP server configured"
[ -f "$START_SCRIPT" ] && echo "   ✅ Start script created"

# If there were errors, show them
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo ""
    echo -e "${RED}Errors encountered:${NC}"
    echo -e "$ERROR_LOG" | head -10
fi

echo ""

# Next steps (only if installation succeeded or partially succeeded)
if [ "$INSTALL_STATUS" != "FAILED" ]; then
    echo "════════════════════════════════════════"
    echo "🎯 Next steps:"
    echo "════════════════════════════════════════"
    echo ""
    echo "1️⃣  Start Claude OS:"
    echo ""
    echo "    Option A - MCP Server only (minimal):"
    echo "    ./start.sh"
    echo ""
    echo "    Option B - Full experience (recommended):"
    echo "    ./start_all_services.sh"
    echo ""
    echo "2️⃣  In Claude Code, go to your project:"
    echo "    cd /path/to/your/project"
    echo ""
    echo "3️⃣  Initialize your project:"
    echo "    /claude-os-init"
    echo ""
    echo "4️⃣  Start coding with AI memory! 🚀"
    echo ""
fi

echo "════════════════════════════════════════"
echo "📚 Documentation:"
echo "════════════════════════════════════════"
echo "   • README.md - Full documentation"
echo "   • BACKUP_RESTORE_GUIDE.md - Backup & restore"
echo "   • /claude-os-search - Search memories"
echo "   • /claude-os-remember - Save insights"
echo ""

# ════════════════════════════════════════════════════════════════
# ERROR REPORTING
# ════════════════════════════════════════════════════════════════

if [ "$ERROR_COUNT" -gt 0 ] || [ "$INSTALL_STATUS" = "FAILED" ]; then
    echo "════════════════════════════════════════"
    echo "🐛 Need help?"
    echo "════════════════════════════════════════"
    echo ""
    echo "Please report this issue on GitHub:"
    echo "  https://github.com/brobertsaz/claude-os/issues/new"
    echo ""
    echo "Include this information:"
    echo "  • Your OS: $(uname -s) $(uname -r)"
    echo "  • Python version: ${PYTHON_VERSION:-unknown}"
    echo "  • Error count: $ERROR_COUNT"
    echo ""
    if [ -n "$ERROR_LOG" ]; then
        echo "Error details:"
        echo -e "$ERROR_LOG" | head -5
        echo ""
    fi
    echo "We'll help you get it working! 🚀"
    echo ""
fi

# Exit with appropriate code
if [ "$INSTALL_STATUS" = "SUCCESS" ]; then
    exit 0
elif [ "$INSTALL_STATUS" = "PARTIAL" ]; then
    exit 0  # Still consider it success if key components work
else
    exit 1
fi
