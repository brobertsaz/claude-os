#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# DEPRECATED: This script now redirects to setup-claude-os.sh
# ═══════════════════════════════════════════════════════════════════════════
#
# For the best experience, run:
#   ./setup-claude-os.sh
#
# This alias exists for backwards compatibility with existing documentation.
# ═══════════════════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "┌────────────────────────────────────────────────────────────────┐"
echo "│  ℹ️  install.sh is now setup-claude-os.sh                      │"
echo "│                                                                │"
echo "│  Redirecting to the new unified installer...                   │"
echo "└────────────────────────────────────────────────────────────────┘"
echo ""
sleep 1

exec "${SCRIPT_DIR}/setup-claude-os.sh" "$@"
