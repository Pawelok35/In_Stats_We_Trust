param(
    [Parameter(Mandatory = $true)]
    [ValidateRange(1, 9999)]
    [int]$Season,
    [Parameter(Mandatory = $true)]
    [ValidateRange(1, 30)]
    [int]$Week,
    [Parameter(Mandatory = $false)]
    [ValidateSet(
        "init-week", "import-games", "import-candidates", "import-market-snapshots",
        "register-lineage", "build-audits", "register-decisions", "record-executions",
        "link-closing", "import-results", "settle-ready", "calculate-clv-ready",
        "status", "report", "run-ready"
    )]
    [string]$Command = "status",
    [Parameter(Mandatory = $false)]
    [string]$InputPath,
    [Parameter(Mandatory = $false)]
    [string]$Root = "data/pregame"
)

$repo = (Resolve-Path (Join-Path $PSScriptRoot ".." )).Path
$python = Join-Path $repo ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    $python = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $python -or -not (Test-Path -LiteralPath $python)) {
    throw "Python nie jest dostepny. Utworz .venv albo dodaj python do PATH."
}

$arguments = @(
    "-m", "pregame.weekly_cli",
    "--root", $Root,
    "--season", $Season.ToString(),
    "--week", $Week.ToString()
)
if ($InputPath) {
    $arguments += @("--input", $InputPath)
}
$arguments += $Command

Push-Location $repo
try {
    & $python @arguments
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
