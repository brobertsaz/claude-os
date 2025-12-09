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

VERSION="2.2.0"
CLAUDE_OS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_CLAUDE_DIR="${HOME}/.claude"
TEMPLATES_DIR="${CLAUDE_OS_DIR}/templates"

# Mode flags
DRY_RUN=false
DEMO_MODE=false
FORCE_MODE=false

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
# GUM DETECTION & SETUP
# ═══════════════════════════════════════════════════════════════════════════
# Gum (https://github.com/charmbracelet/gum) provides beautiful interactive
# prompts. If available, we use it. Otherwise, we fall back to bash.

HAS_GUM=false
if command -v gum &> /dev/null; then
    HAS_GUM=true
fi

# Offer to install gum for enhanced experience
offer_gum_install() {
    if [[ "$HAS_GUM" == "true" ]]; then
        return
    fi

    echo ""
    echo -e "${CYAN}┌────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│${NC}  ${WHITE}✨ Enhanced installer available!${NC}                              ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}                                                                ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}  ${DIM}Install 'gum' for a more beautiful experience with${NC}            ${CYAN}│${NC}"
    echo -e "${CYAN}│${NC}  ${DIM}interactive menus and smooth animations.${NC}                      ${CYAN}│${NC}"
    echo -e "${CYAN}└────────────────────────────────────────────────────────────────┘${NC}"
    echo ""
    echo -ne "  ${WHITE}Install gum? [y/N]:${NC} "
    read -r install_gum

    if [[ "$install_gum" =~ ^[Yy]$ ]]; then
        echo ""
        info "Installing gum..."

        if [[ "$OS" == "macos" ]]; then
            brew install gum &>/dev/null &
            spinner $! "Installing gum via Homebrew..."
        elif [[ "$OS" == "linux" ]]; then
            # Try various package managers
            if [[ "$PKG_MANAGER" == "apt" ]]; then
                sudo mkdir -p /etc/apt/keyrings
                curl -fsSL https://repo.charm.sh/apt/gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/charm.gpg 2>/dev/null
                echo "deb [signed-by=/etc/apt/keyrings/charm.gpg] https://repo.charm.sh/apt/ * *" | sudo tee /etc/apt/sources.list.d/charm.list > /dev/null
                sudo apt update -qq && sudo apt install -y -qq gum &>/dev/null &
                spinner $! "Installing gum via apt..."
            elif command -v go &> /dev/null; then
                go install github.com/charmbracelet/gum@latest &>/dev/null &
                spinner $! "Installing gum via go..."
            else
                warn "Could not auto-install gum. Install manually: https://github.com/charmbracelet/gum"
                return
            fi
        fi

        if command -v gum &> /dev/null; then
            HAS_GUM=true
            success "Gum installed! You'll get the premium experience ✨"
        else
            warn "Gum installation may have failed. Continuing with standard installer."
        fi
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# GUM WRAPPER FUNCTIONS (with bash fallback)
# ═══════════════════════════════════════════════════════════════════════════

# Choose from a list of options
# Usage: choice=$(gum_choose "Option 1" "Option 2" "Option 3")
gum_choose() {
    if [[ "$HAS_GUM" == "true" ]]; then
        gum choose --cursor.foreground="#00FFFF" --selected.foreground="#00FF00" "$@"
    else
        # Bash fallback
        local options=("$@")
        local i=1
        for opt in "${options[@]}"; do
            echo -e "  ${CYAN}[$i]${NC} $opt"
            ((i++))
        done
        echo ""
        while true; do
            echo -ne "  ${WHITE}Enter choice [1-${#options[@]}]:${NC} "
            read -r choice
            if [[ "$choice" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice <= ${#options[@]} )); then
                echo "${options[$((choice-1))]}"
                return
            fi
            echo -e "  ${RED}Please enter a number between 1 and ${#options[@]}${NC}"
        done
    fi
}

# Confirm yes/no
# Usage: if gum_confirm "Are you sure?"; then ...
gum_confirm() {
    local prompt="$1"
    if [[ "$HAS_GUM" == "true" ]]; then
        gum confirm --prompt.foreground="#FFFFFF" "$prompt"
    else
        echo -ne "  ${WHITE}$prompt [y/N]:${NC} "
        read -r response
        [[ "$response" =~ ^[Yy]$ ]]
    fi
}

# Get text input
# Usage: value=$(gum_input "Enter value" "placeholder")
gum_input() {
    local prompt="$1"
    local placeholder="$2"
    if [[ "$HAS_GUM" == "true" ]]; then
        gum input --placeholder "$placeholder" --prompt "$prompt: " --prompt.foreground="#00FFFF"
    else
        echo -ne "  ${WHITE}$prompt:${NC} "
        read -r value
        echo "$value"
    fi
}

# Get password input (hidden)
# Usage: value=$(gum_password "Enter password")
gum_password() {
    local prompt="$1"
    if [[ "$HAS_GUM" == "true" ]]; then
        gum input --password --placeholder "••••••••••••••••" --prompt "$prompt: " --prompt.foreground="#00FFFF"
    else
        echo -ne "  ${WHITE}$prompt:${NC} "
        read -rs value
        echo ""
        echo "$value"
    fi
}

# Show a spinner while a command runs
# Usage: gum_spin "Message" command arg1 arg2
gum_spin() {
    local message="$1"
    shift
    if [[ "$HAS_GUM" == "true" ]]; then
        gum spin --spinner dot --title "$message" -- "$@"
    else
        "$@" &
        spinner $! "$message"
    fi
}

# Style text in a box
gum_style_box() {
    local text="$1"
    if [[ "$HAS_GUM" == "true" ]]; then
        gum style --border rounded --padding "1 2" --border-foreground "#00FFFF" "$text"
    else
        print_box "$text"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# ARGUMENT PARSING & MODES
# ═══════════════════════════════════════════════════════════════════════════

show_help() {
    echo ""
    echo -e "${CYAN}Claude OS Installer v${VERSION}${NC}"
    echo ""
    echo -e "${WHITE}Usage:${NC} ./setup-claude-os.sh [OPTIONS]"
    echo ""
    echo -e "${WHITE}Options:${NC}"
    echo -e "  ${CYAN}--help, -h${NC}      Show this help message"
    echo -e "  ${CYAN}--demo${NC}          Run interactive demo (no changes made)"
    echo -e "  ${CYAN}--dry-run${NC}       Show what would be done without doing it"
    echo -e "  ${CYAN}--force, -f${NC}     Skip confirmation prompts"
    echo -e "  ${CYAN}--version, -v${NC}   Show version number"
    echo ""
    echo -e "${WHITE}Examples:${NC}"
    echo -e "  ${DIM}./setup-claude-os.sh${NC}           # Normal installation"
    echo -e "  ${DIM}./setup-claude-os.sh --demo${NC}    # See the beautiful UI"
    echo -e "  ${DIM}./setup-claude-os.sh --dry-run${NC} # Preview changes"
    echo ""
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                exit 0
                ;;
            --demo)
                DEMO_MODE=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --force|-f)
                FORCE_MODE=true
                shift
                ;;
            --version|-v)
                echo "Claude OS Installer v${VERSION}"
                exit 0
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

# Run the interactive demo without making any changes
run_demo() {
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
    echo -e "${DIM}                    DEMO MODE - No changes will be made${NC}"
    echo ""

    if [[ "$HAS_GUM" != "true" ]]; then
        echo -e "${YELLOW}  ⚠ Gum not installed - showing bash fallback version${NC}"
        echo -e "${DIM}    Install gum for the full experience: brew install gum${NC}"
        echo ""
    fi

    sleep 1

    # Demo: Styled Box
    echo -e "${CYAN}━━━ Demo 1: Styled Boxes ━━━${NC}"
    if [[ "$HAS_GUM" == "true" ]]; then
        gum style --border rounded --padding "1 3" --border-foreground "#00FFFF" \
            "$(gum style --foreground "#FFFFFF" --bold "Welcome to Claude OS!")" \
            "" \
            "$(gum style --foreground "#888888" "Your AI Memory System")"
    else
        print_box "Welcome to Claude OS!"
    fi
    echo ""
    sleep 1

    # Demo: Choose
    echo -e "${CYAN}━━━ Demo 2: Interactive Selection ━━━${NC}"
    echo ""
    local choice
    if [[ "$HAS_GUM" == "true" ]]; then
        choice=$(gum choose --cursor.foreground="#00FFFF" --selected.foreground="#00FF00" \
            "🏠 Local (Ollama) - Free, private, runs on your machine" \
            "☁️  Cloud (OpenAI) - Fast, no local resources needed" \
            "🔧 Custom - I'll configure it myself")
    else
        echo -e "  ${CYAN}[1]${NC} 🏠 Local (Ollama) - Free, private"
        echo -e "  ${CYAN}[2]${NC} ☁️  Cloud (OpenAI) - Fast, no local resources"
        echo -e "  ${CYAN}[3]${NC} 🔧 Custom - Configure manually"
        echo ""
        echo -ne "  ${WHITE}Enter choice [1-3]:${NC} "
        read -r num
        case $num in
            1) choice="🏠 Local" ;;
            2) choice="☁️  Cloud" ;;
            *) choice="🔧 Custom" ;;
        esac
    fi
    echo ""
    echo -e "${GREEN}✓${NC} You selected: $choice"
    echo ""
    sleep 1

    # Demo: Confirm
    echo -e "${CYAN}━━━ Demo 3: Confirmation ━━━${NC}"
    echo ""
    if [[ "$HAS_GUM" == "true" ]]; then
        if gum confirm --prompt.foreground="#FFFFFF" "Do you like this experience?"; then
            echo -e "${GREEN}✓${NC} Awesome!"
        else
            echo -e "${WHITE}The bash version is nice too!${NC}"
        fi
    else
        echo -ne "  ${WHITE}Do you like this? [y/N]:${NC} "
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            echo -e "${GREEN}✓${NC} Awesome!"
        else
            echo -e "${WHITE}The bash version is nice too!${NC}"
        fi
    fi
    echo ""
    sleep 1

    # Demo: Spinner
    echo -e "${CYAN}━━━ Demo 4: Progress Spinner ━━━${NC}"
    echo ""
    if [[ "$HAS_GUM" == "true" ]]; then
        gum spin --spinner dot --title "Installing imaginary things..." -- sleep 2
    else
        sleep 2 &
        spinner $! "Installing imaginary things..."
    fi
    echo -e "${GREEN}✓${NC} Done!"
    echo ""

    # Completion
    echo ""
    if [[ "$HAS_GUM" == "true" ]]; then
        gum style --border double --padding "1 4" --border-foreground "#00FF00" --foreground "#00FF00" \
            "✨  Demo Complete!  ✨"
    else
        echo -e "${GREEN}╔═══════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║     ✨  Demo Complete!  ✨            ║${NC}"
        echo -e "${GREEN}╚═══════════════════════════════════════╝${NC}"
    fi
    echo ""
    echo -e "${DIM}Run without --demo to actually install Claude OS${NC}"
    echo ""

    exit 0
}

