# Run Kino without Docker (PostgreSQL must be running on localhost:5432)
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent

Write-Host "=== Kino local dev (no Docker) ===" -ForegroundColor Cyan
Write-Host "Requires PostgreSQL on localhost:5432 (database: kino, user/pass: postgres/postgres)"
Write-Host "Redis optional on localhost:6379 (API works without it, caching disabled)"
Write-Host ""

$env:DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/kino"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:SECRET_KEY = "dev-secret-replace-in-production"

# Terminal 1 hint
Write-Host "Terminal 1 - API:" -ForegroundColor Green
Write-Host "  cd `"$root\apps\api`""
Write-Host "  alembic upgrade head"
Write-Host "  uvicorn main:app --reload --port 8000"
Write-Host ""
Write-Host "Terminal 2 - Web:" -ForegroundColor Green
Write-Host "  cd `"$root\apps\web`""
Write-Host "  if (-not (Test-Path .env.local)) { Copy-Item .env.example .env.local }"
Write-Host '  $env:NEXT_PUBLIC_API_URL = "http://localhost:8000"'
Write-Host "  npm run dev"
Write-Host ""
Write-Host "Install PostgreSQL (if needed):" -ForegroundColor Yellow
Write-Host "  winget install PostgreSQL.PostgreSQL.16 --accept-package-agreements"
Write-Host "  Then create database 'kino' in pgAdmin or: createdb -U postgres kino"
