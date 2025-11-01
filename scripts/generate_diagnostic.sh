#!/bin/bash
# Generate diagnostic report for troubleshooting

OUTPUT_FILE="${1:-/tmp/claude-os-diagnostic-$(date +%Y%m%d_%H%M%S).txt}"

cat > "$OUTPUT_FILE" << EOF
Claude OS Installation Diagnostic Report
Generated: $(date)
═══════════════════════════════════════════════════════════════

INSTALLATION SUMMARY
───────────────────────────────────────────────────────────────
Status: ${INSTALL_STATUS:-UNKNOWN}
Errors: ${ERROR_COUNT:-0}
Warnings: ${WARNING_COUNT:-0}

${ERROR_LOG}

SYSTEM INFORMATION
───────────────────────────────────────────────────────────────
OS: $(uname -s) $(uname -r)
Architecture: $(uname -m)
Hostname: $(hostname)

PYTHON INFORMATION
───────────────────────────────────────────────────────────────
Default Python: $(python3 --version 2>&1 || echo "Not found")
Python 3.12: $(python3.12 --version 2>&1 || echo "Not found")
Python 3.11: $(python3.11 --version 2>&1 || echo "Not found")

Detected Python: ${PYTHON_VERSION:-Not detected}
Python Command: ${PYTHON_CMD:-Not set}

ENVIRONMENT
───────────────────────────────────────────────────────────────
Claude OS Directory: ${CLAUDE_OS_DIR:-Not set}
User Claude Directory: ${USER_CLAUDE_DIR:-Not set}

Virtual Environment: $([ -d "${CLAUDE_OS_DIR}/venv" ] && echo "Created" || echo "Not created")
$([ -d "${CLAUDE_OS_DIR}/venv" ] && ${CLAUDE_OS_DIR}/venv/bin/python --version 2>&1 || echo "")

DEPENDENCIES
───────────────────────────────────────────────────────────────
$([ -d "${CLAUDE_OS_DIR}/venv" ] && ${CLAUDE_OS_DIR}/venv/bin/pip list 2>&1 | grep -E "(tree-sitter|llama-index|fastapi)" || echo "Virtual environment not available")

FILES CREATED
───────────────────────────────────────────────────────────────
Commands: $(ls -1 ${USER_CLAUDE_DIR}/commands/claude-os-*.md 2>/dev/null | wc -l | xargs) symlinks
Skills: $(ls -1d ${USER_CLAUDE_DIR}/skills/{memory,initialize-project,remember-this} 2>/dev/null | wc -l | xargs) symlinks
start.sh: $([ -f "${CLAUDE_OS_DIR}/start.sh" ] && echo "Created" || echo "Not created")
config.json: $([ -f "${CLAUDE_OS_DIR}/claude-os-config.json" ] && echo "Created" || echo "Not created")
MCP config: $([ -f "${USER_CLAUDE_DIR}/mcp-servers/code-forge.json" ] && echo "Created" || echo "Not created")

SYMLINK DETAILS
───────────────────────────────────────────────────────────────
$(ls -la ${USER_CLAUDE_DIR}/commands/claude-os-*.md 2>&1 | head -10)

$(ls -la ${USER_CLAUDE_DIR}/skills/{memory,initialize-project,remember-this} 2>&1 | head -5)

GIT INFORMATION
───────────────────────────────────────────────────────────────
Git: $(git --version 2>&1 || echo "Not found")
Claude OS Repo: $(cd ${CLAUDE_OS_DIR} 2>/dev/null && git remote -v 2>&1 | head -2 || echo "Not a git repo")

NETWORK CONNECTIVITY
───────────────────────────────────────────────────────────────
GitHub: $(curl -s -o /dev/null -w "%{http_code}" https://github.com --connect-timeout 5 || echo "Failed")
PyPI: $(curl -s -o /dev/null -w "%{http_code}" https://pypi.org --connect-timeout 5 || echo "Failed")

DISK SPACE
───────────────────────────────────────────────────────────────
Available: $(df -h ${CLAUDE_OS_DIR} | tail -1 | awk '{print $4}')
Used by Claude OS: $(du -sh ${CLAUDE_OS_DIR} 2>/dev/null | cut -f1 || echo "Unknown")

RECENT LOGS
───────────────────────────────────────────────────────────────
$(tail -50 ${CLAUDE_OS_DIR}/logs/*.log 2>/dev/null | head -20 || echo "No logs available")

═══════════════════════════════════════════════════════════════
End of Diagnostic Report
═══════════════════════════════════════════════════════════════

To report this issue:
1. Create GitHub issue: https://github.com/brobertsaz/claude-os/issues/new
2. Or run: ./scripts/report_error.sh $OUTPUT_FILE
EOF

echo "$OUTPUT_FILE"
