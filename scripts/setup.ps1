# Set up environment 

$timer = [System.Diagnostics.Stopwatch]::StartNew()

python -m pip install uv
python -m uv sync --all-extras

$env:PLAYWRIGHT_BROWSERS_PATH = "./browsers"
python -m uv run playwright install chromium

python -m uv run pre-commit install

$timer.Stop()
Write-Host "Setup finished in $($timer.Elapsed)"