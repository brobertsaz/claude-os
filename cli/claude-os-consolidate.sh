#!/bin/bash
# Claude OS Consolidation Script
# Moves commands and skills from ~/.claude to Claude OS templates/

set -e  # Exit on error

CLAUDE_OS_DIR="/Users/iamanmp/Projects/claude-os"
USER_CLAUDE_DIR="/Users/iamanmp/.claude"
TEMPLATES_DIR="${CLAUDE_OS_DIR}/templates"

echo "🔧 Claude OS Consolidation Script"
echo "=================================="
echo ""
echo "This script will:"
echo "  1. Move Claude OS commands from ~/.claude/commands/ to templates/commands/"
echo "  2. Move Claude OS skills from ~/.claude/skills/ to templates/skills/"
echo "  3. Create symlinks so everything still works"
echo "  4. Update any hardcoded paths"
echo ""

# Confirm before proceeding
read -p "Continue? [Y/n] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]] && [[ ! -z $REPLY ]]; then
    echo "❌ Aborted"
    exit 1
fi

# Create templates directories if they don't exist
echo "📁 Creating template directories..."
mkdir -p "${TEMPLATES_DIR}/commands"
mkdir -p "${TEMPLATES_DIR}/skills"
mkdir -p "${TEMPLATES_DIR}/agents"

# List of Claude OS commands to move
CLAUDE_OS_COMMANDS=(
    "claude-os-list.md"
    "claude-os-remember.md"
    "claude-os-save.md"
    "claude-os-search.md"
    "claude-os-session.md"
    "claude-os-triggers.md"
    "claude-os-init.md"
)

# List of Claude OS skills to move
CLAUDE_OS_SKILLS=(
    "initialize-project"
    "remember-this"
    "memory"
)

echo ""
echo "📦 Moving commands..."
for cmd in "${CLAUDE_OS_COMMANDS[@]}"; do
    SRC="${USER_CLAUDE_DIR}/commands/${cmd}"
    DEST="${TEMPLATES_DIR}/commands/${cmd}"

    if [ -f "$SRC" ]; then
        # Check if it's already a symlink
        if [ -L "$SRC" ]; then
            echo "   ⏭️  ${cmd} (already a symlink)"
        else
            # Move to templates
            echo "   ➡️  Moving ${cmd}"
            mv "$SRC" "$DEST"

            # Create symlink back
            ln -s "$DEST" "$SRC"
            echo "   🔗 Created symlink"
        fi
    elif [ -f "$DEST" ]; then
        echo "   ✅ ${cmd} (already in templates)"

        # Create symlink if it doesn't exist
        if [ ! -L "$SRC" ]; then
            ln -s "$DEST" "$SRC"
            echo "   🔗 Created symlink"
        fi
    else
        echo "   ⚠️  ${cmd} not found (skipping)"
    fi
done

echo ""
echo "📦 Moving skills..."
for skill in "${CLAUDE_OS_SKILLS[@]}"; do
    SRC="${USER_CLAUDE_DIR}/skills/${skill}"
    DEST="${TEMPLATES_DIR}/skills/${skill}"

    if [ -d "$SRC" ]; then
        # Check if it's already a symlink
        if [ -L "$SRC" ]; then
            echo "   ⏭️  ${skill}/ (already a symlink)"
        else
            # Move to templates
            echo "   ➡️  Moving ${skill}/"
            mv "$SRC" "$DEST"

            # Create symlink back
            ln -s "$DEST" "$SRC"
            echo "   🔗 Created symlink"
        fi
    elif [ -d "$DEST" ]; then
        echo "   ✅ ${skill}/ (already in templates)"

        # Create symlink if it doesn't exist
        if [ ! -L "$SRC" ]; then
            ln -s "$DEST" "$SRC"
            echo "   🔗 Created symlink"
        fi
    else
        echo "   ⚠️  ${skill}/ not found (skipping)"
    fi
done

echo ""
echo "🔧 Updating hardcoded paths in skills..."

# Update paths in initialize-project skill
INIT_SKILL_MD="${TEMPLATES_DIR}/skills/initialize-project/SKILL.md"
if [ -f "$INIT_SKILL_MD" ]; then
    # Backup original
    cp "$INIT_SKILL_MD" "${INIT_SKILL_MD}.backup"

    # Replace hardcoded user paths with relative paths
    sed -i.bak 's|/Users/iamanmp/.claude/|~/.claude/|g' "$INIT_SKILL_MD"
    rm -f "${INIT_SKILL_MD}.bak"
    echo "   ✅ Updated initialize-project/SKILL.md"
fi

# Update paths in remember-this skill
REMEMBER_SKILL_MD="${TEMPLATES_DIR}/skills/remember-this/SKILL.md"
if [ -f "$REMEMBER_SKILL_MD" ]; then
    # Backup original
    cp "$REMEMBER_SKILL_MD" "${REMEMBER_SKILL_MD}.backup"

    # Replace hardcoded user paths
    sed -i.bak 's|/Users/iamanmp/.claude/|~/.claude/|g' "$REMEMBER_SKILL_MD"
    rm -f "${REMEMBER_SKILL_MD}.bak"
    echo "   ✅ Updated remember-this/SKILL.md"
fi

echo ""
echo "✨ Consolidation complete!"
echo ""
echo "📂 Templates location: ${TEMPLATES_DIR}"
echo "🔗 Symlinks created in: ${USER_CLAUDE_DIR}"
echo ""
echo "Next steps:"
echo "  1. Review templates/ directory"
echo "  2. Test commands still work: /claude-os-list"
echo "  3. Commit changes to Claude OS repo"
echo "  4. Share with coworkers!"
echo ""
echo "To install on a new machine:"
echo "  1. Clone Claude OS repo"
echo "  2. Run: ./install.sh"
echo "  3. Commands and skills will be symlinked automatically"
