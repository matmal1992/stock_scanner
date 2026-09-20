Write-Host "Setup started"

$timer = [System.Diagnostics.Stopwatch]::StartNew()


Write-Host ""

python -m pip install --upgrade pip

python -m pip install uv

python -m uv sync --all-extras

$env:PLAYWRIGHT_BROWSERS_PATH = "./browsers"

python -m uv run playwright install chromium

python -m uv run pre-commit install

$timer.Stop()

Write-Host ""
Write-Host "Setup finished in $($timer.Elapsed)"

