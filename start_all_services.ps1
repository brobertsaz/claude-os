#Requires -Version 5.1
# Claude OS - Start All Services (Windows)
# Starts: Ollama, Redis check, RQ workers, MCP server, React frontend
# Usage: .\start_all_services.ps1
#
# Logs written to .\logs\

Set-StrictMode -Version Latest
$ErrorActionPreference = "SilentlyContinue"

$ProjectDir = $PSScriptRoot
$VenvDir = Join-Path $ProjectDir "venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip = Join-Path $VenvDir "Scripts\pip.exe"
$DataDir = Join-Path $ProjectDir "data"
$LogsDir = Join-Path $ProjectDir "logs"
$McpServer = Join-Path $ProjectDir "mcp_server\server.py"
$McpServerDir = Join-Path $ProjectDir "mcp_server"
$FrontendDir = Join-Path $ProjectDir "frontend"
$EnvFile = Join-Path $ProjectDir ".env"

# Redis host — updated to WSL2 IP if Redis runs inside WSL
$script:RedisHost = "localhost"
$redisOk = $false

# ─── Helpers ─────────────────────────────────────────────────────────────────

function Write-OK    { param($msg) Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn  { param($msg) Write-Host "  [!!] $msg" -ForegroundColor Yellow }
function Write-Err   { param($msg) Write-Host "  [XX] $msg" -ForegroundColor Red }
function Write-Info  { param($msg) Write-Host "  [..] $msg" -ForegroundColor Cyan }

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

function Stop-ServiceOnPort {
    param([int]$Port)
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
        $proc = $conn | Select-Object -First 1 -ExpandProperty OwningProcess
        if ($proc -and $proc -ne 0) {
            Stop-Process -Id $proc -Force -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 500
        }
    }
}

function Wait-ForPort {
    param([int]$Port, [int]$Seconds = 10, [string]$Label = "service")
    for ($i = 0; $i -lt $Seconds; $i++) {
        if (Test-Port $Port) { return $true }
        Write-Host "." -NoNewline -ForegroundColor DarkGray
        Start-Sleep -Seconds 1
    }
    Write-Host "" # newline
    return $false
}

# ─── Banner ──────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "  ╔═════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║         Claude OS - Starting Services        ║" -ForegroundColor Cyan
Write-Host "  ╚═════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ─── Pre-flight checks ───────────────────────────────────────────────────────

if (-not (Test-Path $VenvPython)) {
    Write-Err "Virtual environment not found."
    Write-Host "  Run .\setup-claude-os.ps1 first." -ForegroundColor Yellow
    exit 1
}

# Ensure data/logs dirs
@($DataDir, $LogsDir) | ForEach-Object {
    if (-not (Test-Path $_)) { New-Item -ItemType Directory -Path $_ -Force | Out-Null }
}

# Load .env if it exists
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | Where-Object { $_ -match "^[A-Z_]+=.+" } | ForEach-Object {
        $parts = $_ -split "=", 2
        [System.Environment]::SetEnvironmentVariable($parts[0], $parts[1], "Process")
    }
}

$DbPath = if ($env:CLAUDE_OS_DB_PATH) { $env:CLAUDE_OS_DB_PATH } else { Join-Path $DataDir "claude-os.db" }

# ─── 1. Ollama ───────────────────────────────────────────────────────────────

Write-Host "  [1/5] Checking Ollama..." -ForegroundColor White

if (Test-Port 11434) {
    Write-OK "Ollama is running (port 11434)"
} else {
    if (Get-Command ollama -ErrorAction SilentlyContinue) {
        Write-Info "Starting Ollama..."
        Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden
        if (Wait-ForPort 11434 12 "Ollama") {
            Write-OK "Ollama started"
        } else {
            Write-Warn "Ollama didn't start in time. Continuing anyway."
        }
    } else {
        Write-Warn "Ollama not found. Install from https://ollama.ai/download/windows"
        Write-Warn "Continuing - Ollama-dependent features will be unavailable."
    }
}

# ─── 2. Python environment ───────────────────────────────────────────────────

Write-Host "  [2/5] Checking Python environment..." -ForegroundColor White

