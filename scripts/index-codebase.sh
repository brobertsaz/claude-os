#!/bin/bash

# Claude OS Codebase Indexing Script
# Indexes an entire project codebase into Claude OS knowledge bases
#
# Usage:
#   ./index-codebase.sh [project_name] [project_path] [claude_os_url]
#
# Examples:
#   ./index-codebase.sh MyApp ~/Projects/myapp http://localhost:8051
#   ./index-codebase.sh MyApp /var/www/myapp/current http://localhost:8051

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
PROJECT_NAME=${1:-}
PROJECT_PATH=${2:-$(pwd)}
CLAUDE_OS_URL=${3:-http://localhost:8051}

# Validate arguments
if [ -z "$PROJECT_NAME" ]; then
    echo -e "${RED}Error: Project name is required${NC}"
    echo ""
    echo "Usage: $0 <project_name> [project_path] [claude_os_url]"
    echo ""
    echo "Examples:"
    echo "  $0 MyApp ~/Projects/myapp http://localhost:8051"
    echo "  $0 MyApp /var/www/myapp/current http://localhost:8051"
    exit 1
fi

if [ ! -d "$PROJECT_PATH" ]; then
    echo -e "${RED}Error: Project path does not exist: $PROJECT_PATH${NC}"
    exit 1
fi

# Banner
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║         Claude OS Codebase Indexing Script                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${YELLOW}Project:${NC} $PROJECT_NAME"
echo -e "${YELLOW}Path:${NC} $PROJECT_PATH"
echo -e "${YELLOW}Claude OS:${NC} $CLAUDE_OS_URL"
echo ""

# Check if Claude OS is running
echo -e "${BLUE}Checking Claude OS server...${NC}"
if ! curl -s -f "$CLAUDE_OS_URL/health" > /dev/null 2>&1; then
    echo -e "${RED}✗ Claude OS server is not responding at $CLAUDE_OS_URL${NC}"
    echo ""
    echo "Please ensure Claude OS is running:"
    echo "  Local: cd ~/Projects/claude-os && ./start.sh"
    echo "  Server: sudo systemctl start claude-os"
    exit 1
fi
echo -e "${GREEN}✓ Claude OS is running${NC}"
echo ""

# Knowledge base names
KB_DOCS="${PROJECT_NAME}-knowledge_docs"
KB_PROFILE="${PROJECT_NAME}-project_profile"
KB_INDEX="${PROJECT_NAME}-project_index"
KB_MEMORIES="${PROJECT_NAME}-project_memories"

# Function to index a directory
index_directory() {
    local dir_path=$1
    local kb_name=$2
    local description=$3

    if [ ! -d "$dir_path" ]; then
        echo -e "${YELLOW}⊘ Skipping $description (directory not found: $dir_path)${NC}"
        return 0
    fi

    # Count files to index
    file_count=$(find "$dir_path" -type f \( \
        -name "*.rb" -o -name "*.py" -o -name "*.js" -o -name "*.jsx" \
        -o -name "*.ts" -o -name "*.tsx" -o -name "*.go" -o -name "*.java" \
        -o -name "*.php" -o -name "*.c" -o -name "*.cpp" -o -name "*.h" \
        -o -name "*.rs" -o -name "*.swift" -o -name "*.kt" -o -name "*.scala" \
        -o -name "*.md" -o -name "*.txt" -o -name "*.yml" -o -name "*.yaml" \
        -o -name "*.json" -o -name "*.xml" \
    \) 2>/dev/null | wc -l | tr -d ' ')

    echo -e "${BLUE}→ Indexing $description${NC}"
    echo "  Path: $dir_path"
    echo "  Files: ~$file_count"
    echo "  Target: $kb_name"

    # Call Claude OS API
    response=$(curl -s -X POST "$CLAUDE_OS_URL/api/kb/$kb_name/import" \
        -H "Content-Type: application/json" \
        -d "{\"directory_path\": \"$dir_path\"}")

    # Parse response
    if echo "$response" | grep -q '"success".*true'; then
        successful=$(echo "$response" | grep -o '"successful":[0-9]*' | cut -d':' -f2)
        failed=$(echo "$response" | grep -o '"failed":[0-9]*' | cut -d':' -f2)
        total=$(echo "$response" | grep -o '"total_files":[0-9]*' | cut -d':' -f2)

        echo -e "${GREEN}✓ Indexed: $successful files successful, $failed failed (total: $total)${NC}"
    else
        echo -e "${RED}✗ Failed to index $description${NC}"
        echo "  Response: $response"
    fi
    echo ""
}

# Function to get KB stats
get_kb_stats() {
    local kb_name=$1
    local description=$2

    stats=$(curl -s "$CLAUDE_OS_URL/api/kb/$kb_name/stats")

    if echo "$stats" | grep -q '"document_count"'; then
        doc_count=$(echo "$stats" | grep -o '"document_count":[0-9]*' | cut -d':' -f2)
        chunk_count=$(echo "$stats" | grep -o '"chunk_count":[0-9]*' | cut -d':' -f2)
        echo -e "${BLUE}  $description:${NC} $doc_count docs, $chunk_count chunks"
    fi
}

echo -e "${YELLOW}Starting codebase indexing...${NC}"
echo ""

# Index based on common project structures

# 1. Documentation
echo -e "${GREEN}[1/6] Documentation${NC}"
if [ -d "$PROJECT_PATH/docs" ]; then
    index_directory "$PROJECT_PATH/docs" "$KB_DOCS" "Documentation (docs/)"
elif [ -d "$PROJECT_PATH/documentation" ]; then
    index_directory "$PROJECT_PATH/documentation" "$KB_DOCS" "Documentation (documentation/)"
else
    echo -e "${YELLOW}⊘ No docs directory found${NC}"
    echo ""
fi

# 2. Application code (main source)
echo -e "${GREEN}[2/6] Application Code${NC}"
if [ -d "$PROJECT_PATH/app" ]; then
    # Rails/Laravel style
    index_directory "$PROJECT_PATH/app" "$KB_INDEX" "Application Code (app/)"
elif [ -d "$PROJECT_PATH/src" ]; then
    # Modern JS/TS/Go/Rust style
    index_directory "$PROJECT_PATH/src" "$KB_INDEX" "Source Code (src/)"
elif [ -d "$PROJECT_PATH/lib" ]; then
    # Ruby gem style
    index_directory "$PROJECT_PATH/lib" "$KB_INDEX" "Library Code (lib/)"
else
    echo -e "${YELLOW}⊘ No standard source directory found (app/, src/, lib/)${NC}"
    echo ""
fi

# 3. Models/Database
echo -e "${GREEN}[3/6] Models & Database${NC}"
if [ -d "$PROJECT_PATH/app/models" ]; then
    index_directory "$PROJECT_PATH/app/models" "$KB_INDEX" "Models (app/models/)"
fi
if [ -d "$PROJECT_PATH/db" ]; then
    index_directory "$KB_INDEX" "$PROJECT_PATH/db" "Database (db/)"
fi

# 4. Services/Business Logic
echo -e "${GREEN}[4/6] Services & Business Logic${NC}"
if [ -d "$PROJECT_PATH/app/services" ]; then
    index_directory "$PROJECT_PATH/app/services" "$KB_INDEX" "Services (app/services/)"
fi
if [ -d "$PROJECT_PATH/services" ]; then
    index_directory "$PROJECT_PATH/services" "$KB_INDEX" "Services (services/)"
fi

# 5. Controllers/Routes/API
echo -e "${GREEN}[5/6] Controllers & API${NC}"
if [ -d "$PROJECT_PATH/app/controllers" ]; then
    index_directory "$PROJECT_PATH/app/controllers" "$KB_INDEX" "Controllers (app/controllers/)"
fi
if [ -d "$PROJECT_PATH/api" ]; then
    index_directory "$PROJECT_PATH/api" "$KB_INDEX" "API (api/)"
fi

# 6. Configuration
echo -e "${GREEN}[6/6] Configuration${NC}"
if [ -d "$PROJECT_PATH/config" ]; then
    index_directory "$PROJECT_PATH/config" "$KB_PROFILE" "Configuration (config/)"
fi

# Summary
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    Indexing Complete                       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Knowledge Base Statistics:${NC}"
echo ""
get_kb_stats "$KB_DOCS" "Documentation"
get_kb_stats "$KB_INDEX" "Code Index"
get_kb_stats "$KB_PROFILE" "Project Profile"
get_kb_stats "$KB_MEMORIES" "Memories"
echo ""

echo -e "${GREEN}✓ Codebase indexing complete!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Test semantic search: curl -X POST \"$CLAUDE_OS_URL/api/query\" \\"
echo "       -H \"Content-Type: application/json\" \\"
echo "       -d '{\"kb_name\":\"$KB_INDEX\",\"query\":\"your search query\"}'"
echo ""
echo "  2. View in UI: $CLAUDE_OS_URL"
echo ""
echo "  3. Re-run this script anytime to update the index with new code"
echo ""
