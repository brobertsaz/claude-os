# ============================================================================
# Claude OS - Démarrage des services (équivalent Windows de start_all_services.sh)
# Usage :  .\start-claude-os.ps1
# ============================================================================

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "=== Claude OS - Demarrage ===" -ForegroundColor Cyan
Write-Host ""

# --- Dossiers requis ---
foreach ($d in @("data", "logs")) {
    if (-not (Test-Path "$ProjectDir\$d")) {
        New-Item -ItemType Directory "$ProjectDir\$d" -Force | Out-Null
    }
}

# --- 1. Ollama ---
Write-Host "[1/3] Ollama..." -NoNewline
try {
    Invoke-WebRequest -Uri "http://localhost:11434" -UseBasicParsing -TimeoutSec 5 | Out-Null
    Write-Host " deja en cours" -ForegroundColor Green
} catch {
    Write-Host " demarrage..." -NoNewline
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 5
    Write-Host " ok" -ForegroundColor Green
}

# --- 2. API Server (port 8051) ---
Write-Host "[2/3] API Server..." -NoNewline
$apiUp = $false
try {
    Invoke-WebRequest -Uri "http://localhost:8051/docs" -UseBasicParsing -TimeoutSec 5 | Out-Null
    $apiUp = $true
} catch { }

if ($apiUp) {
    Write-Host " deja en cours" -ForegroundColor Green
} else {
    $env:SQLITE_DB_PATH = "$ProjectDir\data\claude-os.db"
    Start-Process -FilePath "$ProjectDir\venv\Scripts\python.exe" `
                  -ArgumentList "server.py" `
                  -WorkingDirectory "$ProjectDir\mcp_server" `
                  -RedirectStandardOutput "$ProjectDir\logs\mcp_server.log" `
                  -RedirectStandardError "$ProjectDir\logs\mcp_server.err.log" `
                  -WindowStyle Hidden
    # Attente jusqu'a 30s
    $ok = $false
    for ($i = 0; $i -lt 15; $i++) {
        Start-Sleep -Seconds 2
        try {
            Invoke-WebRequest -Uri "http://localhost:8051/docs" -UseBasicParsing -TimeoutSec 3 | Out-Null
            $ok = $true; break
        } catch { }
    }
    if ($ok) { Write-Host " ok" -ForegroundColor Green }
    else { Write-Host " ECHEC - voir logs\mcp_server.err.log" -ForegroundColor Red }
}

# --- 3. Frontend (port 5173) ---
Write-Host "[3/3] Frontend..." -NoNewline
$feUp = $false
try {
    Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 5 | Out-Null
    $feUp = $true
} catch { }

if ($feUp) {
    Write-Host " deja en cours" -ForegroundColor Green
} else {
    if (-not (Test-Path "$ProjectDir\frontend\node_modules")) {
        Write-Host " installation npm..." -NoNewline
        Push-Location "$ProjectDir\frontend"; npm install | Out-Null; Pop-Location
    }
    Start-Process "npm" -ArgumentList "run", "dev" `
                  -WorkingDirectory "$ProjectDir\frontend" `
                  -WindowStyle Hidden
    Start-Sleep -Seconds 8
    Write-Host " ok" -ForegroundColor Green
}

Write-Host ""
Write-Host "Interface  : http://localhost:5173" -ForegroundColor Yellow
Write-Host "API / docs : http://localhost:8051/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "Pour arreter : .\stop-claude-os.ps1" -ForegroundColor DarkGray
Write-Host ""
