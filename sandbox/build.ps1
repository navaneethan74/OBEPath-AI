# ==============================================================================
# Build OBEPath Sandbox Image (Windows PowerShell)
# Target Image Tag: obepath-sandbox:1
# ==============================================================================
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "Building obepath-sandbox:1 from $ScriptDir..." -ForegroundColor Cyan

docker build -t obepath-sandbox:1 "$ScriptDir"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Successfully built and tagged obepath-sandbox:1" -ForegroundColor Green
} else {
    Write-Host "Failed to build obepath-sandbox:1 (Exit code: $LASTEXITCODE)" -ForegroundColor Red
    exit $LASTEXITCODE
}
