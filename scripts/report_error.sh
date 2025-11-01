#!/bin/bash
# Error Reporting Script for Claude OS
# Generates diagnostic report and optionally sends to GitHub or webhook

set +e  # Don't exit on errors in this script

REPORT_FILE="${1:-/tmp/claude-os-error-report.txt}"
GITHUB_REPO="brobertsaz/claude-os"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}   Claude OS Error Report${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

# Check if report file exists
if [ ! -f "$REPORT_FILE" ]; then
    echo -e "${RED}Error: Report file not found: $REPORT_FILE${NC}"
    exit 1
fi

# Show report summary
echo -e "${YELLOW}Report generated:${NC}"
echo "$(head -20 "$REPORT_FILE")"
echo ""
echo "Full report: $REPORT_FILE"
echo ""

# Ask user what to do
echo -e "${BLUE}How would you like to report this issue?${NC}"
echo ""
echo "  1. Create GitHub Issue (public, helps community)"
echo "  2. Copy to clipboard (paste in GitHub/Discord manually)"
echo "  3. Save to file only (report later)"
echo "  4. Exit (don't report)"
echo ""
read -p "Choose option (1-4): " choice

case "$choice" in
    1)
        echo ""
        echo -e "${YELLOW}Creating GitHub Issue...${NC}"
        echo ""

        # Check if gh CLI is installed
        if ! command -v gh &> /dev/null; then
            echo -e "${RED}GitHub CLI (gh) not installed.${NC}"
            echo ""
            echo "Install it with:"
            echo "  • macOS: brew install gh"
            echo "  • Linux: https://github.com/cli/cli#installation"
            echo ""
            echo "Or choose option 2 to copy the report manually."
            exit 1
        fi

        # Check if authenticated
        if ! gh auth status &> /dev/null; then
            echo -e "${YELLOW}GitHub CLI not authenticated.${NC}"
            echo ""
            echo "Authenticate with:"
            echo "  gh auth login"
            echo ""
            read -p "Authenticate now? (y/n): " auth_choice
            if [ "$auth_choice" = "y" ]; then
                gh auth login
            else
                echo "Skipping GitHub issue creation."
                exit 0
            fi
        fi

        # Create issue
        ISSUE_TITLE="[Install Error] $(head -1 "$REPORT_FILE" | cut -d':' -f2- | xargs)"
        ISSUE_BODY="$(cat "$REPORT_FILE")"

        echo ""
        echo "Creating issue with title:"
        echo "  $ISSUE_TITLE"
        echo ""

        ISSUE_URL=$(gh issue create \
            --repo "$GITHUB_REPO" \
            --title "$ISSUE_TITLE" \
            --body "$ISSUE_BODY" \
            --label "installation,bug" 2>&1)

        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✓ Issue created successfully!${NC}"
            echo ""
            echo "View at: $ISSUE_URL"
            echo ""
            echo "The maintainers will be notified."
        else
            echo ""
            echo -e "${RED}Failed to create issue.${NC}"
            echo "You can still create it manually at:"
            echo "  https://github.com/$GITHUB_REPO/issues/new"
        fi
        ;;

    2)
        echo ""
        echo -e "${YELLOW}Copying report to clipboard...${NC}"

        # Try different clipboard commands
        if command -v pbcopy &> /dev/null; then
            cat "$REPORT_FILE" | pbcopy
            echo -e "${GREEN}✓ Copied to clipboard!${NC}"
        elif command -v xclip &> /dev/null; then
            cat "$REPORT_FILE" | xclip -selection clipboard
            echo -e "${GREEN}✓ Copied to clipboard!${NC}"
        elif command -v xsel &> /dev/null; then
            cat "$REPORT_FILE" | xsel --clipboard
            echo -e "${GREEN}✓ Copied to clipboard!${NC}"
        else
            echo -e "${RED}No clipboard tool found.${NC}"
            echo ""
            echo "Report saved at: $REPORT_FILE"
            echo ""
            echo "You can view it with:"
            echo "  cat $REPORT_FILE"
        fi

        echo ""
        echo "Create issue manually at:"
        echo "  https://github.com/$GITHUB_REPO/issues/new"
        ;;

    3)
        echo ""
        echo -e "${GREEN}Report saved to: $REPORT_FILE${NC}"
        echo ""
        echo "You can report this later by running:"
        echo "  ./scripts/report_error.sh $REPORT_FILE"
        ;;

    4)
        echo ""
        echo "Exiting without reporting."
        ;;

    *)
        echo ""
        echo -e "${RED}Invalid option.${NC}"
        exit 1
        ;;
esac

echo ""
