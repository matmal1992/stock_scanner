$ErrorActionPreference = "Stop"

# ---------------------------------------------------------
# Restart script as Administrator when necessary
# ---------------------------------------------------------

$currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)

$isAdmin = $currentPrincipal.IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)

if (-not $isAdmin) {
    Write-Host "Administrator privileges are required."
    Write-Host "Requesting elevation..."

    $scriptPath = $MyInvocation.MyCommand.Path

    Start-Process `
        -FilePath "powershell.exe" `
        -Verb RunAs `
        -ArgumentList @(
            "-NoProfile"
            "-ExecutionPolicy", "Bypass"
            "-File", "`"$scriptPath`""
        )

    exit 0
}

# ---------------------------------------------------------
# Setup
# ---------------------------------------------------------

$timer = [System.Diagnostics.Stopwatch]::StartNew()

Write-Host "Running setup as Administrator..."
Write-Host ""

python -m pip install uv

python -m uv sync --all-extras

$env:PLAYWRIGHT_BROWSERS_PATH = "./browsers"

python -m uv run playwright install chromium

python -m uv run pre-commit install

# ---------------------------------------------------------
# Windows Error Reporting
# ---------------------------------------------------------

Write-Host ""
Write-Host "Configuring Windows Error Reporting (WER)..."

& "$PSScriptRoot/setup_wer.ps1"

# ---------------------------------------------------------
# Finished
# ---------------------------------------------------------

$timer.Stop()

Write-Host ""
Write-Host "Setup finished in $($timer.Elapsed)"

