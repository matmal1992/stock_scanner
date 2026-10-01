$ErrorActionPreference = "Stop"

$dumpFolder = "C:\StockScannerDumps"
$werPath = "HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\stock_scanner.exe"

Write-Host "Creating WER dump directory: $dumpFolder"

if (-not (Test-Path $dumpFolder)) {
    New-Item -Path $dumpFolder -ItemType Directory -Force | Out-Null
}

Write-Host "Configuring WER LocalDumps for stock_scanner.exe..."

New-Item `
    -Path $werPath `
    -Force | Out-Null

New-ItemProperty `
    -Path $werPath `
    -Name "DumpFolder" `
    -PropertyType ExpandString `
    -Value $dumpFolder `
    -Force | Out-Null

New-ItemProperty `
    -Path $werPath `
    -Name "DumpCount" `
    -PropertyType DWord `
    -Value 10 `
    -Force | Out-Null

New-ItemProperty `
    -Path $werPath `
    -Name "DumpType" `
    -PropertyType DWord `
    -Value 1 `
    -Force | Out-Null

Write-Host ""
Write-Host "WER LocalDumps configured successfully."
Write-Host "Application : stock_scanner.exe"
Write-Host "Dump folder : $dumpFolder"
Write-Host "Dump count  : 10"
Write-Host "Dump type   : 1 (MiniDump)"
Write-Host ""