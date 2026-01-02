#!/bin/bash

# Claude OS Backup Script
# This script backs up all critical Claude OS data so you can test fresh installations

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}   Claude OS Backup Script${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create backup directory with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="$SCRIPT_DIR/backups/backup_$TIMESTAMP"

echo -e "${YELLOW}Creating backup directory: $BACKUP_DIR${NC}"
mkdir -p "$BACKUP_DIR"

# Function to backup a file or directory
backup_item() {
    local source="$1"
    local dest_name="$2"

    if [ -e "$source" ]; then
        echo -e "${GREEN}✓${NC} Backing up: $source"
        if [ -d "$source" ]; then
            cp -r "$source" "$BACKUP_DIR/$dest_name"
        else
            cp "$source" "$BACKUP_DIR/$dest_name"
        fi
    else
        echo -e "${YELLOW}⚠${NC} Skipping (not found): $source"
    fi
}

echo ""
echo -e "${BLUE}1. Backing up database...${NC}"
backup_item "data/claude-os.db" "claude-os.db"

echo ""
echo -e "${BLUE}2. Backing up configuration files...${NC}"
backup_item ".env" ".env"
backup_item "claude-os-config.json" "claude-os-config.json"
backup_item "claude-os-state.json" "claude-os-state.json"
backup_item "claude-os-triggers.json" "claude-os-triggers.json"

echo ""
echo -e "${BLUE}3. Backing up uploaded files...${NC}"
backup_item "data/uploads" "uploads"

echo ""
echo -e "${BLUE}4. Backing up logs (recent only)...${NC}"
if [ -d "logs" ]; then
    mkdir -p "$BACKUP_DIR/logs"
    # Only backup .log files, skip massive log files
    find logs -name "*.log" -type f -size -10M -exec cp {} "$BACKUP_DIR/logs/" \; 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Backed up recent log files"
fi

echo ""
echo -e "${BLUE}5. Recording symlink state...${NC}"
echo "# Symlinked Commands" > "$BACKUP_DIR/symlink_info.txt"
if [ -d "$HOME/.claude/commands" ]; then
    ls -la "$HOME/.claude/commands" | grep claude-os >> "$BACKUP_DIR/symlink_info.txt" 2>/dev/null || echo "No claude-os commands found" >> "$BACKUP_DIR/symlink_info.txt"
fi

echo "" >> "$BACKUP_DIR/symlink_info.txt"
echo "# Symlinked Skills" >> "$BACKUP_DIR/symlink_info.txt"
if [ -d "$HOME/.claude/skills" ]; then
    ls -la "$HOME/.claude/skills" | grep -E "(memory|initialize-project|memory)" >> "$BACKUP_DIR/symlink_info.txt" 2>/dev/null || echo "No claude-os skills found" >> "$BACKUP_DIR/symlink_info.txt"
fi
echo -e "${GREEN}✓${NC} Recorded symlink information"

echo ""
echo -e "${BLUE}6. Creating backup manifest...${NC}"
cat > "$BACKUP_DIR/MANIFEST.txt" << EOF
Claude OS Backup
Created: $(date)
Backup Directory: $BACKUP_DIR

Contents:
- claude-os.db (SQLite database with all projects, KBs, documents)
- .env (environment variables)
- claude-os-config.json (project configuration)
- claude-os-state.json (session state)
- claude-os-triggers.json (trigger phrases)
- uploads/ (uploaded documents)
- logs/ (recent log files)
- symlink_info.txt (record of ~/.claude/ symlinks)

To restore this backup, run:
  ./restore_claude_os.sh $TIMESTAMP

Database size: $(du -sh data/claude-os.db 2>/dev/null | cut -f1 || echo "N/A")
Total backup size: $(du -sh "$BACKUP_DIR" | cut -f1)
EOF

echo -e "${GREEN}✓${NC} Created manifest file"

# Calculate and display backup size
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}✓ Backup completed successfully!${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "Backup location: ${YELLOW}$BACKUP_DIR${NC}"
echo -e "Backup size: ${YELLOW}$BACKUP_SIZE${NC}"
echo -e "Backup timestamp: ${YELLOW}$TIMESTAMP${NC}"
echo ""
echo -e "${BLUE}To restore this backup later:${NC}"
echo -e "  ${YELLOW}./restore_claude_os.sh $TIMESTAMP${NC}"
echo ""
echo -e "${GREEN}You can now safely test fresh installations!${NC}"
echo ""
