#!/bin/bash
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                        Claude OS Installer                                 ║
# ║                                                                           ║
# ║  Beautiful, unified setup for Claude's AI memory system                   ║
# ║  Works on macOS and Linux                                                 ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

set -e

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

VERSION="2.1.0"
CLAUDE_OS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_CLAUDE_DIR="${HOME}/.claude"
TEMPLATES_DIR="${CLAUDE_OS_DIR}/templates"

# Default model choices
DEFAULT_LLM_MODEL="llama3.2:3b"           # Lite model - faster download, works on most machines
DEFAULT_EMBED_MODEL="nomic-embed-text"    # Best local embedding model
FULL_LLM_MODEL="llama3.1:8b"              # Full model - better quality

# ═══════════════════════════════════════════════════════════════════════════
# COLORS & STYLING
# ═══════════════════════════════════════════════════════════════════════════

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
WHITE='\033[1;37m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

# Box drawing characters
BOX_TL="╭"
BOX_TR="╮"
BOX_BL="╰"
BOX_BR="╯"
BOX_H="─"
BOX_V="│"

# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

# Print a styled box
print_box() {
    local title="$1"
    local width=60
    local padding=$(( (width - ${#title} - 2) / 2 ))

    echo ""
    echo -e "${CYAN}${BOX_TL}$(printf '%*s' "$width" | tr ' ' "$BOX_H")${BOX_TR}${NC}"
    echo -e "${CYAN}${BOX_V}${NC}$(printf '%*s' "$padding")${BOLD}${WHITE}$title${NC}$(printf '%*s' "$((width - padding - ${#title}))") ${CYAN}${BOX_V}${NC}"
    echo -e "${CYAN}${BOX_BL}$(printf '%*s' "$width" | tr ' ' "$BOX_H")${BOX_BR}${NC}"
    echo ""
}

# Print a section header
print_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Animated spinner
spinner() {
    local pid=$1
    local message=$2
    local spin='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local i=0

    while kill -0 $pid 2>/dev/null; do
        i=$(( (i + 1) % 10 ))
        printf "\r${CYAN}  ${spin:$i:1}${NC} ${message}"
        sleep 0.1
    done
    printf "\r"
}

# Success message
success() {
    echo -e "${GREEN}  ✓${NC} $1"
}

# Warning message
warn() {
    echo -e "${YELLOW}  ⚠${NC} $1"
}

# Error message
error() {
    echo -e "${RED}  ✗${NC} $1"
}

# Info message
info() {
    echo -e "${CYAN}  ℹ${NC} $1"
}

# Progress bar
progress_bar() {
    local current=$1
    local total=$2
    local width=40
    local percentage=$((current * 100 / total))
    local filled=$((current * width / total))
    local empty=$((width - filled))

    printf "\r  ${CYAN}["
    printf "%${filled}s" | tr ' ' '█'
    printf "%${empty}s" | tr ' ' '░'
    printf "]${NC} ${percentage}%%"
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        PKG_MANAGER="brew"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        if command -v apt-get &> /dev/null; then
            PKG_MANAGER="apt"
        elif command -v dnf &> /dev/null; then
            PKG_MANAGER="dnf"
        elif command -v yum &> /dev/null; then
            PKG_MANAGER="yum"
        elif command -v pacman &> /dev/null; then
            PKG_MANAGER="pacman"
        else
            PKG_MANAGER="unknown"
        fi
    else
        OS="unknown"
        PKG_MANAGER="unknown"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# BANNER
# ═══════════════════════════════════════════════════════════════════════════

show_banner() {
    clear
    echo ""
    echo -e "${CYAN}"
    cat << 'EOF'
     ██████╗██╗      █████╗ ██╗   ██╗██████╗ ███████╗     ██████╗ ███████╗
    ██╔════╝██║     ██╔══██╗██║   ██║██╔══██╗██╔════╝    ██╔═══██╗██╔════╝
    ██║     ██║     ███████║██║   ██║██║  ██║█████╗      ██║   ██║███████╗
    ██║     ██║     ██╔══██║██║   ██║██║  ██║██╔══╝      ██║   ██║╚════██║
    ╚██████╗███████╗██║  ██║╚██████╔╝██████╔╝███████╗    ╚██████╔╝███████║
     ╚═════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝     ╚═════╝ ╚══════╝
EOF
    echo -e "${NC}"
    echo -e "${DIM}                    Your AI Memory System • v${VERSION}${NC}"
    echo ""
    echo -e "${WHITE}    Claude CLI + Claude OS = Invincible! 🚀${NC}"
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════
# PROVIDER SELECTION
# ═══════════════════════════════════════════════════════════════════════════

select_provider() {
    print_box "Choose Your Setup"

    echo -e "  ${WHITE}How would you like to power Claude OS?${NC}"
    echo ""
    echo -e "  ${CYAN}[1]${NC} ${GREEN}🏠 Local (Ollama)${NC}"
    echo -e "      ${DIM}Free, private, runs on your machine${NC}"
    echo -e "      ${DIM}Best for: Privacy-focused users, offline use${NC}"
    echo ""
    echo -e "  ${CYAN}[2]${NC} ${BLUE}☁️  Cloud (OpenAI)${NC}"
    echo -e "      ${DIM}Fast, no local resources needed${NC}"
    echo -e "      ${DIM}Best for: Quick setup, Linux servers${NC}"
    echo ""
    echo -e "  ${CYAN}[3]${NC} ${MAGENTA}🔧 Custom${NC}"
    echo -e "      ${DIM}I'll configure it myself${NC}"
    echo ""

    while true; do
        echo -ne "  ${WHITE}Enter choice [1-3]:${NC} "
        read -r choice
        case $choice in
            1) PROVIDER="local"; break ;;
            2) PROVIDER="openai"; break ;;
            3) PROVIDER="custom"; break ;;
            *) echo -e "  ${RED}Please enter 1, 2, or 3${NC}" ;;
        esac
    done
}

# ═══════════════════════════════════════════════════════════════════════════
# MODEL SIZE SELECTION (for local installs)
# ═══════════════════════════════════════════════════════════════════════════

select_model_size() {
    print_box "Choose Model Size"

    echo -e "  ${WHITE}Select your local model:${NC}"
    echo ""
    echo -e "  ${CYAN}[1]${NC} ${GREEN}💨 Lite${NC} ${DIM}(Recommended)${NC}"
    echo -e "      ${WHITE}llama3.2:3b${NC} - 2GB download, ~4GB RAM"
    echo -e "      ${DIM}Fast download, works on most machines${NC}"
    echo ""
    echo -e "  ${CYAN}[2]${NC} ${BLUE}🚀 Full${NC}"
    echo -e "      ${WHITE}llama3.1:8b${NC} - 4.7GB download, ~8GB RAM"
    echo -e "      ${DIM}Better quality, needs more resources${NC}"
    echo ""

    while true; do
        echo -ne "  ${WHITE}Enter choice [1-2]:${NC} "
        read -r choice
        case $choice in
            1) LLM_MODEL="$DEFAULT_LLM_MODEL"; break ;;
            2) LLM_MODEL="$FULL_LLM_MODEL"; break ;;
            *) echo -e "  ${RED}Please enter 1 or 2${NC}" ;;
        esac
    done

    EMBED_MODEL="$DEFAULT_EMBED_MODEL"
}

# ═══════════════════════════════════════════════════════════════════════════
# OPENAI CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

configure_openai() {
    print_box "OpenAI Configuration"

    echo -e "  ${WHITE}Enter your OpenAI API key:${NC}"
    echo -e "  ${DIM}(Get one at https://platform.openai.com/api-keys)${NC}"
    echo ""
    echo -ne "  ${WHITE}API Key:${NC} "
    read -rs OPENAI_API_KEY
    echo ""

    if [[ -z "$OPENAI_API_KEY" ]]; then
        error "API key cannot be empty"
        exit 1
    fi

    # Validate key format
    if [[ ! "$OPENAI_API_KEY" =~ ^sk- ]]; then
        warn "API key doesn't start with 'sk-' - are you sure it's correct?"
    fi

    echo ""
    success "API key saved"
}

# ═══════════════════════════════════════════════════════════════════════════
# PYTHON SETUP
# ═══════════════════════════════════════════════════════════════════════════

setup_python() {
    print_section "Setting Up Python Environment"

    # Find compatible Python
    PYTHON_CMD=""

    if command -v python3.12 &> /dev/null; then
        PYTHON_CMD="python3.12"
    elif command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
    elif command -v python3 &> /dev/null; then
        local ver=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
        if [[ "$ver" == "3.11" || "$ver" == "3.12" ]]; then
            PYTHON_CMD="python3"
        fi
    fi

    if [[ -z "$PYTHON_CMD" ]]; then
        error "Python 3.11 or 3.12 required"
        echo ""
        echo -e "  ${WHITE}Install Python:${NC}"
        echo -e "    macOS:  ${CYAN}brew install python@3.12${NC}"
        echo -e "    Ubuntu: ${CYAN}sudo apt install python3.12${NC}"
        echo -e "    Fedora: ${CYAN}sudo dnf install python3.12${NC}"
        exit 1
    fi

    local py_version=$($PYTHON_CMD --version | cut -d' ' -f2)
    success "Found Python $py_version"

    # Create virtual environment
    if [[ ! -d "${CLAUDE_OS_DIR}/venv" ]]; then
        info "Creating virtual environment..."
        $PYTHON_CMD -m venv "${CLAUDE_OS_DIR}/venv" &
        spinner $! "Creating virtual environment..."
        success "Virtual environment created"
    else
        success "Virtual environment exists"
    fi

    # Activate and install dependencies
    source "${CLAUDE_OS_DIR}/venv/bin/activate"

    info "Installing dependencies..."
    pip install --quiet --upgrade pip setuptools wheel 2>/dev/null &
    spinner $! "Upgrading pip..."

    pip install --quiet -r "${CLAUDE_OS_DIR}/requirements.txt" 2>/dev/null &
    spinner $! "Installing dependencies (this may take a minute)..."
    success "Dependencies installed"
}

# ═══════════════════════════════════════════════════════════════════════════
# OLLAMA SETUP
# ═══════════════════════════════════════════════════════════════════════════

setup_ollama() {
    print_section "Setting Up Ollama"

    # Check if Ollama is installed
    if command -v ollama &> /dev/null; then
        success "Ollama already installed"
    else
        info "Installing Ollama..."

        if [[ "$OS" == "macos" ]]; then
            if command -v brew &> /dev/null; then
                brew install ollama &>/dev/null &
                spinner $! "Installing via Homebrew..."
            else
                error "Homebrew required. Install from https://brew.sh"
                exit 1
            fi
        elif [[ "$OS" == "linux" ]]; then
            curl -fsSL https://ollama.ai/install.sh | sh &>/dev/null &
            spinner $! "Installing Ollama..."
        fi

        success "Ollama installed"
    fi

    # Start Ollama if not running
    if ! curl -s http://localhost:11434/api/tags &>/dev/null; then
        info "Starting Ollama..."

        if [[ "$OS" == "macos" ]]; then
            brew services start ollama &>/dev/null || ollama serve &>/dev/null &
        else
            ollama serve &>/dev/null &
        fi

        sleep 3

        if curl -s http://localhost:11434/api/tags &>/dev/null; then
            success "Ollama started"
        else
            warn "Ollama may need manual start: ollama serve"
        fi
    else
        success "Ollama is running"
    fi

    # Download models
    echo ""
    info "Downloading AI models..."
    echo ""

    # Download LLM model
    if curl -s http://localhost:11434/api/tags | grep -q "\"name\":\"${LLM_MODEL}\""; then
        success "Model ${LLM_MODEL} ready"
    else
        echo -e "  ${CYAN}Downloading ${LLM_MODEL}...${NC}"
        echo -e "  ${DIM}(This may take a few minutes on first install)${NC}"
        ollama pull "$LLM_MODEL" 2>&1 | while read line; do
            if [[ "$line" =~ ([0-9]+)% ]]; then
                progress_bar "${BASH_REMATCH[1]}" 100
            fi
        done
        echo ""
        success "Model ${LLM_MODEL} downloaded"
    fi

    # Download embedding model
    if curl -s http://localhost:11434/api/tags | grep -q "\"name\":\"${EMBED_MODEL}\""; then
        success "Model ${EMBED_MODEL} ready"
    else
        echo -e "  ${CYAN}Downloading ${EMBED_MODEL}...${NC}"
        ollama pull "$EMBED_MODEL" 2>&1 | while read line; do
            if [[ "$line" =~ ([0-9]+)% ]]; then
                progress_bar "${BASH_REMATCH[1]}" 100
            fi
        done
        echo ""
        success "Model ${EMBED_MODEL} downloaded"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# REDIS SETUP
# ═══════════════════════════════════════════════════════════════════════════

setup_redis() {
    print_section "Setting Up Redis"

    if command -v redis-cli &> /dev/null; then
        success "Redis already installed"
    else
        info "Installing Redis..."

        if [[ "$OS" == "macos" ]]; then
            brew install redis &>/dev/null &
            spinner $! "Installing via Homebrew..."
        elif [[ "$OS" == "linux" ]]; then
            case "$PKG_MANAGER" in
                apt) sudo apt-get update -qq && sudo apt-get install -y -qq redis-server &>/dev/null & ;;
                dnf) sudo dnf install -y -q redis &>/dev/null & ;;
                yum) sudo yum install -y -q redis &>/dev/null & ;;
                pacman) sudo pacman -S --noconfirm --quiet redis &>/dev/null & ;;
            esac
            spinner $! "Installing Redis..."
        fi

        success "Redis installed"
    fi

    # Start Redis if not running
    if redis-cli ping &>/dev/null; then
        success "Redis is running"
    else
        info "Starting Redis..."

        if [[ "$OS" == "macos" ]]; then
            brew services start redis &>/dev/null || true
        else
            redis-server --daemonize yes &>/dev/null || true
        fi

        sleep 1

        if redis-cli ping &>/dev/null; then
            success "Redis started"
        else
            warn "Redis may need manual start"
        fi
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# CLAUDE CODE INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════