# Show what would be done without doing it
dry_run_msg() {
    echo -e "${YELLOW}  [DRY-RUN]${NC} $1"
}

# Backup a file before overwriting
backup_file() {
    local file="$1"
    if [[ -f "$file" ]]; then
        local backup="${file}.backup.$(date +%Y%m%d_%H%M%S)"
        if [[ "$DRY_RUN" == "true" ]]; then
            dry_run_msg "Would backup $file → $backup"
        else
            cp "$file" "$backup"
            success "Backed up $file → $backup"
        fi
    fi
}

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
    if [[ "$HAS_GUM" == "true" ]]; then
        # Beautiful gum version
        echo ""
        gum style --border rounded --padding "1 2" --border-foreground "#00FFFF" \
            "$(gum style --foreground "#FFFFFF" --bold "How would you like to power Claude OS?")"
        echo ""

        local choice=$(gum choose --cursor.foreground="#00FFFF" --selected.foreground="#00FF00" \
            "🏠 Local (Ollama) - Free, private, runs on your machine" \
            "☁️  Cloud (OpenAI) - Fast, no local resources needed" \
            "🔧 Custom - I'll configure it myself")

        case "$choice" in
            *"Local"*) PROVIDER="local" ;;
            *"Cloud"*) PROVIDER="openai" ;;
            *"Custom"*) PROVIDER="custom" ;;
        esac
    else
        # Bash fallback
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
    fi

    # Show selection confirmation
    echo ""
    case "$PROVIDER" in
        local) success "Selected: Local (Ollama)" ;;
        openai) success "Selected: Cloud (OpenAI)" ;;
        custom) success "Selected: Custom configuration" ;;
    esac
}

