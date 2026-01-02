# Claude OS Backup & Restore Guide

This guide explains how to safely backup and restore your Claude OS installation, perfect for testing fresh installations without losing data.

## Quick Start

### 1. Backup Your Current Setup

```bash
./scripts/backup_claude_os.sh
```

This creates a timestamped backup in `backups/backup_YYYYMMDD_HHMMSS/` containing:
- SQLite database (all projects, knowledge bases, documents)
- Configuration files (.env, JSON configs)
- Uploaded documents
- Recent log files
- Symlink information

**Output example:**
```
Backup location: /Users/iamanmp/Projects/claude-os/backups/backup_20251101_135211
Backup size: 125M
Backup timestamp: 20251101_135211

To restore this backup later:
  ./scripts/restore_claude_os.sh 20251101_135211
```

### 2. Test Fresh Installation

Now you can safely test the installation process:

```bash
# Option 1: Test quick install
./install.sh

# Option 2: Test full setup
./setup.sh
```

### 3. Restore Your Data

If you need to restore your backup:

```bash
./scripts/restore_claude_os.sh 20251101_135211
```

Replace `20251101_135211` with your actual backup timestamp.

---

## What Gets Backed Up?

### Critical Data (Automatically Backed Up)

1. **SQLite Database** (`data/claude-os.db`)
   - All projects
   - All knowledge bases
   - All documents and embeddings
   - Search history
   - Typically 100-200MB

2. **Configuration Files**
   - `.env` - Environment variables (Ollama settings, API keys, etc.)
   - `claude-os-config.json` - Project configuration
   - `claude-os-state.json` - Current session state
   - `claude-os-triggers.json` - Custom trigger phrases

3. **Uploaded Documents** (`data/uploads/`)
   - Any files uploaded through the UI

4. **Recent Logs** (`logs/`)
   - Recent log files (< 10MB each)
   - Useful for debugging

5. **Symlink Information**
   - Record of `~/.claude/commands/` symlinks
   - Record of `~/.claude/skills/` symlinks
   - For reference only (recreated by `install.sh`)

### What's NOT Backed Up (No Need)

- `node_modules/` - Reinstalled from package.json
- `venv/` - Recreated during installation
- Python packages - Reinstalled from requirements.txt
- Ollama models - Remain in system location
- Templates - Already in git repository
- Large log files (> 10MB)

---

## Detailed Usage

### Backup Command

```bash
./scripts/backup_claude_os.sh
```

**What it does:**
1. Creates timestamped backup directory
2. Copies all critical files
3. Records symlink state
4. Creates manifest file
5. Shows backup summary

**No arguments needed** - timestamps are automatic.

### Restore Command

```bash
./scripts/restore_claude_os.sh <timestamp>
```

**Examples:**
```bash
# Restore specific backup
./scripts/restore_claude_os.sh 20251101_135211

# List available backups
./scripts/restore_claude_os.sh
```

**What it does:**
1. Verifies backup exists
2. Shows manifest
3. Asks for confirmation (press Enter to continue)
4. Restores all files
5. Provides next steps

**⚠️ WARNING:** Restore will **overwrite** your current data! Make a new backup first if you want to keep current state.

---

## Testing Fresh Installations

### Recommended Workflow

1. **Backup first:**
   ```bash
   ./scripts/backup_claude_os.sh
   ```

2. **Stop all services:**
   ```bash
   ./stop_all_services.sh
   ```

3. **Clean up (optional but thorough):**
   ```bash
   # Remove symlinks (will be recreated)
   rm ~/.claude/commands/claude-os-*.md
   rm ~/.claude/skills/memory
   rm ~/.claude/skills/initialize-project
   rm ~/.claude/skills/memory

   # Remove virtual environment
   rm -rf venv venv_py312 venv_py313
   ```

4. **Test installation:**
   ```bash
   # Test quick install
   ./install.sh

   # OR test full setup
   ./setup.sh
   ```

5. **Verify it works:**
   ```bash
   # Start services
   ./start.sh

   # Check health
   curl http://localhost:8051/health

   # Check UI
   open http://localhost:5173
   ```

6. **If something goes wrong, restore:**
   ```bash
   ./scripts/restore_claude_os.sh 20251101_135211
   ./start.sh
   ```

---

## Common Scenarios

### Scenario 1: Test install.sh for a user report

```bash
# 1. Backup everything
./scripts/backup_claude_os.sh

# 2. Clean installation (keep data, test scripts)
rm -rf venv
rm ~/.claude/commands/claude-os-*.md
rm ~/.claude/skills/{memory,initialize-project,memory}

# 3. Test install as if you're a new user
./install.sh

# 4. Restore your data (database, configs)
./scripts/restore_claude_os.sh <timestamp>
./start.sh
```

### Scenario 2: Test setup.sh from scratch

