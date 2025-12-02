#!/bin/bash
# Claude OS Uninstall Script
# Removes all Claude OS components from your system

set -e

# Directories
CLAUDE_OS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_CLAUDE_DIR="${HOME}/.claude"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "════════════════════════════════════════"
echo "🗑️  Claude OS Uninstaller"
echo "════════════════════════════════════════"
echo ""

# Confirm uninstall
echo -e "${YELLOW}This will remove:${NC}"
echo "  • Command symlinks from ~/.claude/commands/"
echo "  • Skill symlinks from ~/.claude/skills/"
echo "  • MCP server config from ~/.claude/mcp-servers/"
echo "  • Python virtual environment (venv/)"
echo "  • Local database (data/claude-os.db)"
echo "  • Config files"
echo ""
echo -e "${BLUE}NOTE: This does NOT uninstall Ollama or Redis.${NC}"
echo ""

read -p "Are you sure you want to uninstall Claude OS? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

echo ""
echo "🧹 Removing Claude OS components..."
echo ""

# Remove command symlinks
echo "📁 Removing command symlinks..."
for cmd_file in "${USER_CLAUDE_DIR}"/commands/claude-os-*.md; do
    if [ -L "$cmd_file" ]; then
        rm -f "$cmd_file"
        echo "   ✅ Removed: $(basename "$cmd_file")"
    fi
done

# Remove skill symlinks
echo ""
echo "📁 Removing skill symlinks..."
for skill in "initialize-project" "remember-this" "memory"; do
    skill_path="${USER_CLAUDE_DIR}/skills/${skill}"
    if [ -L "$skill_path" ]; then
        rm -f "$skill_path"
        echo "   ✅ Removed: ${skill}/"
    fi
done

# Remove MCP server config
echo ""
echo "📡 Removing MCP server config..."
MCP_CONFIG="${USER_CLAUDE_DIR}/mcp-servers/code-forge.json"
if [ -f "$MCP_CONFIG" ]; then
    rm -f "$MCP_CONFIG"
    echo "   ✅ Removed: code-forge.json"
fi

# Ask about data removal
echo ""
echo -e "${YELLOW}Do you want to delete your Claude OS data (knowledge bases, memories)?${NC}"
read -p "Delete data? (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Remove database
    if [ -d "${CLAUDE_OS_DIR}/data" ]; then
        rm -rf "${CLAUDE_OS_DIR}/data"
        echo "   ✅ Removed: data/"
    fi
fi

# Remove virtual environment
echo ""
echo "🐍 Removing Python virtual environment..."
if [ -d "${CLAUDE_OS_DIR}/venv" ]; then
    rm -rf "${CLAUDE_OS_DIR}/venv"
    echo "   ✅ Removed: venv/"
fi

# Also check for alternative venv directories
for venv_dir in "venv_py312" "venv_test"; do
    if [ -d "${CLAUDE_OS_DIR}/${venv_dir}" ]; then
        rm -rf "${CLAUDE_OS_DIR}/${venv_dir}"
        echo "   ✅ Removed: ${venv_dir}/"
    fi
done

# Remove config files
echo ""
echo "⚙️  Removing config files..."
for config_file in "claude-os-config.json" "claude-os-state.json" "claude-os-triggers.json"; do
    if [ -f "${CLAUDE_OS_DIR}/${config_file}" ]; then
        rm -f "${CLAUDE_OS_DIR}/${config_file}"
        echo "   ✅ Removed: ${config_file}"
    fi
done

# Remove logs
if [ -d "${CLAUDE_OS_DIR}/logs" ]; then
    rm -rf "${CLAUDE_OS_DIR}/logs"
    echo "   ✅ Removed: logs/"
fi

# Remove htmlcov (test coverage)
if [ -d "${CLAUDE_OS_DIR}/htmlcov" ]; then
    rm -rf "${CLAUDE_OS_DIR}/htmlcov"
    echo "   ✅ Removed: htmlcov/"
fi

# Remove __pycache__ directories
echo ""
echo "🧹 Cleaning up Python cache..."
find "${CLAUDE_OS_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "${CLAUDE_OS_DIR}" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
echo "   ✅ Removed Python cache directories"

echo ""
echo "════════════════════════════════════════"
echo -e "${GREEN}✨ Claude OS has been uninstalled!${NC}"
echo "════════════════════════════════════════"
echo ""
echo "The claude-os directory itself was NOT deleted."
echo "To completely remove, run:"
echo ""
echo "  rm -rf ${CLAUDE_OS_DIR}"
echo ""
echo "To reinstall later:"
echo "  cd ${CLAUDE_OS_DIR}"
echo "  ./install.sh"
echo ""

# Optional: Remove Ollama and Redis
echo "════════════════════════════════════════"
echo "📦 Optional: External Dependencies"
echo "════════════════════════════════════════"
echo ""
echo "Claude OS installed but did NOT remove:"
echo ""
echo "  • Ollama - Local AI runtime"
echo "    To uninstall: https://ollama.ai/docs/uninstall"
echo ""
echo "  • Redis - Caching service"
echo "    macOS: brew uninstall redis"
echo "    Linux: sudo apt remove redis-server"
echo ""