# ═══════════════════════════════════════════════════════════════════════════
# MODEL SIZE SELECTION (for local installs)
# ═══════════════════════════════════════════════════════════════════════════

select_model_size() {
    if [[ "$HAS_GUM" == "true" ]]; then
        # Beautiful gum version
        echo ""
        gum style --border rounded --padding "1 2" --border-foreground "#00FFFF" \
            "$(gum style --foreground "#FFFFFF" --bold "Choose your model size")"
        echo ""

        local choice=$(gum choose --cursor.foreground="#00FFFF" --selected.foreground="#00FF00" \
            "💨 Lite (Recommended) - llama3.2:3b - 2GB download, ~4GB RAM" \
            "🚀 Full - llama3.1:8b - 4.7GB download, ~8GB RAM")

        case "$choice" in
            *"Lite"*) LLM_MODEL="$DEFAULT_LLM_MODEL" ;;
            *"Full"*) LLM_MODEL="$FULL_LLM_MODEL" ;;
        esac
    else
        # Bash fallback
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
    fi

    EMBED_MODEL="$DEFAULT_EMBED_MODEL"

    # Show selection confirmation
    echo ""
    success "Selected: $LLM_MODEL"
}

# ═══════════════════════════════════════════════════════════════════════════
# OPENAI CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