setup_claude_integration() {
    print_section "Integrating with Claude Code"

    # Create directories
    mkdir -p "${USER_CLAUDE_DIR}/commands"
    mkdir -p "${USER_CLAUDE_DIR}/skills"
    mkdir -p "${USER_CLAUDE_DIR}/mcp-servers"
    mkdir -p "${CLAUDE_OS_DIR}/data"
    mkdir -p "${CLAUDE_OS_DIR}/logs"

    success "Created directories"

    # Symlink commands
    local cmd_count=0
    for cmd_file in "${TEMPLATES_DIR}"/commands/*.md; do
        if [[ -f "$cmd_file" ]]; then
            local cmd_name=$(basename "$cmd_file")
            local dest="${USER_CLAUDE_DIR}/commands/${cmd_name}"
            rm -f "$dest" 2>/dev/null
            ln -s "$cmd_file" "$dest"
            ((cmd_count++))
        fi
    done
    success "Linked ${cmd_count} commands"

    # Symlink skills
    local skill_count=0
    for skill_dir in "${TEMPLATES_DIR}"/skills/*/; do
        if [[ -d "$skill_dir" ]]; then
            local skill_name=$(basename "$skill_dir")
            local dest="${USER_CLAUDE_DIR}/skills/${skill_name}"
            rm -rf "$dest" 2>/dev/null
            ln -s "$skill_dir" "$dest"
            ((skill_count++))
        fi
    done
    success "Linked ${skill_count} skills"

    # Configure MCP server in settings.json
    local settings_file="${USER_CLAUDE_DIR}/settings.json"

    if [[ ! -f "$settings_file" ]]; then
        echo "{}" > "$settings_file"
    fi

    python3 << EOF
import json
import os

settings_file = "$settings_file"
claude_os_dir = "$CLAUDE_OS_DIR"

try:
    with open(settings_file, 'r') as f:
        settings = json.load(f)
except:
    settings = {}

if 'mcpServers' not in settings:
    settings['mcpServers'] = {}

settings['mcpServers']['code-forge'] = {
    "command": os.path.join(claude_os_dir, "venv", "bin", "python3"),
    "args": [os.path.join(claude_os_dir, "mcp_server", "claude_code_mcp.py")],
    "env": {
        "CLAUDE_OS_API": "http://localhost:8051"
    }
}

with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)
EOF

    success "Configured MCP server"
}

