#!/bin/bash

# Claude OS Test Runner
# This script runs the test suite with proper environment setup

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Claude OS Test Suite${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest not found${NC}"
    echo "Installing test dependencies..."
    pip install pytest pytest-asyncio pytest-cov pytest-mock httpx faker
fi

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo -e "${YELLOW}⚠️  PostgreSQL is not running${NC}"
    echo "Please start PostgreSQL before running tests"
    exit 1
fi

# Check if test database exists
if ! psql -lqt | cut -d \| -f 1 | grep -qw codeforge_test; then
    echo -e "${YELLOW}⚠️  Test database 'codeforge_test' does not exist${NC}"
    echo "Creating test database..."
    createdb codeforge_test
    psql -d codeforge_test -c "CREATE EXTENSION IF NOT EXISTS vector"
    echo -e "${GREEN}✅ Test database created${NC}"
fi

# Set test environment variables
export TEST_POSTGRES_HOST=${TEST_POSTGRES_HOST:-localhost}
export TEST_POSTGRES_PORT=${TEST_POSTGRES_PORT:-5432}
export TEST_POSTGRES_DB=${TEST_POSTGRES_DB:-codeforge_test}
export TEST_POSTGRES_USER=${TEST_POSTGRES_USER:-$USER}
export TEST_OLLAMA_HOST=${TEST_OLLAMA_HOST:-http://localhost:11434}

echo -e "${GREEN}Test Configuration:${NC}"
echo "  Database: $TEST_POSTGRES_DB"
echo "  Host: $TEST_POSTGRES_HOST:$TEST_POSTGRES_PORT"
echo "  User: $TEST_POSTGRES_USER"
echo "  Ollama: $TEST_OLLAMA_HOST"
echo ""

# Parse command line arguments
TEST_ARGS=""
COVERAGE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            TEST_ARGS="$TEST_ARGS -m unit"
            shift
            ;;
        --integration)
            TEST_ARGS="$TEST_ARGS -m integration"
            shift
            ;;
        --vector)
            TEST_ARGS="$TEST_ARGS -m vector"
            shift
            ;;
        --rag)
            TEST_ARGS="$TEST_ARGS -m rag"
            shift
            ;;
        --api)
            TEST_ARGS="$TEST_ARGS -m api"
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose|-v)
            TEST_ARGS="$TEST_ARGS -v"
            shift
            ;;
        --help|-h)
            echo "Usage: ./run_tests.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --unit          Run only unit tests"
            echo "  --integration   Run only integration tests"
            echo "  --vector        Run only vector operation tests"
            echo "  --rag           Run only RAG engine tests"
            echo "  --api           Run only API endpoint tests"
            echo "  --coverage      Generate coverage report"
            echo "  --verbose, -v   Verbose output"
            echo "  --help, -h      Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./run_tests.sh                    # Run all tests"
            echo "  ./run_tests.sh --unit             # Run only unit tests"
            echo "  ./run_tests.sh --coverage         # Run with coverage"
            echo "  ./run_tests.sh --integration -v   # Run integration tests verbosely"
            exit 0
            ;;
        *)
            TEST_ARGS="$TEST_ARGS $1"
            shift
            ;;
    esac
done

# Run tests
echo -e "${GREEN}Running tests...${NC}"
echo ""

if [ "$COVERAGE" = true ]; then
    pytest $TEST_ARGS --cov=app --cov-report=term-missing --cov-report=html
    echo ""
    echo -e "${GREEN}✅ Coverage report generated: htmlcov/index.html${NC}"
else
    pytest $TEST_ARGS
fi

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo -e "${GREEN}================================${NC}"
else
    echo ""
    echo -e "${RED}================================${NC}"
    echo -e "${RED}❌ Some tests failed${NC}"
    echo -e "${RED}================================${NC}"
    exit 1
fi

