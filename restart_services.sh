#!/bin/bash

# Restart Code-Forge services to apply performance optimizations
echo "🚀 Restarting Code-Forge services with optimizations..."

# Stop services
echo "Stopping services..."
./stop.sh

# Wait for clean shutdown
sleep 2

# Start services with new configuration
echo "Starting services with optimizations..."
./start.sh

echo ""
echo "✅ Services restarted with optimizations:"
echo "  - RAGEngine caching enabled (saves 10-15s per query)"
echo "  - TOP_K_RETRIEVAL increased from 5 to 15"
echo "  - SIMILARITY_THRESHOLD lowered from 0.7 to 0.5"
echo "  - Context window increased from 1024 to 4096 tokens"
echo "  - Temperature lowered to 0.2 for more factual responses"
echo ""
echo "🎯 Expected performance improvements:"
echo "  - First query: ~15-20 seconds (builds cache)"
echo "  - Subsequent queries: ~5-10 seconds (uses cache)"
echo "  - Better context retrieval from your 51 documents"
echo "  - Reduced hallucinations about non-existent content"
echo ""
echo "📊 Monitor logs for performance metrics:"
echo "  docker-compose logs -f mcp_server | grep 'Query executed'"