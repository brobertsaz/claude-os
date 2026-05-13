#Requires -Version 5.1
# Claude OS - Start MCP Server (Windows)
# Starts the FastAPI HTTP server (mcp_server/server.py) on port 8051.
# Usage: .\start.ps1
# For full services (Redis, workers, frontend), use start_all_services.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectDir = $PSScriptRoot
$VenvPython = Join-Path $ProjectDir "venv\Scripts\python.exe"
$McpServer = Join-Path $ProjectDir "mcp_server\server.py"
$McpServerDir = Join-Path $ProjectDir "mcp_server"
$DataDir = Join-Path $ProjectDir "data"
$LogsDir = Join-Path $ProjectDir "logs"

# Ensure data and logs directories exist
@($DataDir, $LogsDir) | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
    }
}

# Check venv exists
if (-not (Test-Path $VenvPython)) {
    Write-Host "  [XX] Virtual environment not found at $VenvPython" -ForegroundColor Red
    Write-Host "  Run .\setup-claude-os.ps1 first." -ForegroundColor Yellow
    exit 1
}

# Check MCP server file
if (-not (Test-Path $McpServer)) {
    Write-Host "  [XX] MCP server not found at $McpServer" -ForegroundColor Red
    exit 1
}

# Kill any existing MCP server on port 8051
$conn = Get-NetTCPConnection -LocalPort 8051 -State Listen -ErrorAction SilentlyContinue
if ($conn) {
    $pid = $conn | Select-Object -First 1 -ExpandProperty OwningProcess
    if ($pid -and $pid -ne 0) {
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 500
    }
}

# Start MCP server (stdin/stdout mode)
Write-Host ""
Write-Host "  Claude OS MCP Server" -ForegroundColor Cyan
Write-Host ("  " + "-" * 50) -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Server: $McpServer" -ForegroundColor DarkGray
Write-Host "  Python: $VenvPython" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Press Ctrl+C to stop." -ForegroundColor DarkGray
Write-Host ""

$env:SQLITE_DB_PATH = Join-Path $DataDir "claude-os.db"

# Load .env if present; respect CLAUDE_OS_DB_PATH if set there
$EnvFile = Join-Path $ProjectDir ".env"
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | Where-Object { $_ -match "^[A-Z_]+=.+" } | ForEach-Object {
        $parts = $_ -split "=", 2
        [System.Environment]::SetEnvironmentVariable($parts[0], $parts[1], "Process")
    }
}
if ($env:CLAUDE_OS_DB_PATH) { $env:SQLITE_DB_PATH = $env:CLAUDE_OS_DB_PATH }

Push-Location $McpServerDir
try {
    & $VenvPython server.py
} finally {
    Pop-Location
}
