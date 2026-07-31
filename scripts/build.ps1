# Build EXE

$ErrorActionPreference = "Stop"

$timer = [System.Diagnostics.Stopwatch]::StartNew()

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot
$browserPath = Join-Path $projectRoot "browsers"

Write-Host "=== BUILD START ==="

# Czyszczenie builda
if (Test-Path build) {
    Write-Host "Cleaning build directory..."
    Remove-Item -Recurse -Force build/* -ErrorAction SilentlyContinue
}

# Sprawdzenie czy browsers istnieją
if (-Not (Test-Path "browsers")) {
    Write-Host "ERROR: 'browsers' directory not found!"
    Write-Host "Run Setup Environment first."
    exit 1
}

# Build PyInstaller
Write-Host "Running PyInstaller..."

python -m uv run pyinstaller `
    --clean `
    --onedir `
    --name stock_scanner `
    --add-data "$browserPath;browsers" `
    --distpath build/dist `
    --workpath build/work `
    --specpath build/spec `
    src/main.py

# (opcjonalnie) kopiowanie assets
if (Test-Path "src/assets") {
    Write-Host "Copying assets..."
    Copy-Item -Recurse -Force src/assets build/dist/assets
}

$timer.Stop()

Write-Host "=== BUILD FINISHED ==="
Write-Host "Time: $($timer.Elapsed)"