configure_openai() {
    if [[ "$HAS_GUM" == "true" ]]; then
        # Beautiful gum version
        echo ""
        gum style --border rounded --padding "1 2" --border-foreground "#00FFFF" \
            "$(gum style --foreground "#FFFFFF" --bold "OpenAI Configuration")"
        echo ""
        echo -e "  ${DIM}Get your API key at https://platform.openai.com/api-keys${NC}"
        echo ""

        OPENAI_API_KEY=$(gum input --password --placeholder "sk-..." --prompt "API Key: " --prompt.foreground="#00FFFF")
    else
        # Bash fallback
        print_box "OpenAI Configuration"

        echo -e "  ${WHITE}Enter your OpenAI API key:${NC}"
        echo -e "  ${DIM}(Get one at https://platform.openai.com/api-keys)${NC}"
        echo ""
        echo -ne "  ${WHITE}API Key:${NC} "
        read -rs OPENAI_API_KEY
        echo ""
    fi

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
        warn "Python 3.11 or 3.12 not found"
        echo ""

        # Offer to install Python automatically
        local install_python=""
        if [[ "$HAS_GUM" == "true" ]]; then
            install_python=$(gum choose "Yes, install Python 3.12 for me" "No, I'll install it myself" --header "Install Python 3.12 automatically?")
            [[ "$install_python" == "Yes"* ]] && install_python="y"
        else
            echo -ne "  ${WHITE}Install Python 3.12 automatically? [Y/n]:${NC} "
            read -r install_python
            install_python=${install_python:-y}
        fi

        if [[ "$install_python" =~ ^[Yy]$ ]]; then
            info "Installing Python 3.12..."

            if [[ "$OS" == "macos" ]]; then
                if command -v brew &> /dev/null; then
                    brew install python@3.12 &>/dev/null &
                    spinner $! "Installing Python 3.12 via Homebrew..."
                else
                    error "Homebrew not found. Install from https://brew.sh first."
                    exit 1
                fi
            elif [[ "$OS" == "linux" ]]; then
                case "$PKG_MANAGER" in
                    apt)
                        info "Adding deadsnakes PPA for Python 3.12 (this may take a minute)..."
                        sudo apt-get install -y software-properties-common
                        sudo add-apt-repository -y ppa:deadsnakes/ppa
                        info "Updating package lists..."
                        sudo apt-get update
                        info "Installing Python 3.12..."
                        sudo apt-get install -y python3.12 python3.12-venv python3.12-dev
                        ;;
                    dnf)
                        sudo dnf install -y -q python3.12 python3.12-devel &>/dev/null &
                        spinner $! "Installing Python 3.12 via dnf..."
                        ;;
                    yum)
                        sudo yum install -y -q python3.12 python3.12-devel &>/dev/null &
                        spinner $! "Installing Python 3.12 via yum..."
                        ;;
                    pacman)
                        sudo pacman -S --noconfirm python &>/dev/null &
                        spinner $! "Installing Python via pacman..."
                        ;;
                    *)
                        error "Unknown package manager. Please install Python 3.12 manually."
                        exit 1
                        ;;
                esac
            fi

            # Re-check for Python after install
            if command -v python3.12 &> /dev/null; then
                PYTHON_CMD="python3.12"
                success "Python 3.12 installed successfully"
            else
                error "Python installation failed. Please install manually."
                exit 1
            fi
        else
            echo ""
            echo -e "  ${WHITE}Install Python manually:${NC}"
            echo -e "    macOS:  ${CYAN}brew install python@3.12${NC}"
            echo -e "    Ubuntu: ${CYAN}sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt install python3.12 python3.12-venv${NC}"
            echo -e "    Fedora: ${CYAN}sudo dnf install python3.12${NC}"
            exit 1
        fi
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
            cmd_count=$((cmd_count + 1))
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
            skill_count=$((skill_count + 1))
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
    local json_config="${CLAUDE_OS_DIR}/claude-os-config.json"

    # Backup existing configs before overwriting
    backup_file "$config_file"
    backup_file "$json_config"

    if [[ "$DRY_RUN" == "true" ]]; then
        dry_run_msg "Would create $config_file with:"
        dry_run_msg "  CLAUDE_OS_PROVIDER=${PROVIDER}"
        dry_run_msg "  LLM_MODEL=${LLM_MODEL:-gpt-4o-mini}"
        dry_run_msg "  EMBEDDING_MODEL=${EMBED_MODEL:-text-embedding-3-small}"
        dry_run_msg "Would create $json_config"
        return
    fi

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

    if [[ "$HAS_GUM" == "true" ]]; then
        # Beautiful gum completion
        gum style --border double --padding "1 4" --border-foreground "#00FF00" --foreground "#00FF00" \
            "✨  Claude OS is ready!  ✨"
    else
        echo -e "${GREEN}"
        cat << 'EOF'
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║   ✨  Claude OS is ready!  ✨                                     ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
EOF
        echo -e "${NC}"
    fi

    echo ""
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
    # Parse command line arguments first
    parse_args "$@"

    # Detect OS (needed for gum install and demo)
    detect_os

    # Handle demo mode - runs demo and exits
    if [[ "$DEMO_MODE" == "true" ]]; then
        run_demo
        exit 0
    fi

    # Show banner
    show_banner

    # Show dry-run notice if applicable
    if [[ "$DRY_RUN" == "true" ]]; then
        echo ""
        echo -e "${YELLOW}┌────────────────────────────────────────────────────────────────┐${NC}"
        echo -e "${YELLOW}│${NC}  ${WHITE}🔍 DRY-RUN MODE${NC}                                              ${YELLOW}│${NC}"
        echo -e "${YELLOW}│${NC}                                                                ${YELLOW}│${NC}"
        echo -e "${YELLOW}│${NC}  ${DIM}No changes will be made. This shows what would happen.${NC}       ${YELLOW}│${NC}"
        echo -e "${YELLOW}└────────────────────────────────────────────────────────────────┘${NC}"
        echo ""
        sleep 1
    fi

    # Offer to install gum for enhanced experience (skip in dry-run)
    if [[ "$DRY_RUN" != "true" ]]; then
        offer_gum_install
    fi

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
    if [[ "$DRY_RUN" == "true" ]]; then
        print_section "Python Environment"
        dry_run_msg "Would create/use virtual environment at ${CLAUDE_OS_DIR}/venv"
        dry_run_msg "Would install dependencies from requirements.txt"
    else
        setup_python
    fi

    # Provider-specific dependencies
    if [[ "$PROVIDER" == "local" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            print_section "Ollama Setup"
            dry_run_msg "Would install Ollama if not present"
            dry_run_msg "Would download model: ${LLM_MODEL}"
            dry_run_msg "Would download model: ${EMBED_MODEL}"
        else
            setup_ollama
        fi
    fi

    # Optional: Redis (useful for caching)
    if [[ "$DRY_RUN" == "true" ]]; then
        print_section "Redis Setup"
        dry_run_msg "Would install Redis if not present"
        dry_run_msg "Would start Redis service"
    else
        setup_redis
    fi

    # Claude Code integration
    if [[ "$DRY_RUN" == "true" ]]; then
        print_section "Claude Code Integration"
        dry_run_msg "Would create directories: ~/.claude/commands, ~/.claude/skills"
        dry_run_msg "Would symlink commands from ${TEMPLATES_DIR}/commands/"
        dry_run_msg "Would symlink skills from ${TEMPLATES_DIR}/skills/"
        dry_run_msg "Would configure MCP server in ~/.claude/settings.json"
    else
        setup_claude_integration
    fi

    # Create configuration
    create_config

    # Show completion
    if [[ "$DRY_RUN" == "true" ]]; then
        echo ""
        echo -e "${YELLOW}┌────────────────────────────────────────────────────────────────┐${NC}"
        echo -e "${YELLOW}│${NC}  ${WHITE}✓ Dry-run complete!${NC}                                          ${YELLOW}│${NC}"
        echo -e "${YELLOW}│${NC}                                                                ${YELLOW}│${NC}"
        echo -e "${YELLOW}│${NC}  ${DIM}Run without --dry-run to perform the actual installation.${NC}    ${YELLOW}│${NC}"
        echo -e "${YELLOW}└────────────────────────────────────────────────────────────────┘${NC}"
        echo ""
    else
        show_completion
    fi
}

# Run main
main "$@"
