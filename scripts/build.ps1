# Build EXE

$ErrorActionPreference = "Stop"

$timer = [System.Diagnostics.Stopwatch]::StartNew()

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot
$browserPath = Join-Path $projectRoot "browsers"

Write-Host "=== BUILD START ===" -ForegroundColor Green

# Czyszczenie builda
if (Test-Path build) {
    Write-Host "Cleaning build directory..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force build/* -ErrorAction SilentlyContinue
}

# Sprawdzenie czy browsers istnieją
if (-Not (Test-Path "browsers")) {
    Write-Host "ERROR: 'browsers' directory not found!" -ForegroundColor Red
    Write-Host "Run Setup Environment first." -ForegroundColor Red
    exit 1
}

# Build PyInstaller
Write-Host "Running PyInstaller..." -ForegroundColor Cyan

python -m uv run pyinstaller `
    --clean `
    --onedir `
    --name stock_scanner `
    --add-data "$browserPath;browsers" `
    --add-data "$projectRoot/assets;assets" `
    --distpath build/dist `
    --workpath build/work `
    --specpath build/spec `
    src/main.py

# if (Test-Path "src/assets") {
#     Write-Host "Copying assets..." -ForegroundColor Yellow
#     Copy-Item -Recurse -Force src/assets build/dist/assets
# }

$timer.Stop()

Write-Host "=== BUILD FINISHED ===" -ForegroundColor Green
Write-Host "Time: $($timer.Elapsed)" -ForegroundColor Green