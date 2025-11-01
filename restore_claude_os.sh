#!/bin/bash

# Claude OS Restore Script
# This script restores a previously backed up Claude OS installation

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}   Claude OS Restore Script${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if backup timestamp was provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: No backup timestamp provided${NC}"
    echo ""
    echo "Usage: $0 <timestamp>"
    echo ""
    echo "Available backups:"
    if [ -d "backups" ]; then
        ls -1 backups/ | grep backup_ | sed 's/backup_/  /'
    else
        echo "  No backups found"
    fi
    exit 1
fi

TIMESTAMP="$1"
BACKUP_DIR="$SCRIPT_DIR/backups/backup_$TIMESTAMP"

# Check if backup exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}Error: Backup not found at $BACKUP_DIR${NC}"
    echo ""
    echo "Available backups:"
    if [ -d "backups" ]; then
        ls -1 backups/ | grep backup_ | sed 's/backup_/  /'
    else
        echo "  No backups found"
    fi
    exit 1
fi

echo -e "${YELLOW}Restoring from backup: $TIMESTAMP${NC}"
echo -e "${YELLOW}Backup location: $BACKUP_DIR${NC}"
echo ""

# Show manifest if it exists
if [ -f "$BACKUP_DIR/MANIFEST.txt" ]; then
    echo -e "${BLUE}Backup Manifest:${NC}"
    cat "$BACKUP_DIR/MANIFEST.txt"
    echo ""
fi

# Ask for confirmation
echo -e "${RED}WARNING: This will overwrite your current Claude OS data!${NC}"
echo -e "${YELLOW}Press Enter to continue, or Ctrl+C to cancel...${NC}"
read -r

# Function to restore a file or directory
restore_item() {
    local backup_path="$1"
    local dest_path="$2"
    local item_name="$3"

    if [ -e "$backup_path" ]; then
        echo -e "${GREEN}✓${NC} Restoring: $item_name"

        # Create parent directory if needed
        mkdir -p "$(dirname "$dest_path")"

        if [ -d "$backup_path" ]; then
            rm -rf "$dest_path" 2>/dev/null || true
            cp -r "$backup_path" "$dest_path"
        else
            cp "$backup_path" "$dest_path"
        fi
    else
        echo -e "${YELLOW}⚠${NC} Skipping (not in backup): $item_name"
    fi
}

echo ""
echo -e "${BLUE}1. Restoring database...${NC}"
restore_item "$BACKUP_DIR/claude-os.db" "data/claude-os.db" "SQLite database"

echo ""
echo -e "${BLUE}2. Restoring configuration files...${NC}"
restore_item "$BACKUP_DIR/.env" ".env" "Environment variables"
restore_item "$BACKUP_DIR/claude-os-config.json" "claude-os-config.json" "Project config"
restore_item "$BACKUP_DIR/claude-os-state.json" "claude-os-state.json" "Session state"
restore_item "$BACKUP_DIR/claude-os-triggers.json" "claude-os-triggers.json" "Trigger phrases"

echo ""
echo -e "${BLUE}3. Restoring uploaded files...${NC}"
restore_item "$BACKUP_DIR/uploads" "data/uploads" "Uploaded documents"

echo ""
echo -e "${BLUE}4. Restoring logs...${NC}"
if [ -d "$BACKUP_DIR/logs" ]; then
    mkdir -p "logs"
    cp "$BACKUP_DIR/logs"/*.log logs/ 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Restored log files"
else
    echo -e "${YELLOW}⚠${NC} No logs in backup"
fi

echo ""
echo -e "${BLUE}5. Checking symlinks...${NC}"
if [ -f "$BACKUP_DIR/symlink_info.txt" ]; then
    echo -e "${YELLOW}Symlink information (for reference):${NC}"
    cat "$BACKUP_DIR/symlink_info.txt"
    echo ""
    echo -e "${BLUE}Note: Symlinks are managed by install.sh${NC}"
    echo -e "If you need to recreate them, run: ${YELLOW}./install.sh${NC}"
fi

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}✓ Restore completed successfully!${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Start Claude OS: ${GREEN}./start.sh${NC}"
echo -e "  2. Verify services: ${GREEN}curl http://localhost:8051/health${NC}"
echo -e "  3. Check UI: ${GREEN}http://localhost:5173${NC}"
echo ""
