#!/bin/bash

# Code-Forge Setup Script
# Automated setup for first-time users

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Archon-inspired banner
echo -e "${PURPLE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ██████╗ ██████╗ ██████╗ ███████╗    ███████╗ ██████╗ ██████╗  ██████╗ ███████╗
║  ██╔════╝██╔═══██╗██╔══██╗██╔════╝    ██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
║  ██║     ██║   ██║██║  ██║█████╗      █████╗  ██║   ██║██████╔╝██║  ███╗█████╗
║  ██║     ██║   ██║██║  ██║██╔══╝      ██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝
║  ╚██████╗╚██████╔╝██████╔╝███████╗    ██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗
║   ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝    ╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
║                                                               ║
║           Localized Multi-Knowledge-Base RAG System          ║
║                    with MCP Integration                      ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${BLUE}🚀 Starting Code-Forge setup...${NC}\n"

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
    print_error "This script is designed for macOS. For other platforms, please follow manual setup instructions."
    exit 1
fi

print_success "Running on macOS"

# ============================================================================
# 1. Check Docker
# ============================================================================
echo -e "\n${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${PURPLE}  Step 1: Docker${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d ' ' -f3 | cut -d ',' -f1)
    print_success "Docker installed (version $DOCKER_VERSION)"

    # Check if Docker is running
    if docker info &> /dev/null; then
        print_success "Docker daemon is running"
    else
        print_error "Docker is installed but not running"
        print_status "Please start Docker Desktop and run this script again"
        exit 1
    fi
else
    print_error "Docker not found"
    print_status "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# ============================================================================
# 2. Check PostgreSQL
# ============================================================================
echo -e "\n${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${PURPLE}  Step 2: PostgreSQL${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

if command -v psql &> /dev/null; then
    PG_VERSION=$(psql --version | cut -d ' ' -f3)
    print_success "PostgreSQL installed (version $PG_VERSION)"
else
    print_error "PostgreSQL not found"
    print_status "Please install PostgreSQL from: https://postgresapp.com/"
    print_status "Or via Homebrew: brew install postgresql@17"
    exit 1
fi

# Test PostgreSQL connection
print_status "Testing PostgreSQL connection..."
if psql -c "SELECT version();" &> /dev/null; then
    print_success "PostgreSQL connection successful"
else
    print_error "Cannot connect to PostgreSQL"
    print_status "Please ensure PostgreSQL is running"
    print_status "If using Postgres.app, make sure it's started"
    exit 1
fi

# ============================================================================
# 3. Install pgvector Extension
# ============================================================================
echo -e "\n${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${PURPLE}  Step 3: pgvector Extension${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

print_status "Checking for pgvector extension..."

# Check if pgvector is available
if psql -c "CREATE EXTENSION IF NOT EXISTS vector;" &> /dev/null; then
    PGVECTOR_VERSION=$(psql -c "SELECT extversion FROM pg_extension WHERE extname='vector';" -t 2>/dev/null | xargs)
    if [ -n "$PGVECTOR_VERSION" ]; then
        print_success "pgvector extension installed (version $PGVECTOR_VERSION)"
    else
        print_success "pgvector extension enabled"
    fi
else
    print_error "pgvector extension not available"
    print_status "Installing pgvector..."

    # Try to install via Homebrew
    if command -v brew &> /dev/null; then
        brew install pgvector
        print_success "pgvector installed via Homebrew"
    else
        print_error "Homebrew not found. Please install pgvector manually:"
        print_status "Visit: https://github.com/pgvector/pgvector"
        exit 1
    fi
fi

# ============================================================================
# 4. Create Database
# ============================================================================
echo -e "\n${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${PURPLE}  Step 4: Database Setup${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

print_status "Creating 'codeforge' database..."

# Check if database exists
if psql -lqt | cut -d \| -f 1 | grep -qw codeforge; then
    print_warning "Database 'codeforge' already exists"
    read -p "$(echo -e ${YELLOW}Do you want to recreate it? This will DELETE all existing data! [y/N]: ${NC})" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Dropping existing database..."
        psql -c "DROP DATABASE codeforge;" 2>/dev/null || true
        psql -c "CREATE DATABASE codeforge;"
        print_success "Database recreated"
    else
        print_status "Keeping existing database"
    fi
else
    psql -c "CREATE DATABASE codeforge;"
    print_success "Database 'codeforge' created"
fi

# Enable pgvector extension in the database
print_status "Enabling pgvector extension in codeforge database..."
psql -d codeforge -c "CREATE EXTENSION IF NOT EXISTS vector;" &> /dev/null
print_success "pgvector extension enabled in codeforge database"

