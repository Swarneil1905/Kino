# Diagnose Docker on Windows for Kino
Write-Host "=== Docker diagnostic ===" -ForegroundColor Cyan

$dockerPaths = @(
    "$env:ProgramFiles\Docker\Docker\resources\bin\docker.exe",
    "$env:LocalAppData\Docker\cli-plugins\docker-compose.exe"
)

$found = $false
foreach ($p in $dockerPaths) {
    if (Test-Path $p) {
        Write-Host "Found: $p" -ForegroundColor Green
        $found = $true
    }
}

$cmd = Get-Command docker -ErrorAction SilentlyContinue
if ($cmd) {
    Write-Host "docker on PATH: $($cmd.Source)" -ForegroundColor Green
    docker --version
    docker compose version
    exit 0
}

if (-not $found) {
    Write-Host ""
    Write-Host "Docker is NOT installed (or not finished installing)." -ForegroundColor Yellow
    Write-Host "PowerShell cannot find 'docker' and there is no Docker Desktop folder."
    Write-Host ""
    Write-Host "Install Docker Desktop:" -ForegroundColor Cyan
    Write-Host "  1. Download: https://docs.docker.com/desktop/setup/install/windows-install/"
    Write-Host "  2. Or run (Admin PowerShell):"
    Write-Host '     winget install Docker.DockerDesktop --accept-package-agreements --accept-source-agreements'
    Write-Host "  3. Reboot, open Docker Desktop, wait until it says 'Engine running'"
    Write-Host "  4. Close ALL terminals, open a NEW PowerShell, then:"
    Write-Host "     cd $PSScriptRoot\.."
    Write-Host "     docker compose up --build"
    Write-Host ""
    Write-Host "Without Docker, use local dev instead:" -ForegroundColor Cyan
    Write-Host "     .\scripts\start-local.ps1"
    exit 1
}

Write-Host "Docker is installed but this terminal has a stale PATH." -ForegroundColor Yellow
Write-Host "Fix (pick one):" -ForegroundColor Cyan
Write-Host "  A) Close ALL terminals, fully quit Cursor, reopen, then: docker --version"
Write-Host "  B) Refresh PATH in this terminal:"
Write-Host '     $env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")'
Write-Host '     docker --version'
Write-Host ""
Write-Host "Or use full path for now:"
Write-Host '  & "C:\Program Files\Docker\Docker\resources\bin\docker.exe" compose up --build'
exit 1
