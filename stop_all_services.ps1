#Requires -Version 5.1
# Claude OS - Stop All Services (Windows)
# Stops: MCP server (8051), React frontend (5173), Redis, RQ workers
# Usage: .\stop_all_services.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "SilentlyContinue"

function Write-OK   { param($msg) Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "  [!!] $msg" -ForegroundColor Yellow }
function Write-Info { param($msg) Write-Host "  [..] $msg" -ForegroundColor Cyan }

function Stop-OnPort {
    param([int]$Port, [string]$Label)
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
        $procId = $conn | Select-Object -First 1 -ExpandProperty OwningProcess
        if ($procId -and $procId -ne 0) {
            $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
            $name = if ($proc) { $proc.Name } else { "PID $procId" }
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
            Write-OK "Stopped $Label ($name on port $Port)"
            return
        }
    }
    Write-Info "$Label not running (port $Port)"
}

Write-Host ""
Write-Host "  Stopping Claude OS services..." -ForegroundColor Cyan
Write-Host ""

# Stop MCP server (port 8051)
Stop-OnPort 8051 "MCP Server"

# Stop React frontend (port 5173)
Stop-OnPort 5173 "Frontend"

# Stop RQ workers (find python processes running rq worker with our queue names)
$rqWorkers = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*rq*" -and $_.CommandLine -like "*worker*" }

if ($rqWorkers) {
    $rqWorkers | ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Write-OK "Stopped $($rqWorkers.Count) RQ worker(s)"
} else {
    Write-Info "RQ workers not running"
}

# Stop Redis if we started it
Stop-OnPort 6379 "Redis"

# Stop WSL Redis if running
if (Get-Command wsl -ErrorAction SilentlyContinue) {
    $wslRedisRunning = wsl pgrep -x redis-server 2>$null
    if ($wslRedisRunning) {
        wsl -e sh -c "pkill redis-server 2>/dev/null" | Out-Null
        Write-OK "Stopped Redis (WSL)"
    }
}

Write-Host ""
Write-Host "  All services stopped." -ForegroundColor Green
Write-Host ""

