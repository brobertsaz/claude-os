# Claude OS Skills Management

Manage Claude Code skills - list, install from templates, create custom, and configure.

## Commands

```
/claude-os-skills                    - List all skills (global + project)
/claude-os-skills templates          - Show available templates
/claude-os-skills install <name>     - Install template to project
/claude-os-skills create             - Create a custom skill
/claude-os-skills view <name>        - View skill details
/claude-os-skills delete <name>      - Delete a project skill
```

---

## LIST SKILLS (default)

When user runs `/claude-os-skills` with no arguments:

**Step 1: Get Skills**
```
mcp__code-forge__list_skills
  project_path: "{cwd}"
```

**Step 2: Display Results**
```
═══════════════════════════════════════
📚 CLAUDE CODE SKILLS
═══════════════════════════════════════

🌐 GLOBAL SKILLS (always available)
────────────────────────────────────
  ✓ memory - Save and recall information
  ✓ remember-this - Auto-save on trigger phrases

📁 PROJECT SKILLS ({cwd})
────────────────────────────────────
  ✓ rails-backend - Rails patterns and service objects
  ✓ rspec - RSpec testing patterns

💡 TIP: Run '/claude-os-skills templates' to see available templates
═══════════════════════════════════════
```

---

## LIST TEMPLATES

When user runs `/claude-os-skills templates`:

**Step 1: Get Templates**
```
mcp__code-forge__list_skill_templates
```

**Step 2: Display by Category**
```
═══════════════════════════════════════
📦 SKILL TEMPLATES
═══════════════════════════════════════

GENERAL
────────────────────────────────────
  • initialize-project
    Analyze codebase, generate docs
    Tags: onboarding, analysis

RAILS
────────────────────────────────────
  • rails-backend
    Service objects, ActiveRecord, APIs
    Tags: ruby, rails, backend

REACT
────────────────────────────────────
  • react-patterns
    Hooks, TypeScript, components
    Tags: react, typescript, frontend

TESTING
────────────────────────────────────
  • rspec
    RSpec patterns, factories
    Tags: ruby, rspec, tdd

───────────────────────────────────────
Install with: /claude-os-skills install <name>
═══════════════════════════════════════
```

---

## INSTALL TEMPLATE

When user runs `/claude-os-skills install <name>`:

**Step 1: Install Template**
```
mcp__code-forge__install_skill_template
  template_name: "<name>"
  project_path: "{cwd}"
```

**Step 2: Confirm**
```
✓ Installed '<name>' to {cwd}/.claude/skills/<name>

The skill is now available in this project!

To use it, Claude Code will automatically load it when relevant,
or you can explicitly invoke it with: skill: <name>
```

---

## CREATE CUSTOM SKILL

When user runs `/claude-os-skills create`:

**Step 1: Gather Information**

Ask the user for:
1. Skill name (e.g., "deployment", "code-review")
2. Description (one sentence)
3. Content (the skill instructions)

**Step 2: Create Skill**
```
mcp__code-forge__create_skill
  name: "<name>"
  description: "<description>"
  content: "<content>"
  project_path: "{cwd}"
```

**Step 3: Confirm**
```
✓ Created skill '<name>' in {cwd}/.claude/skills/<name>

The skill is now available in this project!
```

---

## VIEW SKILL

When user runs `/claude-os-skills view <name>`:

**Step 1: Get Skill Details**

First try project scope, then global:
```
mcp__code-forge__get_skill
  name: "<name>"
  scope: "project"
  project_path: "{cwd}"
```

If not found:
```
mcp__code-forge__get_skill
  name: "<name>"
  scope: "global"
```

**Step 2: Display Skill**
```
═══════════════════════════════════════
📖 SKILL: <name>
═══════════════════════════════════════

Scope: project
Source: template
Category: rails
Tags: ruby, rails, backend

─────────────────────────────────────

<skill content here>

═══════════════════════════════════════
```

---

## DELETE SKILL

When user runs `/claude-os-skills delete <name>`:

**Step 1: Confirm with User**
```
⚠️  Are you sure you want to delete the '<name>' skill?

This will remove it from {cwd}/.claude/skills/<name>

Type 'yes' to confirm, or anything else to cancel.
```

**Step 2: Delete if Confirmed**
```
mcp__code-forge__delete_skill
  name: "<name>"
  project_path: "{cwd}"
```

**Step 3: Confirm**
```
✓ Deleted skill '<name>' from project
```

**Note:** Cannot delete global skills (memory, remember-this). These are core to Claude OS.

---

## SKILL LOCATIONS

- **Global Skills**: `~/.claude/skills/`
  - Available in ALL projects
  - Core skills: memory, remember-this

- **Project Skills**: `{project}/.claude/skills/`
  - Available only in that project
  - Installed from templates or custom created

- **Templates**: `claude-os/templates/skill-library/`
  - Categorized templates to install

---

## TIPS

1. **Start with templates** - Install what you need per-project
2. **Keep global minimal** - Only core skills should be global
3. **Customize templates** - After installing, edit for your needs
4. **Create custom skills** - Document project-specific patterns

---

## EXAMPLES

```
/claude-os-skills
→ Lists all global and project skills

/claude-os-skills templates
→ Shows available templates by category

/claude-os-skills install rails-backend
→ Installs Rails patterns to current project

/claude-os-skills create
→ Interactive custom skill creation

/claude-os-skills view rails-backend
→ Shows full skill content

/claude-os-skills delete old-skill
→ Removes skill from project (after confirmation)
```