# ═══════════════════════════════════════════════════════════════════════════
# CREATE CONFIGURATION FILE
# ═══════════════════════════════════════════════════════════════════════════

create_config() {
    print_section "Creating Configuration"

    local config_file="${CLAUDE_OS_DIR}/.env"

    cat > "$config_file" << EOF
# Claude OS Configuration
# Generated by setup-claude-os.sh on $(date)

# Provider: local or openai
CLAUDE_OS_PROVIDER=${PROVIDER}

# LLM Settings
LLM_MODEL=${LLM_MODEL:-gpt-4o-mini}
EMBEDDING_MODEL=${EMBED_MODEL:-text-embedding-3-small}

# Ollama Settings (for local provider)
OLLAMA_HOST=http://localhost:11434

# OpenAI Settings (for cloud provider)
OPENAI_API_KEY=${OPENAI_API_KEY:-}

# Server Settings
CLAUDE_OS_HOST=0.0.0.0
CLAUDE_OS_PORT=8051

# Database
CLAUDE_OS_DB_PATH=./data/claude-os.db
EOF

    success "Created configuration file"

    # Also create the JSON config for backwards compatibility
    cat > "${CLAUDE_OS_DIR}/claude-os-config.json" << EOF
{
  "provider": "${PROVIDER}",
  "llm_model": "${LLM_MODEL:-gpt-4o-mini}",
  "embed_model": "${EMBED_MODEL:-text-embedding-3-small}",
  "version": "${VERSION}",
  "installed_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF
}

# ═══════════════════════════════════════════════════════════════════════════
# COMPLETION
# ═══════════════════════════════════════════════════════════════════════════

show_completion() {
    echo ""
    echo -e "${GREEN}"
    cat << 'EOF'
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║   ✨  Claude OS is ready!  ✨                                     ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"

    echo -e "  ${WHITE}What was set up:${NC}"
    echo ""
    [[ -d "${CLAUDE_OS_DIR}/venv" ]] && echo -e "    ${GREEN}✓${NC} Python environment"
    [[ "$PROVIDER" == "local" ]] && echo -e "    ${GREEN}✓${NC} Ollama with ${LLM_MODEL}"
    [[ "$PROVIDER" == "local" ]] && echo -e "    ${GREEN}✓${NC} Embedding model (${EMBED_MODEL})"
    [[ "$PROVIDER" == "openai" ]] && echo -e "    ${GREEN}✓${NC} OpenAI API configured"
    command -v redis-cli &>/dev/null && echo -e "    ${GREEN}✓${NC} Redis cache"
    [[ -d "${USER_CLAUDE_DIR}/commands" ]] && echo -e "    ${GREEN}✓${NC} Claude Code commands"
    [[ -d "${USER_CLAUDE_DIR}/skills" ]] && echo -e "    ${GREEN}✓${NC} Claude Code skills"
    [[ -f "${USER_CLAUDE_DIR}/settings.json" ]] && echo -e "    ${GREEN}✓${NC} MCP server configured"

    echo ""
    echo -e "  ${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  ${WHITE}Next Steps:${NC}"
    echo ""
    echo -e "  ${CYAN}1.${NC} Start Claude OS:"
    echo -e "     ${DIM}./start_all_services.sh${NC}"
    echo ""
    echo -e "  ${CYAN}2.${NC} In your project, initialize Claude OS:"
    echo -e "     ${DIM}/claude-os-init${NC}"
    echo ""
    echo -e "  ${CYAN}3.${NC} Start a session:"
    echo -e "     ${DIM}/claude-os-session start \"working on feature X\"${NC}"
    echo ""
    echo -e "  ${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  ${DIM}Documentation: README.md${NC}"
    echo -e "  ${DIM}Issues: https://github.com/brobertsaz/claude-os/issues${NC}"
    echo ""
    echo -e "  ${WHITE}Happy coding! 🚀${NC}"
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

main() {
    # Detect OS first
    detect_os

    # Show banner
    show_banner

    # Provider selection
    select_provider

    # Provider-specific setup
    if [[ "$PROVIDER" == "local" ]]; then
        select_model_size
    elif [[ "$PROVIDER" == "openai" ]]; then
        configure_openai
        LLM_MODEL="gpt-4o-mini"
        EMBED_MODEL="text-embedding-3-small"
    elif [[ "$PROVIDER" == "custom" ]]; then
        info "Custom setup - you'll need to configure .env manually"
        LLM_MODEL=""
        EMBED_MODEL=""
    fi

    # Common setup
    setup_python

    # Provider-specific dependencies
    if [[ "$PROVIDER" == "local" ]]; then
        setup_ollama
    fi

    # Optional: Redis (useful for caching)
    setup_redis

    # Claude Code integration
    setup_claude_integration

    # Create configuration
    create_config

    # Show completion
    show_completion
}

# Run main
main "$@"
