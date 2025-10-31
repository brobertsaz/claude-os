#!/bin/bash

# save-to-mcp.sh - Save context to Claude OS
# Usage: save-to-mcp.sh "Document Title" "Content" "KB Name (optional)" "Category (optional)"

TITLE="${1:-Captured Context}"
CONTENT="${2:-}"
KB_NAME="${3:-Pistn-project_memories}"
CATEGORY="${4:-General}"

# Sanitize KB name for URL
KB_ENCODED=$(echo "$KB_NAME" | sed 's/ /%20/g')

# Create timestamp
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
DATE=$(date +"%Y-%m-%d")

# Create document
DOC_CONTENT=$(cat <<EOF
# $TITLE

**Date Saved**: $DATE
**Time**: $TIMESTAMP
**Category**: $CATEGORY

---

## Context

$CONTENT

---

*Saved to Claude OS - Your AI Memory System*
EOF
)

# Save locally first
DOC_FILENAME=$(echo "$TITLE" | sed 's/[^a-zA-Z0-9]/_/g').md
DOC_PATH="/tmp/${DOC_FILENAME}"

echo "$DOC_CONTENT" > "$DOC_PATH"

# Upload to Claude OS
API_URL="http://localhost:8051"
RESPONSE=$(curl -s -X POST \
  "$API_URL/api/kb/$KB_ENCODED/upload" \
  -F "file=@$DOC_PATH" \
  -w "\n%{http_code}")

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)

# Check response
if [[ "$HTTP_CODE" =~ ^(200|201)$ ]]; then
  echo "✅ Saved to Claude OS"
  echo "📁 KB: $KB_NAME"
  echo "📄 Title: $TITLE"
  echo "🏷️  Category: $CATEGORY"
  echo "💾 Local: $DOC_PATH"
  exit 0
else
  echo "❌ Failed to save (HTTP $HTTP_CODE)"
  echo "Response: $(echo "$RESPONSE" | sed '$d')"
  exit 1
fi
