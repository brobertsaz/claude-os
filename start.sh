#!/bin/bash

# ============================================================================
# Code-Forge Quick Start Script
# ============================================================================
# This script starts all Code-Forge services for daily use.
# For first-time setup, run ./setup.sh instead.
# ============================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Banner
echo -e "${PURPLE}"
cat << "EOF"
   ____          _        _____
  / ___|___   __| | ___  |  ___|__  _ __ __ _  ___
 | |   / _ \ / _` |/ _ \ | |_ / _ \| '__/ _` |/ _ \
 | |__| (_) | (_| |  __/ |  _| (_) | | | (_| |  __/
  \____\___/ \__,_|\___| |_|  \___/|_|  \__, |\___|
                                        |___/
EOF
echo -e "${NC}"

echo -e "${BLUE}🚀 Starting Code-Forge...${NC}\n"

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

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_warning "This script is optimized for macOS. Adjust commands for your platform if needed."
fi

# ============================================================================
# 1. Check Prerequisites
# ============================================================================
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${PURPLE}  Checking Prerequisites${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker not found. Please run ./setup.sh first."
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker Desktop."
    exit 1
fi
print_success "Docker is running"

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js not found. Please run ./setup.sh first."
    exit 1
fi
print_success "Node.js is installed"

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    print_warning "Frontend dependencies not installed. Installing now..."
    cd frontend
    npm install
    cd ..
    print_success "Frontend dependencies installed"
else
    print_success "Frontend dependencies ready"
fi

# ============================================================================
# 2. Start Backend Services
# ============================================================================
echo -e "\n${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${PURPLE}  Starting Backend Services${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

print_status "Starting Docker containers..."
docker-compose up -d

# Wait for services to be ready
sleep 3

# Check if containers are running
if docker-compose ps | grep -q "Up"; then
    print_success "Backend services started"
else
    print_error "Failed to start backend services"
    print_status "Run 'docker-compose logs' to see errors"
    exit 1
fi

# ============================================================================
# 3. Start Frontend Dev Server
# ============================================================================
echo -e "\n${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${PURPLE}  Starting Frontend Dev Server${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# Check if frontend is already running
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_warning "Frontend dev server already running on port 5173"
    print_status "Kill it with: pkill -f 'vite'"
else
    print_status "Starting React dev server..."
    cd frontend
    npm run dev > ../frontend-dev.log 2>&1 &
    FRONTEND_PID=$!
    cd ..

    # Wait for frontend to start
    sleep 3

    # Check if frontend started successfully
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        print_success "Frontend dev server started (PID: $FRONTEND_PID)"
    else
        print_warning "Frontend may have failed to start"
        print_status "Check frontend-dev.log for errors"
    fi
fi

# ============================================================================
# 4. Open Browser
# ============================================================================
echo -e "\n${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${PURPLE}  Opening Browser${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

print_status "Waiting for frontend to be ready..."
sleep 2

# Open browser
if command -v open &> /dev/null; then
    open http://localhost:5173
    print_success "Browser opened at http://localhost:5173"
else
    print_status "Please open http://localhost:5173 in your browser"
fi

# ============================================================================
# Success!
# ============================================================================
echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✓ Code-Forge is Running!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo -e "${YELLOW}Access the application:${NC}"
echo -e "  ${GREEN}•${NC} React UI:      ${BLUE}http://localhost:5173${NC} ${PURPLE}(Opening now...)${NC}"
echo -e "  ${GREEN}•${NC} Streamlit UI:  ${BLUE}http://localhost:8501${NC} ${YELLOW}(Legacy)${NC}"
echo -e "  ${GREEN}•${NC} MCP Server:    ${BLUE}http://localhost:8051${NC}"
echo -e "  ${GREEN}•${NC} Ollama API:    ${BLUE}http://localhost:11434${NC}\n"

echo -e "${YELLOW}Useful commands:${NC}"
echo -e "  ${GREEN}•${NC} View backend logs:  ${BLUE}docker-compose logs -f${NC}"
echo -e "  ${GREEN}•${NC} View frontend logs: ${BLUE}tail -f frontend-dev.log${NC}"
echo -e "  ${GREEN}•${NC} Stop all services:  ${BLUE}./stop.sh${NC} or ${BLUE}docker-compose down && pkill -f 'vite'${NC}\n"

echo -e "${PURPLE}Happy coding! 🚀${NC}\n"