if (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Info "Updating dependencies with UV..."
    & uv pip install -r "$ProjectDir\requirements.txt" --python $VenvPython --quiet 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-OK "Dependencies up to date (UV)"
    } else {
        Write-Warn "UV install had issues. Trying pip..."
        & $VenvPip install -r "$ProjectDir\requirements.txt" --quiet 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-OK "Dependencies up to date (pip fallback)"
        } else {
            Write-Err "pip install also failed. Check your Python environment."
            exit 1
        }
    }
} else {
    & $VenvPip install -r "$ProjectDir\requirements.txt" --quiet 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-OK "Dependencies verified (pip)"
    } else {
        Write-Err "pip install failed. Check your Python environment and try running setup-claude-os.ps1 again."
        exit 1
    }
}

# ─── 3. Redis ────────────────────────────────────────────────────────────────

Write-Host "  [3/5] Checking Redis..." -ForegroundColor White

if (Test-Port 6379) {
    Write-OK "Redis is running (port 6379)"
    $redisOk = $true
} else {
    # Try WSL Redis
    if (Get-Command wsl -ErrorAction SilentlyContinue) {
        $wslRedis = wsl which redis-server 2>$null
        if ($wslRedis) {
            Write-Info "Starting Redis via WSL..."

            # Get WSL2 IP first so we can bind Redis to it specifically
            $wslIp = (wsl hostname -I 2>$null).Trim().Split()[0]
            if ($wslIp) {
                $script:RedisHost = $wslIp
                Write-Info "WSL2 IP: $wslIp — Redis will bind to 127.0.0.1 and $wslIp"
            }

            # Bind Redis to loopback (WSL-internal) + WSL2 adapter IP only.
            # Do NOT use --bind 0.0.0.0 or --protected-mode no as that exposes
            # an unauthenticated Redis instance to the host network.
            $bindArgs = if ($wslIp) { "127.0.0.1 $wslIp" } else { "127.0.0.1" }
            wsl -e sh -c "pkill redis-server 2>/dev/null; sleep 1; redis-server --daemonize yes --bind $bindArgs --loglevel warning" | Out-Null
            Start-Sleep -Seconds 2

            # Disable protected mode so Windows-side clients (RQ workers, MCP server) can connect
            wsl -e sh -c "redis-cli -h 127.0.0.1 CONFIG SET protected-mode no" | Out-Null

            # Verify connectivity via WSL IP
            $socket = New-Object System.Net.Sockets.TcpClient
            try {
                $socket.Connect($script:RedisHost, 6379)
                if ($socket.Connected) {
                    Write-OK "Redis started via WSL ($($script:RedisHost):6379)"
                    $redisOk = $true
                }
            } catch { } finally { $socket.Close() }
        }
    }

    if (-not $redisOk) {
        if (Get-Command redis-server -ErrorAction SilentlyContinue) {
            Write-Info "Starting Redis..."
            Start-Process redis-server -WindowStyle Hidden
            Start-Sleep -Seconds 2
            if (Test-Port 6379) {
                Write-OK "Redis started"
                $redisOk = $true
            }
        }
    }

    if (-not $redisOk) {
        Write-Warn "Redis not running. RQ workers will be skipped."
        Write-Warn "Install Memurai (https://www.memurai.com) or enable WSL2 + Redis."
        $redisOk = $false
    }
}

# ─── 4. RQ Workers ───────────────────────────────────────────────────────────

Write-Host "  [4/5] Starting RQ workers..." -ForegroundColor White

