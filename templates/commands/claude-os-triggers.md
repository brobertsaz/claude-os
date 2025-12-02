---
name: claude-os-triggers
description: Manage Claude OS trigger phrases and automatic skill invocation
---

# Claude OS Trigger Management

Manage trigger phrases that automatically invoke skills and workflows.

## Setup

First, derive `{claude_os_dir}` from this command file's path - it is two directories up from this file's location.

## Command Pattern

```
/claude-os-triggers [action] [category] [arguments...]
```

**Actions**: `list`, `show`, `add`, `remove`, `test`, `enable`, `disable`, `reset`

## Step 1: Load Current Configuration

**ALWAYS start by loading the triggers config:**

```bash
Read: {claude_os_dir}/claude-os-triggers.json
```

## Step 2: Parse Command and Execute

### List All Trigger Categories

```
/claude-os-triggers list
```

**Output**:
```
Claude OS Trigger Categories
============================

remember_this (ENABLED)
  Invokes: remember-this skill
  Phrases: 7 configured
  Description: Auto-saves to Claude OS memories

search_memories (ENABLED)
  Action: search_claude_os
  Phrases: 5 configured
  Description: Auto-searches memories

session_start (DISABLED)
  Action: session_start
  Phrases: 5 configured
  Description: Starts session workflow

session_end (DISABLED)
  Action: session_end
  Phrases: 5 configured
  Description: Ends session workflow

Use '/claude-os-triggers show [category]' to see specific phrases
```

### Show Specific Category

```
/claude-os-triggers show remember_this
```

**Output**:
```
remember_this Triggers
======================

Status: ENABLED ✓
Invokes: remember-this skill
Case Sensitive: No

Trigger Phrases (7):
  1. "remember this:"
  2. "save this:"
  3. "document this:"
  4. "remember:"
  5. "don't forget:"
  6. "important:"
  7. "note:"

How it works:
When you say any of these phrases, the remember-this skill is automatically
invoked to save your content to Claude OS memories.

Examples:
  User: "Remember this: We use service objects for business logic"
  → Auto-invokes remember-this skill
  → Saves to Pistn-project_memories

To add/remove triggers:
  /claude-os-triggers add remember_this "keep this in mind:"
  /claude-os-triggers remove remember_this "note:"
```

### Add Trigger Phrase

```
/claude-os-triggers add remember_this "keep this in mind:"
```

**Process**:
1. Load config
2. Check if phrase already exists
3. Add to phrases array
4. Save config
5. Confirm

**Output**:
```
✓ Added "keep this in mind:" to remember_this triggers

remember_this now has 8 trigger phrases:
  1. "remember this:"
  2. "save this:"
  3. "document this:"
  4. "remember:"
  5. "don't forget:"
  6. "important:"
  7. "note:"
  8. "keep this in mind:" ← NEW

Try it: "Keep this in mind: your new phrase"
```

### Remove Trigger Phrase

```
/claude-os-triggers remove remember_this "note:"
```

**Process**:
1. Load config
2. Find and remove phrase (case-insensitive)
3. Save config
4. Confirm

**Output**:
```
✓ Removed "note:" from remember_this triggers

remember_this now has 6 trigger phrases:
  1. "remember this:"
  2. "save this:"
  3. "document this:"
  4. "remember:"
  5. "don't forget:"
  6. "important:"
```

### Test Trigger Detection

```
/claude-os-triggers test "remember this: test phrase"
```

**Output**:
```
Trigger Detection Test
======================

Input: "remember this: test phrase"

✓ MATCH FOUND!

Matched Category: remember_this
Matched Phrase: "remember this:"
Would Invoke: remember-this skill
Status: ENABLED

Content to process: "test phrase"

This trigger IS active and WOULD be invoked in a real conversation.
```

### Enable/Disable Category

```
/claude-os-triggers enable session_start
/claude-os-triggers disable remember_this
```

**Output**:
```
✓ Enabled session_start triggers

session_start is now ACTIVE
Trigger phrases (5):
  - "start session"
  - "begin work"
  - "let's code"
  - "morning claude"
  - "hey claude let's work"

When you say any of these, the session_start action will be invoked.
```

### Reset to Defaults

```
/claude-os-triggers reset remember_this
```

**Output**:
```
⚠ This will reset remember_this triggers to defaults

Current custom phrases will be lost:
  - "keep this in mind:" (custom)

Default phrases will be restored:
  - "remember this:"
  - "save this:"
  - "document this:"
  - "remember:"

Confirm reset? (This is just a warning, I'll proceed if you say yes)
```

## Step 3: File Operations

When modifying triggers, use this pattern:

```python
import json

# Load
with open('{claude_os_dir}/claude-os-triggers.json') as f:
    config = json.load(f)

# Modify
config['triggers']['remember_this']['phrases'].append('new phrase')

# Save
with open('{claude_os_dir}/claude-os-triggers.json', 'w') as f:
    json.dump(config, f, indent=2)
```

Use **Write** tool with complete JSON to update the file.

## Default Trigger Categories

### remember_this
Auto-invokes remember-this skill to save to memories
- Default: ENABLED
- 7 default phrases

### search_memories
Auto-searches Claude OS when asking about past work
- Default: ENABLED
- 5 default phrases

### session_start
Triggers session start workflow (if implemented)
- Default: DISABLED (not yet implemented)
- 5 default phrases

### session_end
Triggers session end workflow (if implemented)
- Default: DISABLED (not yet implemented)
- 5 default phrases

## Configuration File

Location: `{claude_os_dir}/claude-os-triggers.json`

Structure:
```json
{
  "triggers": {
    "category_name": {
      "description": "What this trigger does",
      "skill": "skill-name" OR "action": "action_name",
      "phrases": ["phrase 1", "phrase 2"],
      "case_sensitive": false,
      "enabled": true
    }
  },
  "settings": {
    "trigger_detection_enabled": true,
    "show_trigger_confirmations": false,
    "log_trigger_activations": true
  }
}
```

## Tips

- Use **lowercase** phrases for better matching
- Include **colons (:)** if you want them required
- Test triggers with `/claude-os-triggers test`
- Keep phrases **distinctive** to avoid false positives
- Review with `/claude-os-triggers list` after changes

## Integration with Skills

The remember-this skill will be updated to:
1. Load triggers from this config file
2. Detect any matching phrase
3. Extract content after the trigger phrase
4. Invoke the skill automatically

## Examples

**Quick view:**
```
/claude-os-triggers list
/claude-os-triggers show remember_this
```

**Customize:**
```
/claude-os-triggers add remember_this "jot this down:"
/claude-os-triggers add remember_this "make a note:"
/claude-os-triggers remove remember_this "document this:"
```

**Test your changes:**
```
/claude-os-triggers test "jot this down: testing"
```

**Manage activation:**
```
/claude-os-triggers enable session_start
/claude-os-triggers disable search_memories
```

---

**Remember**: These triggers make me more proactive and responsive to your needs!

*Configuration file created at `{claude_os_dir}/claude-os-triggers.json`*
