$ErrorActionPreference = "Stop"

$script = Join-Path $PSScriptRoot "scripts\verify_metrics_v3.ps1"
if (-not (Test-Path -LiteralPath $script)) {
    throw "Missing delegated script: $script"
}

& $script @args
exit $LASTEXITCODE

