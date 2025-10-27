#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================="
echo "🔄 Claude OS - Restarting All Services"
echo "=================================================${NC}"
echo ""

# Get the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Stop services
echo -e "${YELLOW}Stopping existing services...${NC}"
"$PROJECT_DIR/stop_all_services.sh"

# Wait a bit for ports to be released and cleanup
echo -e "${YELLOW}Cleaning up...${NC}"
sleep 3

# Start services
echo ""
echo -e "${YELLOW}Starting all services fresh...${NC}"
echo ""
"$PROJECT_DIR/start_all_services.sh"
