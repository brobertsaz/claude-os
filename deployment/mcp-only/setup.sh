#!/bin/bash

# Claude OS MCP-Only Setup Script
# This script helps with first-time deployment

set -e

echo "🚀 Claude OS MCP-Only Deployment Setup"
echo "======================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install docker-compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and docker-compose are installed"
echo ""

# Check if database exists
DB_PATH="../../data/claude-os.db"
if [ ! -f "$DB_PATH" ]; then
    echo "⚠️  Database not found at: $DB_PATH"
    echo ""
    echo "   This deployment expects your existing Claude OS database."
    echo "   Please ensure Claude OS is set up locally first, or"
    echo "   adjust the volume mount in docker-compose.yml"
    echo ""
    read -p "   Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Database found at: $DB_PATH"
    # Get database size
    DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
    echo "   Size: $DB_SIZE"
fi
echo ""

# Create .env from example if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo "   Please review and update .env with your settings"
    echo ""
else
    echo "✅ .env file already exists"
    echo ""
fi

# Prompt for CORS origins
echo "🔧 Configuration"
echo "---------------"
read -p "Enter CORS origins (comma-separated, or * for all) [*]: " CORS_INPUT
CORS_INPUT=${CORS_INPUT:-*}

# Update .env
sed -i.bak "s|CORS_ORIGINS=.*|CORS_ORIGINS=$CORS_INPUT|" .env && rm .env.bak
echo "✅ CORS_ORIGINS set to: $CORS_INPUT"
echo ""

# Ask about authentication
read -p "Enable authentication? (y/n) [n]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Generate a random secret
    JWT_SECRET=$(openssl rand -hex 32 2>/dev/null || echo "CHANGE-THIS-SECRET-$(date +%s)")

    read -p "Enter API username [admin]: " API_USER
    API_USER=${API_USER:-admin}

    read -s -p "Enter API password: " API_PASS
    echo

    if [ -z "$API_PASS" ]; then
        echo "❌ Password cannot be empty"
        exit 1
    fi

    # Uncomment and set auth variables in .env
    sed -i.bak "s|# JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$JWT_SECRET|" .env && rm .env.bak
    sed -i.bak "s|# JWT_ALGORITHM=.*|JWT_ALGORITHM=HS256|" .env && rm .env.bak
    sed -i.bak "s|# API_USERNAME=.*|API_USERNAME=$API_USER|" .env && rm .env.bak
    sed -i.bak "s|# API_PASSWORD=.*|API_PASSWORD=$API_PASS|" .env && rm .env.bak

    echo "✅ Authentication enabled"
else
    echo "⚠️  Authentication disabled (not recommended for production)"
fi
echo ""

# Start services
echo "🐳 Starting Docker containers..."
echo "-------------------------------"
docker-compose up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 5

# Wait for Ollama to be ready
echo "Checking Ollama status..."
OLLAMA_READY=0
for i in {1..30}; do
    if docker exec claude-os-ollama ollama list &>/dev/null; then
        OLLAMA_READY=1
        break
    fi
    echo "  Waiting for Ollama... ($i/30)"
    sleep 2
done

if [ $OLLAMA_READY -eq 0 ]; then
    echo "⚠️  Ollama is taking longer than expected to start"
    echo "   You can check logs with: docker-compose logs ollama"
else
    echo "✅ Ollama is ready"
fi
echo ""

# Pull required models
echo "📥 Pulling required Ollama models..."
echo "-----------------------------------"
echo "This may take a few minutes on first run..."
echo ""

echo "Pulling nomic-embed-text (embeddings)..."
docker exec claude-os-ollama ollama pull nomic-embed-text

echo "Pulling llama3.1:latest (LLM)..."
docker exec claude-os-ollama ollama pull llama3.1:latest

echo ""
echo "✅ Models downloaded successfully"
echo ""

# Check MCP server health
echo "🏥 Checking MCP server health..."
sleep 3

if curl -f http://localhost:8051/health &>/dev/null; then
    echo "✅ MCP server is healthy!"
else
    echo "⚠️  MCP server is not responding yet"
    echo "   Check logs with: docker-compose logs mcp-server"
fi

echo ""
echo "========================================="
echo "✨ Setup Complete!"
echo "========================================="
echo ""
echo "Your MCP server is now running at:"
echo "  http://localhost:8051"
echo ""
echo "Test it with:"
echo "  curl http://localhost:8051/health"
echo ""
echo "View logs:"
echo "  docker-compose logs -f mcp-server"
echo ""
echo "Stop services:"
echo "  docker-compose down"
echo ""
echo "See README.md for usage examples and API documentation"
echo ""
