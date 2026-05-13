#Requires -Version 5.1
# Claude OS - Restart All Services (Windows)
# Usage: .\restart_services.ps1

$ProjectDir = $PSScriptRoot

Write-Host ""
Write-Host "  Restarting Claude OS services..." -ForegroundColor Cyan
Write-Host ""

& "$ProjectDir\stop_all_services.ps1"
Start-Sleep -Seconds 2
& "$ProjectDir\start_all_services.ps1"
