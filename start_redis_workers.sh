#!/bin/bash

# Claude OS Real-Time Learning System - Worker Startup Script
# Starts RQ workers for real-time learning system

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Claude OS Real-Time Learning System${NC}"
echo -e "${GREEN}Redis Worker Startup${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Check if Redis is running
echo -e "${YELLOW}1. Checking Redis connection...${NC}"
if ! redis-cli ping &> /dev/null; then
    echo -e "${RED}❌ Redis is not running${NC}"
    echo "Please start Redis first:"
    echo "  redis-server"
    echo "  or: brew services start redis"
    exit 1
fi
echo -e "${GREEN}✅ Redis is running${NC}\n"

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}2. Creating Python virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment exists${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}3. Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}\n"

# Install dependencies
echo -e "${YELLOW}4. Installing dependencies...${NC}"
pip install -q redis rq 2>/dev/null || true
echo -e "${GREEN}✅ Dependencies installed${NC}\n"

# Start workers
echo -e "${YELLOW}5. Starting RQ workers...${NC}"
echo -e "${GREEN}🚀 Worker queues: claude-os:learning, claude-os:prompts, claude-os:ingest${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}\n"

python -m rq worker claude-os:learning claude-os:prompts claude-os:ingest --with-scheduler

# Cleanup on exit
trap 'echo -e "\n${GREEN}👋 Redis workers stopped${NC}"' EXIT