# Run schema.sql
print_status "Creating database schema..."
if [ -f "app/db/schema.sql" ]; then
    psql -d codeforge -f app/db/schema.sql &> /dev/null
    print_success "Database schema created"

    # Verify tables
    TABLE_COUNT=$(psql -d codeforge -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" | xargs)
    print_success "Created $TABLE_COUNT tables"
else
    print_error "Schema file not found: app/db/schema.sql"
    exit 1
fi

# ============================================================================
# 5. Check Ollama
# ============================================================================
echo -e "\n${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${PURPLE}  Step 5: Ollama${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

if command -v ollama &> /dev/null; then
    OLLAMA_VERSION=$(ollama --version 2>&1 | head -n1 || echo "unknown")
    print_success "Ollama installed ($OLLAMA_VERSION)"
else
    print_error "Ollama not found"
    print_status "Installing Ollama..."

    if command -v brew &> /dev/null; then
        brew install ollama
        print_success "Ollama installed via Homebrew"
    else
        print_status "Please install Ollama from: https://ollama.ai/download"
        exit 1
    fi
fi

# ============================================================================
# 6. Download Required Models
# ============================================================================
echo -e "\n${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${PURPLE}  Step 6: Ollama Models${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

print_status "This will download ~7GB of models. This may take a while..."

# Start Ollama service if not running
if ! pgrep -x "ollama" > /dev/null; then
    print_status "Starting Ollama service..."
    ollama serve &> /dev/null &
    sleep 3
    print_success "Ollama service started"
fi

# Download embedding model
print_status "Downloading nomic-embed-text (274 MB)..."
ollama pull nomic-embed-text
print_success "nomic-embed-text downloaded"

# Download LLM model
print_status "Downloading llama3.2:3b (2.0 GB)..."
ollama pull llama3.2:3b
print_success "llama3.2:3b downloaded"

# List installed models
print_success "Installed models:"
ollama list

# ============================================================================
# 7. Create Data Directories
# ============================================================================
echo -e "\n${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${PURPLE}  Step 7: Data Directories${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

print_status "Creating data directories..."
mkdir -p data/ollama
print_success "Created data/ollama/"

# ============================================================================
# 8. Build Docker Containers
# ============================================================================
echo -e "\n${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${PURPLE}  Step 8: Docker Containers${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

print_status "Building Docker containers..."
docker-compose build
print_success "Docker containers built"

# ============================================================================
# 9. Start Services
# ============================================================================
echo -e "\n${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${PURPLE}  Step 9: Start Services${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

print_status "Starting Code-Forge services..."
docker-compose up -d
sleep 5
print_success "Services started"

# ============================================================================
# 10. Verify Installation
# ============================================================================
echo -e "\n${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${PURPLE}  Step 10: Verification${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

print_status "Verifying installation..."

# Check if services are running
if docker ps | grep -q code-forge-app; then
    print_success "Code-Forge app container running"
else
    print_error "Code-Forge app container not running"
fi

if docker ps | grep -q code-forge-ollama; then
    print_success "Ollama container running"
else
    print_error "Ollama container not running"
fi

# ============================================================================
# Setup Complete!
# ============================================================================
echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✓ Setup Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo -e "${BLUE}🎉 Code-Forge is ready to use!${NC}\n"

echo -e "${YELLOW}Access the application:${NC}"
echo -e "  ${GREEN}•${NC} React UI:      ${BLUE}http://localhost:5173${NC} ${PURPLE}(Recommended)${NC}"
echo -e "  ${GREEN}•${NC} Streamlit UI:  ${BLUE}http://localhost:8501${NC}"
echo -e "  ${GREEN}•${NC} MCP Server:    ${BLUE}http://localhost:8051${NC}"
echo -e "  ${GREEN}•${NC} Ollama API:    ${BLUE}http://localhost:11434${NC}\n"

echo -e "${YELLOW}Next steps:${NC}"
echo -e "  ${GREEN}1.${NC} Start the React frontend: ${BLUE}cd frontend && npm install && npm run dev${NC}"
echo -e "  ${GREEN}2.${NC} Open ${BLUE}http://localhost:5173${NC} in your browser"
echo -e "  ${GREEN}3.${NC} Create your first knowledge base"
echo -e "  ${GREEN}4.${NC} Upload documents and start chatting!\n"

echo -e "${YELLOW}Useful commands:${NC}"
echo -e "  ${GREEN}•${NC} View logs:        ${BLUE}docker-compose logs -f${NC}"
echo -e "  ${GREEN}•${NC} Stop services:    ${BLUE}docker-compose down${NC}"
echo -e "  ${GREEN}•${NC} Restart services: ${BLUE}docker-compose restart${NC}\n"

echo -e "${PURPLE}For more information, see README.md${NC}\n"

