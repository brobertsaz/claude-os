# ============================================================================
# Claude OS - Arrêt des services (équivalent Windows de stop_all_services.sh)
# Usage :  .\stop-claude-os.ps1
# ============================================================================

Write-Host ""
Write-Host "=== Claude OS - Arret ===" -ForegroundColor Cyan

# Arrete les processus ecoutant sur les ports 8051 (API) et 5173 (frontend)
foreach ($port in @(8051, 5173)) {
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($conns) {
        foreach ($pid_ in ($conns.OwningProcess | Select-Object -Unique)) {
            try {
                $name = (Get-Process -Id $pid_ -ErrorAction Stop).ProcessName
                Stop-Process -Id $pid_ -Force -ErrorAction Stop
                Write-Host "  Port ${port} : $name (PID $pid_) arrete" -ForegroundColor Green
            } catch {
                Write-Host "  Port ${port} : impossible d'arreter le PID $pid_" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "  Port ${port} : rien en ecoute" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "Note : Ollama reste actif (service Windows). Pour l'arreter :" -ForegroundColor DarkGray
Write-Host "  Get-Process ollama* | Stop-Process -Force" -ForegroundColor DarkGray
Write-Host ""
