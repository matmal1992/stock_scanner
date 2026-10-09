# Build EXE — DEBUG

$ErrorActionPreference = "Stop"

$timer = [System.Diagnostics.Stopwatch]::StartNew()

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot
$browserPath = Join-Path $projectRoot "browsers"

Write-Host "=== DEBUG BUILD START ===" -ForegroundColor Green

# Czyszczenie builda
if (Test-Path build/debug) {
    Write-Host "Cleaning build directory..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force build/debug/* -ErrorAction SilentlyContinue
}

# Sprawdzenie czy browsers istnieją
if (-Not (Test-Path "browsers")) {
    Write-Host "ERROR: 'browsers' directory not found!" -ForegroundColor Red
    Write-Host "Run Setup Environment first." -ForegroundColor Red
    exit 1
}

Write-Host "Building Stock Scanner (DEBUG)..." -ForegroundColor Cyan

python -m uv run pyinstaller `
    --onedir `
    --console `
    --debug=all `
    --name stock_scanner_debug `
    --add-data "$browserPath;browsers" `
    --add-data "$projectRoot/assets;assets" `
    --distpath build/debug/dist `
    --workpath build/debug/work `
    --specpath build/debug/spec `
    src/main.py

if ($LASTEXITCODE -ne 0) {
    throw "Stock Scanner DEBUG build failed with exit code $LASTEXITCODE"
}

Write-Host "Building Watchdog (DEBUG)..." -ForegroundColor Cyan

python -m uv run pyinstaller `
    --onedir `
    --console `
    --debug=all `
    --name watchdog_debug `
    --paths "$projectRoot/src" `
    --distpath build/debug/dist `
    --workpath build/debug/work `
    --specpath build/debug/spec `
    src/stock_scanner/core/watchdog.py

if ($LASTEXITCODE -ne 0) {
    throw "Watchdog DEBUG build failed with exit code $LASTEXITCODE"
}

$timer.Stop()

Write-Host "=== DEBUG BUILD FINISHED ===" -ForegroundColor Green
Write-Host "Time: $($timer.Elapsed)" -ForegroundColor Green
