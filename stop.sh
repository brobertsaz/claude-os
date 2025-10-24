#!/bin/bash

# ============================================================================
# Code-Forge Stop Script
# ============================================================================
# This script stops all Code-Forge services.
# ============================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Stopping Code-Forge...${NC}\n"

# Function to print status
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# ============================================================================
# 1. Stop Frontend Dev Server
# ============================================================================
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${PURPLE}  Stopping Frontend Dev Server${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_status "Stopping React dev server..."
    pkill -f 'vite' 2>/dev/null
    sleep 1
    
    # Verify it stopped
    if ! lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_success "Frontend dev server stopped"
    else
        print_warning "Frontend may still be running. Try: pkill -9 -f 'vite'"
    fi
else
    print_status "Frontend dev server not running"
fi

# ============================================================================
# 2. Stop Backend Services
# ============================================================================
echo -e "\n${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${PURPLE}  Stopping Backend Services${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

if command -v docker-compose &> /dev/null; then
    print_status "Stopping Docker containers..."
    docker-compose down
    print_success "Backend services stopped"
else
    print_warning "docker-compose not found"
fi

# ============================================================================
# Success!
# ============================================================================
echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✓ Code-Forge Stopped${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo -e "${YELLOW}To start again, run:${NC} ${BLUE}./start.sh${NC}\n"

