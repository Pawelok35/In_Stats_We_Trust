Param(
    [int]$Season,
    [switch]$PairsOnly
)

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$pythonExe = Join-Path $repoRoot '.venv/./Scripts/python.exe'
if (-not (Test-Path $pythonExe)) {
    $pythonExe = 'python'
}

$originalPythonPath = $env:PYTHONPATH
if ([string]::IsNullOrEmpty($originalPythonPath)) {
    $env:PYTHONPATH = $repoRoot
} else {
    $env:PYTHONPATH = "$repoRoot;$originalPythonPath"
}

function Resolve-Season {
    param([int]$InputSeason)
    if ($InputSeason) { return $InputSeason }

    $defaultSeason = & $pythonExe -c "from utils.config import load_settings; print(load_settings().default_season)"
    if ($LASTEXITCODE -ne 0 -or -not $defaultSeason) {
        throw 'Unable to resolve default season from configuration.'
    }
    return [int]$defaultSeason.Trim()
}

function Resolve-FinishedWeek {
    param([int]$ResolvedSeason)

    $pythonCode = @"
import sys
import datetime as dt
from pathlib import Path

import polars as pl

from utils.config import load_settings

season = int(sys.argv[1])
settings = load_settings()
data_root = settings.data_root

finished_weeks = set()

schedule_path = data_root / "schedules" / f"{season}.parquet"
if schedule_path.exists():
    try:
        schedule = pl.read_parquet(schedule_path)
    except Exception:
        schedule = None
    else:
        if "week" in schedule.columns:
            if "game_date" in schedule.columns:
                today = dt.date.today()
                try:
                    schedule = schedule.filter(pl.col("game_date") <= pl.lit(today))
                except Exception:
                    pass
            weeks = schedule.select("week").drop_nulls().unique().to_series().to_list()
            finished_weeks.update(int(w) for w in weeks if w is not None)

if not finished_weeks:
    for week in range(22, 0, -1):
        l2_path = data_root / "l2" / str(season) / f"{week}.parquet"
        if l2_path.exists():
            finished_weeks.add(week)
            break

if not finished_weeks:
    raise SystemExit("NO_WEEK")

print(max(finished_weeks))
"@

    $tempPy = [System.IO.Path]::GetTempFileName() + '.py'
    Set-Content -Path $tempPy -Value $pythonCode -Encoding UTF8
    $result = & $pythonExe $tempPy $ResolvedSeason
    $status = $LASTEXITCODE
    Remove-Item $tempPy -ErrorAction SilentlyContinue

    if ($status -ne 0) {
        if ($result -and $result.Trim() -eq 'NO_WEEK') {
            throw "No finished week found for season $ResolvedSeason."
        }
        throw "Failed to determine the latest finished week for season $ResolvedSeason."
    }

    return [int]$result.Trim()
}

try {
    $resolvedSeason = Resolve-Season -InputSeason $Season
    $resolvedWeek = Resolve-FinishedWeek -ResolvedSeason $resolvedSeason

    Write-Host "Detected finished week: season $resolvedSeason, week $resolvedWeek" -ForegroundColor Cyan

    $buildArgs = @('build-week', '--season', $resolvedSeason, '--week', $resolvedWeek)
    Write-Host "Running: $pythonExe -m app.cli $($buildArgs -join ' ')" -ForegroundColor DarkGray
    & $pythonExe -m app.cli @buildArgs
    if ($LASTEXITCODE -ne 0) {
        throw "build-week failed for season $resolvedSeason week $resolvedWeek."
    }

    $reportArgs = @('build-weekly-reports', '--season', $resolvedSeason, '--week', $resolvedWeek)
    if ($PairsOnly) {
        $reportArgs += '--pairs-only'
    }
    Write-Host "Running: $pythonExe -m app.cli $($reportArgs -join ' ')" -ForegroundColor DarkGray
    & $pythonExe -m app.cli @reportArgs
    if ($LASTEXITCODE -ne 0) {
        throw "build-weekly-reports failed for season $resolvedSeason week $resolvedWeek."
    }

    Write-Host "Finished update for season $resolvedSeason week $resolvedWeek." -ForegroundColor Green
}
finally {
    if ([string]::IsNullOrEmpty($originalPythonPath)) {
        Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    } else {
        $env:PYTHONPATH = $originalPythonPath
    }
}