if ($redisOk) {
    # Stop existing RQ worker processes (Get-CimInstance exposes CommandLine; Get-Process does not)
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like "*rq*worker*" } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

    $workersLog = Join-Path $LogsDir "rq_workers.log"

    # Set env for workers (REDIS_HOST points to WSL2 IP if Redis runs in WSL)
    $env:SQLITE_DB_PATH = $DbPath
    $env:REDIS_HOST = $script:RedisHost
    if ($env:CLAUDE_OS_PROVIDER) { } # already set from .env

    # Use the rq console script (python -m rq is not supported)
    $rqExe = Join-Path (Split-Path $VenvPython) "rq.exe"
    if (-not (Test-Path $rqExe)) { $rqExe = Join-Path (Split-Path $VenvPython) "rq" }

    # Build Redis URL — use WSL IP if Redis is running in WSL
    $redisUrl = "redis://$($script:RedisHost):6379"

    $workerProcess = Start-Process $rqExe `
        -ArgumentList "worker", "--url", $redisUrl, "claude-os:learning", "claude-os:prompts", "claude-os:ingest" `
        -RedirectStandardOutput $workersLog `
        -RedirectStandardError "$workersLog.err" `
        -WorkingDirectory $McpServerDir `
        -WindowStyle Hidden `
        -PassThru

    Start-Sleep -Seconds 2

    if (-not $workerProcess.HasExited) {
        Write-OK "RQ workers started (PID $($workerProcess.Id))"
        Write-Host "      Log: $workersLog" -ForegroundColor DarkGray
    } else {
        Write-Warn "RQ workers exited early. Check: $workersLog"
    }
} else {
    Write-Warn "Skipping RQ workers (Redis unavailable)"
}

# ─── 5. MCP Server ───────────────────────────────────────────────────────────

Write-Host "  [5/5] Starting MCP server..." -ForegroundColor White

Stop-ServiceOnPort 8051

$mcpLog = Join-Path $LogsDir "mcp_server.log"
$env:SQLITE_DB_PATH = $DbPath
$env:REDIS_HOST = $script:RedisHost

$mcpProcess = Start-Process $VenvPython `
    -ArgumentList "server.py" `
    -WorkingDirectory $McpServerDir `
    -RedirectStandardOutput $mcpLog `
    -RedirectStandardError "$mcpLog.err" `
    -WindowStyle Hidden `
    -PassThru

if (Wait-ForPort 8051 15 "MCP server") {
    Write-OK "MCP server running on port 8051 (PID $($mcpProcess.Id))"
    Write-Host "      Log: $mcpLog" -ForegroundColor DarkGray
} else {
    Write-Warn "MCP server may not have started. Check: $mcpLog"
}

# ─── Optional: Frontend ──────────────────────────────────────────────────────

if (Test-Path $FrontendDir) {
    Write-Host ""
    Write-Host "  [+] Starting React frontend..." -ForegroundColor White

    Stop-ServiceOnPort 5173

    $nodeModules = Join-Path $FrontendDir "node_modules"
    if (-not (Test-Path $nodeModules)) {
        if (Get-Command npm -ErrorAction SilentlyContinue) {
            Write-Info "Installing npm dependencies..."
            Push-Location $FrontendDir
            npm install --silent 2>&1 | Out-Null
            Pop-Location
        } else {
            Write-Warn "npm not found. Skipping frontend. Install Node.js from https://nodejs.org"
        }
    }

    if (Test-Path $nodeModules) {
        $frontendLog = Join-Path $LogsDir "frontend.log"
        $feProcess = Start-Process cmd `
            -ArgumentList "/c npm run dev" `
            -WorkingDirectory $FrontendDir `
            -RedirectStandardOutput $frontendLog `
            -RedirectStandardError "$frontendLog.err" `
            -WindowStyle Hidden `
            -PassThru

        if (Wait-ForPort 5173 15 "frontend") {
            Write-OK "Frontend running on http://localhost:5173 (PID $($feProcess.Id))"
        } else {
            Write-Warn "Frontend may not have started. Check: $frontendLog"
        }
    }
}

# ─── Summary ─────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "  ─────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host "  Services status:" -ForegroundColor White
Write-Host ""

if (Test-Port 11434) { Write-OK "Ollama           http://localhost:11434" } else { Write-Warn "Ollama           not running" }
if ($redisOk)        { Write-OK "Redis            port 6379"               } else { Write-Warn "Redis            not running" }
if (Test-Port 8051)  { Write-OK "MCP Server       http://localhost:8051"   } else { Write-Warn "MCP Server       not running" }
if (Test-Port 5173)  { Write-OK "Frontend         http://localhost:5173"   } else { Write-Host "  [--] Frontend        not started" -ForegroundColor DarkGray }
Write-Host ""
Write-Host "  Logs: $LogsDir" -ForegroundColor DarkGray
Write-Host "  Stop: .\stop_all_services.ps1" -ForegroundColor DarkGray
Write-Host ""
