# NOTE: if execution policy blocks running this script, launch PowerShell with:
#   PowerShell -ExecutionPolicy Bypass -File .\verify_metrics_v3.ps1
param(
    [int]$Season = 2025,
    [int]$Week = 9,
    [string]$TeamA = "MIA",
    [string]$TeamB = "BAL",
    [switch]$SkipBuild,
    [switch]$SkipL4
)

$ErrorActionPreference = "Stop"

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "== $Text =="
}

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Action
    )
    Write-Header -Text $Name
    try {
        & $Action
        Write-Host "OK: $Name"
    } catch {
        Write-Host "FAILED: $Name"
        Write-Host $_.Exception.Message
        throw
    }
}

function Test-FileRequired {
    param([string]$Path)
    if (!(Test-Path -LiteralPath $Path)) {
        throw "Missing file: $Path"
    }
}

function Test-ManifestFile {
    param(
        [string]$Layer,
        [string]$Season,
        [int]$Week,
        [string]$ParquetPath
    )
    $candidates = @(
        "data/$Layer/$Season/${Week}_manifest.json",
        "data/$Layer/$Season/$Week/manifest.json",
        "data/$Layer/$Season/$Week-manifest.json",
        "data/$Layer/$Season/$Week/$Week_manifest.json"
    )
    $manifest = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $manifest) {
        throw "Manifest not found for layer '$Layer'. Tried: `n$($candidates -join "`n")"
    }

    Write-Host "Manifest found: $manifest"
    $json = Get-Content -Raw -LiteralPath $manifest | ConvertFrom-Json
    if (-not $json.layer) { throw "Manifest missing 'layer' key." }
    if ($json.layer -notlike "*$Layer*") { throw "Manifest 'layer' mismatch. Value: $($json.layer)" }
    if (-not $json.rows -or [int]$json.rows -le 0) { throw "Manifest 'rows' must be > 0. Value: $($json.rows)" }
    if (-not $json.sha256) { throw "Manifest missing 'sha256'." }
    if (-not $json.files -or $json.files.Count -eq 0) { throw "Manifest 'files' list empty." }

    $hasParquet = $false
    foreach ($f in $json.files) {
        if ($f -like "*$ParquetPath") { $hasParquet = $true; break }
    }
    if (-not $hasParquet) {
        Write-Host "Note: Manifest 'files' doesn't explicitly include $ParquetPath (may be acceptable if relative paths are used)."
    }
}

function Test-ParquetColumns {
    param(
        [string]$Path,
        [string]$RequiredColumnsCsv
    )
    Test-FileRequired -Path $Path
    $py = @"
import polars as pl, sys
p = r'''$Path'''
req_csv = r'''$RequiredColumnsCsv'''
required = [c.strip() for c in req_csv.split(',') if c.strip()]
df = pl.read_parquet(p)
cols = set(df.columns)
missing = [c for c in required if c not in cols]
print('File:', p)
print('Rows:', len(df))
print('Columns:', sorted(list(cols)))
print('Required:', required)
if missing:
    print('MISSING:', missing)
    sys.exit(2)
"@
    python -c $py | Write-Host
    if ($LASTEXITCODE -ne 0) { throw "Required columns missing in $Path" }
}

# Ensure we are at repo root (heuristic: app/cli.py exists)
if (!(Test-Path -LiteralPath "app/cli.py")) {
    throw "Run this script from the repository root (where 'app/cli.py' exists)."
}

# 0) Activate venv
Invoke-Step -Name "Activate virtual environment" -Action {
    $activate = ".\.venv\Scripts\Activate.ps1"
    if (!(Test-Path -LiteralPath $activate)) { throw "Could not find $activate" }
    . $activate
    python --version | Write-Host
}

# 1) Build week (ETL + metrics) unless skipped
if (-not $SkipBuild) {
    Invoke-Step -Name "Build L1->L4 for season=$Season week=$Week" -Action {
        if ($SkipL4) {
            python -m app.cli build-week --season $Season --week $Week --skip-l4
        } else {
            python -m app.cli build-week --season $Season --week $Week
        }
    }

    Invoke-Step -Name "Build weekly reports (pairs-only)" -Action {
        python -m app.cli build-weekly-reports --season $Season --week $Week --pairs-only
    }
} else {
    Write-Host "Skipping build steps (--SkipBuild provided)."
}

# Expected files
$l1 = "data/l1/$Season/$Week.parquet"
$l2 = "data/l2/$Season/$Week.parquet"
$l3 = "data/l3_team_week/$Season/$Week.parquet"
$l4c = "data/l4_core12/$Season/$Week.parquet"
$l4p = "data/l4_powerscore/$Season/$Week.parquet"

# 2) Sanity: L1/L2/L3 columns
Invoke-Step -Name "Check L1 parquet columns" -Action {
    Test-ParquetColumns -Path $l1 -RequiredColumnsCsv "season,week,game_id,play_id,posteam,defteam,epa,success,yardline_100,down,distance"
}
Invoke-Step -Name "Check L2 parquet columns" -Action {
    Test-ParquetColumns -Path $l2 -RequiredColumnsCsv "season,week,game_id,play_id,TEAM,OPP,epa,success,success_bin,yards_gained,play_type,drive"
}
Invoke-Step -Name "Check L3 parquet columns" -Action {
    Test-ParquetColumns -Path $l3 -RequiredColumnsCsv "season,week,TEAM,drives,plays,epa_off_mean,epa_def_mean,success_rate_off,success_rate_def,tempo"
}

# 3) Sanity: L4 Core12 + PowerScore
if ($SkipL4) {
    Write-Host "Skipping L4 checks (--SkipL4)."
} else {
    Invoke-Step -Name "Check L4 Core12 parquet columns & manifest" -Action {
        Test-ParquetColumns -Path $l4c -RequiredColumnsCsv "season,week,TEAM,core_epa_off,core_epa_def,core_sr_off,core_sr_def,core_ed_sr_off,core_third_down_conv"
        Test-ManifestFile -Layer "l4_core12" -Season $Season -Week $Week -ParquetPath $l4c
    }

    Invoke-Step -Name "Check L4 PowerScore parquet columns & manifest" -Action {
        Test-ParquetColumns -Path $l4p -RequiredColumnsCsv "season,week,team,power_score"
        Test-ManifestFile -Layer "l4_powerscore" -Season $Season -Week $Week -ParquetPath $l4p
    }
}

# 4) Comparison report
$cmpOutDir = "data/reports/comparisons/${Season}_w${Week}"
$cmpOut = Join-Path $cmpOutDir "${TeamA}_vs_${TeamB}.md"
Invoke-Step -Name "Generate comparison report ${TeamA} vs ${TeamB}" -Action {
    python -m app.cli compare-report --season $Season --week $Week --team-a $TeamA --team-b $TeamB
    Test-FileRequired -Path $cmpOut
    Write-Host "Report path: $cmpOut"
    $assets = Join-Path $cmpOutDir "assets"
    if (Test-Path -LiteralPath $assets) {
        Write-Host "Assets directory: $assets"
        Get-ChildItem -LiteralPath $assets -File | Select-Object -First 10 | ForEach-Object { Write-Host " - " $_.FullName }
    }
    $cmpManifest = Join-Path $cmpOutDir "manifest.json"
    if (Test-Path -LiteralPath $cmpManifest) {
        Write-Host "Comparison manifest: $cmpManifest"
    } else {
        Write-Host "Note: comparison manifest not found (may be written at batch level)."
    }
}

# 5) Weekly summary presence
Invoke-Step -Name "Weekly summary presence" -Action {
    $weeklySummary = "data/reports/${Season}_w${Week}_summary.md"
    if (!(Test-Path -LiteralPath $weeklySummary)) {
        $weeklySummary = "data/reports/${Season}_w${Week}/weekly_summary.md"
    }
    Test-FileRequired -Path $weeklySummary
    Write-Host "Weekly summary: $weeklySummary"
}

# 6) Run tests
Invoke-Step -Name "Run pytest (quiet)" -Action {
    python -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw "Pytest returned non-zero exit code." }
}

Write-Host ""
Write-Host "All checks passed."
Write-Host "Comparison report: $cmpOut"
Write-Host "Tip: Re-run with different teams, e.g.:"
Write-Host "  PowerShell -ExecutionPolicy Bypass -File .\verify_metrics_v3.ps1 -Season $Season -Week $Week -TeamA KC -TeamB BUF [-SkipL4]"