```bash
# 1. Backup everything
./scripts/backup_claude_os.sh

# 2. Full clean (simulate fresh machine)
./stop_all_services.sh
rm -rf venv venv_*
rm -rf node_modules
rm -rf data/claude-os.db
rm ~/.claude/commands/claude-os-*.md
rm ~/.claude/skills/{memory,initialize-project,memory}

# 3. Test full setup
./setup.sh
./start_all_services.sh

# 4. Restore your data
./scripts/restore_claude_os.sh <timestamp>
./start.sh
```

### Scenario 3: Test project initialization

```bash
# 1. Backup current state
./scripts/backup_claude_os.sh

# 2. Create test project
cd ~/test-project
/claude-os-init  # In Claude Code

# 3. If something breaks, restore
cd ~/Projects/claude-os
./scripts/restore_claude_os.sh <timestamp>
```

---

## Backup Best Practices

### When to Backup

- **Before testing installations** - Always!
- **Before major changes** - Modifying core files
- **Weekly** - If actively developing
- **Before upgrades** - Git pull, dependency updates

### Backup Management

```bash
# List all backups
ls -lh backups/

# Check backup size
du -sh backups/backup_*

# Remove old backups (keep last 5)
cd backups
ls -t | tail -n +6 | xargs rm -rf

# Archive old backups
tar -czf backups_archive_2025.tar.gz backups/
```

### Multiple Backups

The backup script creates **new backups** each time - it never overwrites:

```bash
./scripts/backup_claude_os.sh  # Creates backup_20251101_135211
./scripts/backup_claude_os.sh  # Creates backup_20251101_140530
./scripts/backup_claude_os.sh  # Creates backup_20251101_141005
```

You can safely run it multiple times!

---

## Troubleshooting

### "Backup location not found"

```bash
# List available backups
ls -1 backups/ | grep backup_

# Use exact timestamp from list
./scripts/restore_claude_os.sh 20251101_135211
```

### "Permission denied"

```bash
# Make scripts executable
chmod +x scripts/backup_claude_os.sh scripts/restore_claude_os.sh
```

### "Database locked" during backup

```bash
# Stop services first
./stop_all_services.sh

# Then backup
./scripts/backup_claude_os.sh
```

### Restore doesn't fix everything

The restore script restores **data** but not:
- Python packages (run `pip install -r requirements.txt`)
- Node modules (run `cd frontend && npm install`)
- Symlinks (run `./install.sh`)
- Running services (run `./start.sh`)

**Full recovery process:**
```bash
./scripts/restore_claude_os.sh <timestamp>
./install.sh  # Recreate symlinks
./start.sh    # Start services
```

---

## File Locations Reference

### Backed Up Locations

```
claude-os/
├── data/
│   ├── claude-os.db          ← BACKED UP (critical!)
│   └── uploads/              ← BACKED UP
├── .env                      ← BACKED UP (has secrets)
├── claude-os-config.json     ← BACKED UP
├── claude-os-state.json      ← BACKED UP
├── claude-os-triggers.json   ← BACKED UP
└── logs/                     ← BACKED UP (recent only)

~/.claude/
├── commands/claude-os-*.md   ← Symlink info recorded
└── skills/{memory,etc}       ← Symlink info recorded
```

### Backup Storage Location

```
claude-os/
└── backups/
    ├── backup_20251101_135211/
    │   ├── claude-os.db
    │   ├── .env
    │   ├── claude-os-config.json
    │   ├── claude-os-state.json
    │   ├── claude-os-triggers.json
    │   ├── uploads/
    │   ├── logs/
    │   ├── symlink_info.txt
    │   └── MANIFEST.txt
    └── backup_20251101_140530/
        └── ...
```

---

## Security Notes

### .env File Contains Secrets

The `.env` file may contain:
- `CLAUDE_OS_PASSWORD` - Admin password
- `CLAUDE_OS_SECRET_KEY` - JWT secret
- API keys (if using OpenAI)

**Backups are stored locally** in `backups/` directory.

**⚠️ DO NOT:**
- Commit backups to git (.gitignore already excludes them)
- Share backup directories
- Store backups in public locations

### Recommended Backup Security

```bash
# Encrypt sensitive backups
tar -czf - backups/backup_20251101_135211 | \
  openssl enc -aes-256-cbc -pbkdf2 -out backup_encrypted.tar.gz.enc

# Decrypt when needed
openssl enc -aes-256-cbc -pbkdf2 -d -in backup_encrypted.tar.gz.enc | \
  tar -xzf -
```

---

## Summary

**You now have:**

✅ `backup_claude_os.sh` - Backup all your data
✅ `restore_claude_os.sh` - Restore from backup
✅ Safe testing workflow
✅ Your first backup created!

**Next steps:**

1. Your backup is ready: `backups/backup_20251101_135211/`
2. You can safely test `./install.sh`
3. If anything breaks: `./scripts/restore_claude_os.sh 20251101_135211`
4. Test away with confidence! 🚀

---

**Questions?**
- Check `backups/backup_*/MANIFEST.txt` for backup contents
- Run `./scripts/restore_claude_os.sh` with no arguments to list backups
- Backups are fast (30 seconds) - backup often!
