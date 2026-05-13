#Requires -Version 5.1
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                      Claude OS Installer for Windows                      ║
# ║                                                                           ║
# ║  Beautiful, unified setup for Claude's AI memory system                   ║
# ║  Uses UV for fast Python package management                               ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

param(
    [switch]$DryRun,
    [switch]$Force,
    [switch]$Help,
    [switch]$Version
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

$CLAUDE_OS_VERSION = "2.2.0"
$CLAUDE_OS_DIR = $PSScriptRoot
$USER_CLAUDE_DIR = Join-Path $env:USERPROFILE ".claude"
$TEMPLATES_DIR = Join-Path $CLAUDE_OS_DIR "templates"

$DEFAULT_LLM_MODEL = "llama3.2:3b"
$DEFAULT_EMBED_MODEL = "nomic-embed-text"
$FULL_LLM_MODEL = "llama3.1:8b"

# ═══════════════════════════════════════════════════════════════════════════
# COLORS & OUTPUT HELPERS
# ═══════════════════════════════════════════════════════════════════════════

function Write-Success { param($msg) Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn    { param($msg) Write-Host "  [!!] $msg" -ForegroundColor Yellow }
function Write-Err     { param($msg) Write-Host "  [XX] $msg" -ForegroundColor Red }
function Write-Info    { param($msg) Write-Host "  [..] $msg" -ForegroundColor Cyan }

function Write-Section {
    param($title)
    Write-Host ""
    Write-Host ("=" * 62) -ForegroundColor Blue
    Write-Host "  $title" -ForegroundColor Blue
    Write-Host ("=" * 62) -ForegroundColor Blue
    Write-Host ""
}

function Write-DryRun { param($msg) Write-Host "  [DRY-RUN] $msg" -ForegroundColor Yellow }

function Show-Banner {
    Clear-Host
    Write-Host ""
    Write-Host @"
     ██████╗██╗      █████╗ ██╗   ██╗██████╗ ███████╗     ██████╗ ███████╗
    ██╔════╝██║     ██╔══██╗██║   ██║██╔══██╗██╔════╝    ██╔═══██╗██╔════╝
    ██║     ██║     ███████║██║   ██║██║  ██║█████╗      ██║   ██║███████╗
    ██║     ██║     ██╔══██║██║   ██║██║  ██║██╔══╝      ██║   ██║╚════██║
    ╚██████╗███████╗██║  ██║╚██████╔╝██████╔╝███████╗    ╚██████╔╝███████║
     ╚═════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝     ╚═════╝ ╚══════╝
"@ -ForegroundColor Cyan
    Write-Host "                    Your AI Memory System * v$CLAUDE_OS_VERSION (Windows)" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "    Claude CLI + Claude OS = Invincible! " -ForegroundColor White
    Write-Host ""
}

function Show-Help {
    Write-Host ""
    Write-Host "Claude OS Installer v$CLAUDE_OS_VERSION (Windows)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor White
    Write-Host "  .\setup-claude-os.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:" -ForegroundColor White
    Write-Host "  -Help       Show this help message"
    Write-Host "  -DryRun     Show what would be done without doing it"
    Write-Host "  -Force      Skip confirmation prompts"
    Write-Host "  -Version    Show version number"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor White
    Write-Host "  .\setup-claude-os.ps1              # Normal installation"
    Write-Host "  .\setup-claude-os.ps1 -DryRun      # Preview changes"
    Write-Host ""
}

# ═══════════════════════════════════════════════════════════════════════════
# PORT & PROCESS HELPERS
# ═══════════════════════════════════════════════════════════════════════════

function Test-Port {
    param([int]$Port)
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $tcp.Connect("127.0.0.1", $Port)
        $tcp.Close()
        return $true
    } catch {
        return $false
    }
}

function Stop-ProcessOnPort {
    param([int]$Port)
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
        $proc = $conn | Select-Object -First 1 -ExpandProperty OwningProcess
        if ($proc -and $proc -ne 0) {
            Stop-Process -Id $proc -Force -ErrorAction SilentlyContinue
        }
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# UV SETUP
# ═══════════════════════════════════════════════════════════════════════════

function Install-UV {
    Write-Section "Checking UV (Python Package Manager)"

    if (Get-Command uv -ErrorAction SilentlyContinue) {
        $uvVersion = (uv --version 2>&1)
        Write-Success "UV already installed: $uvVersion"
        return
    }

    Write-Info "UV not found. Installing UV..."

    # Try winget first
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Info "Installing UV via winget..."
        winget install --id=astral-sh.uv -e --silent 2>&1 | Out-Null
        # Refresh PATH
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
                    [System.Environment]::GetEnvironmentVariable("PATH", "User")
    }

    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Info "Trying UV installer script..."
        Write-Warn "This will download and execute a remote script from https://astral.sh/uv/install.ps1"
        if (-not $Force) {
            $confirm = Read-Host "  Proceed? [Y/n]"
            if ($confirm -and $confirm -notmatch "^[Yy]") {
                Write-Err "UV install skipped. Please install UV manually:"
                Write-Host "    winget install astral-sh.uv" -ForegroundColor Cyan
                Write-Host "    - or -" -ForegroundColor DarkGray
                Write-Host "    irm https://astral.sh/uv/install.ps1 | iex" -ForegroundColor Cyan
                exit 1
            }
        }
        try {
            $installScript = (Invoke-WebRequest "https://astral.sh/uv/install.ps1" -UseBasicParsing).Content
            Invoke-Expression $installScript 2>&1 | Out-Null
            # Refresh PATH to include UV's install location (~/.local/bin or ~/.cargo/bin)
            $env:PATH = "$env:USERPROFILE\.local\bin;$env:USERPROFILE\.cargo\bin;$env:PATH"
        } catch {
            Write-Err "Could not auto-install UV."
            Write-Host ""
            Write-Host "  Please install UV manually:" -ForegroundColor White
            Write-Host "    winget install astral-sh.uv" -ForegroundColor Cyan
            Write-Host "    - or -" -ForegroundColor DarkGray
            Write-Host "    irm https://astral.sh/uv/install.ps1 | iex" -ForegroundColor Cyan
            Write-Host ""
            exit 1
        }
    }

    if (Get-Command uv -ErrorAction SilentlyContinue) {
        $uvVersion = (uv --version 2>&1)
        Write-Success "UV installed: $uvVersion"
    } else {
        Write-Err "UV installation failed. Please install manually: winget install astral-sh.uv"
        exit 1
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# PROVIDER SELECTION
# ═══════════════════════════════════════════════════════════════════════════

function Select-Provider {
    Write-Host ""
    Write-Host "  How would you like to power Claude OS?" -ForegroundColor White
    Write-Host ""
    Write-Host "  [1]" -ForegroundColor Cyan -NoNewline
    Write-Host " Local (Ollama)" -ForegroundColor Green -NoNewline
    Write-Host " - Free, private, runs on your machine"
    Write-Host "      Best for: Privacy-focused users, offline use" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  [2]" -ForegroundColor Cyan -NoNewline
    Write-Host " Cloud (OpenAI)" -ForegroundColor Blue -NoNewline
    Write-Host " - Fast, no local resources needed"
    Write-Host "      Best for: Quick setup, cloud deployments" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  [3]" -ForegroundColor Cyan -NoNewline
    Write-Host " Custom" -ForegroundColor Magenta -NoNewline
    Write-Host " - I'll configure it myself"
    Write-Host ""

    while ($true) {
        $choice = Read-Host "  Enter choice [1-3]"
        switch ($choice) {
            "1" { return "local" }
            "2" { return "openai" }
            "3" { return "custom" }
            default { Write-Host "  Please enter 1, 2, or 3" -ForegroundColor Red }
        }
    }
}

function Select-ModelSize {
    Write-Host ""
    Write-Host "  Select your local model:" -ForegroundColor White
    Write-Host ""
    Write-Host "  [1]" -ForegroundColor Cyan -NoNewline
    Write-Host " Lite (Recommended)" -ForegroundColor Green -NoNewline
    Write-Host " - llama3.2:3b - 2GB download, ~4GB RAM"
    Write-Host "      Fast download, works on most machines" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  [2]" -ForegroundColor Cyan -NoNewline
    Write-Host " Full" -ForegroundColor Blue -NoNewline
    Write-Host " - llama3.1:8b - 4.7GB download, ~8GB RAM"
    Write-Host "      Better quality, needs more resources" -ForegroundColor DarkGray
    Write-Host ""

    while ($true) {
        $choice = Read-Host "  Enter choice [1-2]"
        switch ($choice) {
            "1" { return $DEFAULT_LLM_MODEL }
            "2" { return $FULL_LLM_MODEL }
            default { Write-Host "  Please enter 1 or 2" -ForegroundColor Red }
        }
    }
}

function Get-OpenAIKey {
    Write-Host ""
    Write-Host "  Enter your OpenAI API key:" -ForegroundColor White
    Write-Host "  (Get one at https://platform.openai.com/api-keys)" -ForegroundColor DarkGray
    Write-Host ""
    $key = Read-Host "  API Key" -AsSecureString
    $plain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($key))
    if (-not $plain) {
        Write-Err "API key cannot be empty"
        exit 1
    }
    if (-not $plain.StartsWith("sk-")) {
        Write-Warn "API key doesn't start with 'sk-' - are you sure it's correct?"
    }
    Write-Success "API key saved"
    return $plain
}

# ═══════════════════════════════════════════════════════════════════════════
# PYTHON SETUP WITH UV
# ═══════════════════════════════════════════════════════════════════════════

function Setup-Python {
    Write-Section "Setting Up Python Environment with UV"

    $venvPath = Join-Path $CLAUDE_OS_DIR "venv"

    if ($DryRun) {
        Write-DryRun "Would create virtual environment at $venvPath using UV"
        Write-DryRun "Would install dependencies from requirements.txt using UV"
        return
    }

    # Use UV to create the virtual environment (UV auto-manages Python version)
    if (-not (Test-Path $venvPath)) {
        Write-Info "Creating virtual environment with UV (Python 3.12)..."
        Push-Location $CLAUDE_OS_DIR
        try {
            & uv venv venv --python 3.12 2>&1 | ForEach-Object { Write-Verbose $_ }
            if ($LASTEXITCODE -ne 0) {
                # Try without specifying version if 3.12 not available
                Write-Warn "Python 3.12 not found, trying latest compatible version..."
                & uv venv venv --python ">=3.11,<3.13" 2>&1 | ForEach-Object { Write-Verbose $_ }
            }
        } finally {
            Pop-Location
        }
        if (-not (Test-Path "$venvPath\Scripts\python.exe")) {
            Write-Err "Virtual environment was created but python.exe not found at $venvPath\Scripts\python.exe"
            exit 1
        }
        Write-Success "Virtual environment created at $venvPath"
    } else {
        Write-Success "Virtual environment already exists"
    }

    # Install dependencies with UV (much faster than pip)
    Write-Info "Installing dependencies with UV (this is fast!)..."
    Push-Location $CLAUDE_OS_DIR
    try {
        & uv pip install -r requirements.txt --python "$venvPath\Scripts\python.exe" 2>&1 |
            ForEach-Object {
                if ($_ -match "Installed|Resolved|Built") { Write-Verbose $_ }
            }
        if ($LASTEXITCODE -ne 0) {
            Write-Err "Failed to install dependencies"
            Write-Host "  Try running manually: uv pip install -r requirements.txt" -ForegroundColor Yellow
            exit 1
        }
    } finally {
        Pop-Location
    }
    Write-Success "Dependencies installed"

    # Show Python version being used
    $pyExe = Join-Path $venvPath "Scripts\python.exe"
    if (Test-Path $pyExe) {
        $pyVersion = & $pyExe --version 2>&1
        Write-Success "Using $pyVersion"
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# OLLAMA SETUP
# ═══════════════════════════════════════════════════════════════════════════

function Setup-Ollama {
    param([string]$LlmModel, [string]$EmbedModel)
    Write-Section "Setting Up Ollama"

    if ($DryRun) {
        Write-DryRun "Would install Ollama if not present"
        Write-DryRun "Would download model: $LlmModel"
        Write-DryRun "Would download model: $EmbedModel"
        return
    }

    if (Get-Command ollama -ErrorAction SilentlyContinue) {
        Write-Success "Ollama already installed"
    } else {
        Write-Info "Installing Ollama..."

        if (Get-Command winget -ErrorAction SilentlyContinue) {
            winget install --id=Ollama.Ollama -e --silent 2>&1 | Out-Null
            $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
                        [System.Environment]::GetEnvironmentVariable("PATH", "User") + ";" +
                        "$env:LOCALAPPDATA\Programs\Ollama"
        }

        if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
            Write-Warn "Could not auto-install Ollama."
            Write-Host ""
            Write-Host "  Please install Ollama manually:" -ForegroundColor White
            Write-Host "    https://ollama.ai/download/windows" -ForegroundColor Cyan
            Write-Host "    - or -" -ForegroundColor DarkGray
            Write-Host "    winget install Ollama.Ollama" -ForegroundColor Cyan
            Write-Host ""
            $cont = Read-Host "  Press Enter to continue after installing Ollama, or Ctrl+C to exit"
        }
    }

    # Start Ollama if not running
    if (-not (Test-Port 11434)) {
        Write-Info "Starting Ollama..."
        Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 3

        if (Test-Port 11434) {
            Write-Success "Ollama started"
        } else {
            Write-Warn "Could not verify Ollama is running. Start it manually: ollama serve"
        }
    } else {
        Write-Success "Ollama is running"
    }

    # Download models
    Write-Host ""
    Write-Info "Downloading AI models..."
    Write-Host ""

    $ollamaTags = try { (Invoke-WebRequest "http://localhost:11434/api/tags" -UseBasicParsing).Content } catch { "" }

    if ($ollamaTags -match [regex]::Escape("`"name`":`"$LlmModel`"")) {
        Write-Success "Model $LlmModel ready"
    } else {
        Write-Info "Downloading $LlmModel (this may take several minutes)..."
        & ollama pull $LlmModel
        Write-Success "Model $LlmModel downloaded"
    }

    if ($ollamaTags -match [regex]::Escape("`"name`":`"$EmbedModel`"")) {
        Write-Success "Model $EmbedModel ready"
    } else {
        Write-Info "Downloading $EmbedModel..."
        & ollama pull $EmbedModel
        Write-Success "Model $EmbedModel downloaded"
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# REDIS SETUP (Windows)
# ═══════════════════════════════════════════════════════════════════════════

function Setup-Redis {
    Write-Section "Setting Up Redis"

    if ($DryRun) {
        Write-DryRun "Would check for Redis / Memurai"
        Write-DryRun "Would start Redis service"
        return
    }

    # Check if Redis is already running
    if (Test-Port 6379) {
        Write-Success "Redis is running on port 6379"
        return
    }

    # Check for redis-server (native Windows Redis or Memurai)
    $hasRedis = Get-Command redis-server -ErrorAction SilentlyContinue
    $hasMemurai = Get-Command memurai-cli -ErrorAction SilentlyContinue

    if ($hasRedis) {
        Write-Info "Starting Redis..."
        Start-Process redis-server -WindowStyle Hidden
        Start-Sleep -Seconds 2
        if (Test-Port 6379) {
            Write-Success "Redis started"
        } else {
            Write-Warn "Redis may not be running. Start manually: redis-server"
        }
        return
    }

    if ($hasMemurai) {
        Write-Info "Starting Memurai (Redis-compatible)..."
        Start-Process memurai -WindowStyle Hidden
        Start-Sleep -Seconds 2
        if (Test-Port 6379) {
            Write-Success "Memurai started"
        }
        return
    }

    # Redis not installed - offer options
    Write-Warn "Redis is not installed."
    Write-Host ""
    Write-Host "  Redis is used for the real-time learning system." -ForegroundColor White
    Write-Host "  The MCP server works without Redis (learning features disabled)." -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  Options to install Redis on Windows:" -ForegroundColor White
    Write-Host "  [1] Install Memurai (Redis-compatible, recommended for Windows)" -ForegroundColor Cyan
    Write-Host "      https://www.memurai.com/get-memurai"
    Write-Host "  [2] Install via WSL2 (if you have WSL installed)" -ForegroundColor Cyan
    Write-Host "      wsl --install  then: sudo apt install redis-server"
    Write-Host "  [3] Skip Redis (MCP server still works, no real-time learning)" -ForegroundColor Cyan
    Write-Host ""

    if (-not $Force) {
        $choice = Read-Host "  Enter choice [1-3]"
        switch ($choice) {
            "1" {
                Write-Info "Opening Memurai download page..."
                Start-Process "https://www.memurai.com/get-memurai"
                Write-Host ""
                Write-Warn "After installing Memurai, re-run this script or start services manually."
            }
            "2" {
                Write-Info "To set up Redis with WSL2:"
                Write-Host "    wsl sudo apt update && sudo apt install -y redis-server" -ForegroundColor Cyan
                Write-Host "    wsl sudo service redis-server start" -ForegroundColor Cyan
            }
            "3" {
                Write-Warn "Skipping Redis. Real-time learning will be disabled."
                Write-Warn "Set REDIS_DISABLED=1 in your .env file."
            }
        }
    } else {
        Write-Warn "Skipping Redis (--force mode). Real-time learning will be disabled."
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# CLAUDE CODE INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════

function Setup-ClaudeIntegration {
    Write-Section "Integrating with Claude Code"

    $commandsDir = Join-Path $USER_CLAUDE_DIR "commands"
    $skillsDir = Join-Path $USER_CLAUDE_DIR "skills"
    $mcpDir = Join-Path $USER_CLAUDE_DIR "mcp-servers"
    $dataDir = Join-Path $CLAUDE_OS_DIR "data"
    $logsDir = Join-Path $CLAUDE_OS_DIR "logs"

    if ($DryRun) {
        Write-DryRun "Would create: $commandsDir"
        Write-DryRun "Would create: $skillsDir"
        Write-DryRun "Would create: $dataDir"
        Write-DryRun "Would create: $logsDir"
        Write-DryRun "Would link/copy commands from $TEMPLATES_DIR\commands\"
        Write-DryRun "Would link/copy skills from $TEMPLATES_DIR\skills\"
        return
    }

    # Create directories
    @($commandsDir, $skillsDir, $mcpDir, $dataDir, $logsDir) | ForEach-Object {
        if (-not (Test-Path $_)) {
            New-Item -ItemType Directory -Path $_ -Force | Out-Null
        }
    }
    Write-Success "Created directories"

    # Determine if we can create symlinks (requires Admin or Developer Mode)
    $canSymlink = $false
    try {
        $testLink = Join-Path $env:TEMP "claude-os-symlink-test"
        $testTarget = Join-Path $env:TEMP "claude-os-symlink-target"
        if (-not (Test-Path $testTarget)) { New-Item -ItemType Directory -Path $testTarget | Out-Null }
        New-Item -ItemType SymbolicLink -Path $testLink -Target $testTarget -ErrorAction Stop | Out-Null
        Remove-Item $testLink -Force -ErrorAction SilentlyContinue
        Remove-Item $testTarget -Force -ErrorAction SilentlyContinue
        $canSymlink = $true
    } catch {
        $canSymlink = $false
    }

    # Link or copy commands
    $cmdCount = 0
    $cmdDir = Join-Path $TEMPLATES_DIR "commands"
    if (Test-Path $cmdDir) {
        Get-ChildItem "$cmdDir\*.md" | ForEach-Object {
            $dest = Join-Path $commandsDir $_.Name
            if (Test-Path $dest) { Remove-Item $dest -Force }
            if ($canSymlink) {
                New-Item -ItemType SymbolicLink -Path $dest -Target $_.FullName | Out-Null
            } else {
                Copy-Item $_.FullName -Destination $dest -Force
            }
            $cmdCount++
        }
    }
    $linkType = if ($canSymlink) { "symlinked" } else { "copied" }
    Write-Success "$linkType $cmdCount commands"

    # Link or copy skills (directories)
    $skillCount = 0
    $skillSrcDir = Join-Path $TEMPLATES_DIR "skills"
    if (Test-Path $skillSrcDir) {
        Get-ChildItem $skillSrcDir -Directory | ForEach-Object {
            $dest = Join-Path $skillsDir $_.Name
            if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
            if ($canSymlink) {
                New-Item -ItemType SymbolicLink -Path $dest -Target $_.FullName | Out-Null
            } else {
                Copy-Item $_.FullName -Destination $dest -Recurse -Force
            }
            $skillCount++
        }
    }
    Write-Success "$linkType $skillCount skills"

    Write-Info "MCP server will be configured per-project via /claude-os-init"

    # Show symlink note if we couldn't create them
    if (-not $canSymlink) {
        Write-Host ""
        Write-Warn "Commands/skills were copied (not symlinked) - no Developer Mode or Admin rights detected."
        Write-Warn "Re-run as Administrator or enable Developer Mode for live-symlink updates."
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# CREATE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

function New-Config {
    param([string]$Provider, [string]$LlmModel, [string]$EmbedModel, [string]$OpenAiKey = "")

    Write-Section "Creating Configuration"

    $configFile = Join-Path $CLAUDE_OS_DIR ".env"
    $jsonConfig = Join-Path $CLAUDE_OS_DIR "claude-os-config.json"

    if ($DryRun) {
        Write-DryRun "Would create $configFile"
        Write-DryRun "  CLAUDE_OS_PROVIDER=$Provider"
        Write-DryRun "  LLM_MODEL=$LlmModel"
        Write-DryRun "  EMBEDDING_MODEL=$EmbedModel"
        return
    }

    # Backup existing
    if (Test-Path $configFile) {
        $backup = "$configFile.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Copy-Item $configFile $backup
        Write-Info "Backed up $configFile"
    }

    $timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

    @"
# Claude OS Configuration
# Generated by setup-claude-os.ps1 on $timestamp

# Provider: local, openai, or custom
CLAUDE_OS_PROVIDER=$Provider

# LLM Settings
LLM_MODEL=$LlmModel
EMBEDDING_MODEL=$EmbedModel

# Ollama Settings (for local provider)
OLLAMA_HOST=http://localhost:11434

# OpenAI Settings (for cloud provider)
OPENAI_API_KEY=$OpenAiKey

# Server Settings
CLAUDE_OS_HOST=0.0.0.0
CLAUDE_OS_PORT=8051

# Database
CLAUDE_OS_DB_PATH=./data/claude-os.db
"@ | Set-Content $configFile -Encoding UTF8

    Write-Success "Created $configFile"

    @"
{
  "provider": "$Provider",
  "llm_model": "$LlmModel",
  "embed_model": "$EmbedModel",
  "version": "$CLAUDE_OS_VERSION",
  "platform": "windows",
  "installed_at": "$timestamp"
}
"@ | Set-Content $jsonConfig -Encoding UTF8

    Write-Success "Created $jsonConfig"
}

# ═══════════════════════════════════════════════════════════════════════════
# COMPLETION
# ═══════════════════════════════════════════════════════════════════════════

function Show-Completion {
    param([string]$Provider, [string]$LlmModel, [string]$EmbedModel)

    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║                                                                   ║" -ForegroundColor Green
    Write-Host "║   ✨  Claude OS is ready!  ✨                                     ║" -ForegroundColor Green
    Write-Host "║                                                                   ║" -ForegroundColor Green
    Write-Host "╚═══════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "  What was set up:" -ForegroundColor White
    Write-Host ""

    $venvPath = Join-Path $CLAUDE_OS_DIR "venv"
    if (Test-Path $venvPath) { Write-Host "    [OK] Python environment (UV-managed)" -ForegroundColor Green }
    if ($Provider -eq "local") {
        Write-Host "    [OK] Ollama with $LlmModel" -ForegroundColor Green
        Write-Host "    [OK] Embedding model ($EmbedModel)" -ForegroundColor Green
    }
    if ($Provider -eq "openai") { Write-Host "    [OK] OpenAI API configured" -ForegroundColor Green }
    if (Test-Port 6379) { Write-Host "    [OK] Redis cache" -ForegroundColor Green }
    $cmdDir = Join-Path $USER_CLAUDE_DIR "commands"
    if (Test-Path $cmdDir) { Write-Host "    [OK] Claude Code commands" -ForegroundColor Green }

    Write-Host ""
    Write-Host ("  " + "=" * 58) -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Next Steps:" -ForegroundColor White
    Write-Host ""
    Write-Host "  1. Start Claude OS (MCP server only):" -ForegroundColor Cyan
    Write-Host "     .\start.ps1"
    Write-Host ""
    Write-Host "  2. Start all services (MCP + Frontend + Workers):" -ForegroundColor Cyan
    Write-Host "     .\start_all_services.ps1"
    Write-Host ""
    Write-Host "  3. In your project, initialize Claude OS:" -ForegroundColor Cyan
    Write-Host "     /claude-os-init"
    Write-Host ""
    Write-Host "  4. Start a session:" -ForegroundColor Cyan
    Write-Host "     /claude-os-session start `"working on feature X`""
    Write-Host ""
    Write-Host ("  " + "=" * 58) -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Documentation: README.md" -ForegroundColor DarkGray
    Write-Host "  Issues: https://github.com/brobertsaz/claude-os/issues" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  Happy coding! " -ForegroundColor White
    Write-Host ""
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if ($Help) { Show-Help; exit 0 }
if ($Version) { Write-Host "Claude OS Installer v$CLAUDE_OS_VERSION"; exit 0 }

Show-Banner

if ($DryRun) {
    Write-Host ""
    Write-Host "+------------------------------------------------------------------+" -ForegroundColor Yellow
    Write-Host "|  DRY-RUN MODE - No changes will be made                          |" -ForegroundColor Yellow
    Write-Host "+------------------------------------------------------------------+" -ForegroundColor Yellow
    Write-Host ""
}

# 1. Ensure UV is installed
Install-UV

# 2. Select provider
$provider = Select-Provider
$llmModel = ""
$embedModel = $DEFAULT_EMBED_MODEL
$openAiKey = ""

switch ($provider) {
    "local" {
        Write-Success "Selected: Local (Ollama)"
        $llmModel = Select-ModelSize
        Write-Success "Selected model: $llmModel"
    }
    "openai" {
        Write-Success "Selected: Cloud (OpenAI)"
        $openAiKey = Get-OpenAIKey
        $llmModel = "gpt-4o-mini"
        $embedModel = "text-embedding-3-small"
    }
    "custom" {
        Write-Success "Selected: Custom"
        Write-Info "Custom setup - configure .env manually after installation"
        $llmModel = "llama3.1:latest"
        $embedModel = $DEFAULT_EMBED_MODEL
    }
}

# 3. Python environment with UV
Setup-Python

# 4. Provider-specific setup
if ($provider -eq "local") {
    Setup-Ollama -LlmModel $llmModel -EmbedModel $embedModel
}

# 5. Redis
Setup-Redis

# 6. Claude Code integration
Setup-ClaudeIntegration

# 7. Config
New-Config -Provider $provider -LlmModel $llmModel -EmbedModel $embedModel -OpenAiKey $openAiKey

# 8. Done
Show-Completion -Provider $provider -LlmModel $llmModel -EmbedModel $embedModel
