# scripts/verify_repo.ps1
$ErrorActionPreference = 'Stop'

Write-Host '== QA gates ==' -ForegroundColor Cyan
python -m ruff check .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m black --check .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m pytest -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host '== CLI smoke ==' -ForegroundColor Cyan
python -m app.cli --help | Out-Null
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m app.cli build-week --season 2025 --week 8
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host '== Artefacts check ==' -ForegroundColor Cyan
$paths = @(
  'data/l4_core12/2025/8.parquet',
  'data/l4_core12/2025/8_manifest.json',
  'data/l4_powerscore/2025/8.parquet',
  'data/l4_powerscore/2025/8_manifest.json',
  'data/reports/2025_w8_summary.md'
)
$missing = @()
foreach ($p in $paths) { if (-not (Test-Path $p)) { $missing += $p } }
if ($missing.Count -gt 0) {
  Write-Host 'Missing artefacts:' -ForegroundColor Red
  $missing | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }
  exit 1
}

Write-Host '== Manifest sanity ==' -ForegroundColor Cyan
$manifests = @(
  'data/l4_core12/2025/8_manifest.json',
  'data/l4_powerscore/2025/8_manifest.json'
)
foreach ($m in $manifests) {
  $j = Get-Content $m -Raw | ConvertFrom-Json
  if (-not $j.path -or -not $j.rows -or -not $j.cols) {
    Write-Host "Bad manifest: $m" -ForegroundColor Red
    exit 1
  }
}

Write-Host '== Reports QA ==' -ForegroundColor Cyan
python -m app.cli build-weekly-reports --season 2025 --week 8 | Out-Null
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$teamReportsDir = 'data/reports/teams/2025_w8'
if (-not (Test-Path $teamReportsDir)) {
  Write-Host "Missing team reports directory: $teamReportsDir" -ForegroundColor Red
  exit 1
}

$teamReports = Get-ChildItem -Path $teamReportsDir -Filter '*.md' -File -ErrorAction SilentlyContinue
if (-not $teamReports -or $teamReports.Count -lt 1) {
  Write-Host 'No team reports generated.' -ForegroundColor Red
  exit 1
}

$teamManifestPath = Join-Path $teamReportsDir 'manifest.json'
if (-not (Test-Path $teamManifestPath)) {
  Write-Host "Missing team report manifest: $teamManifestPath" -ForegroundColor Red
  exit 1
}

$teamAssetsRoot = Join-Path $teamReportsDir 'assets'

foreach ($report in $teamReports) {
  $content = (Get-Content $report.FullName -Raw).Trim()
  if (-not $content) {
    Write-Host "Empty team report detected: $($report.FullName)" -ForegroundColor Red
    exit 1
  }

  $teamCode = [System.IO.Path]::GetFileNameWithoutExtension($report.Name)
  $teamAssetsDir = Join-Path $teamAssetsRoot $teamCode
  if (-not (Test-Path $teamAssetsDir)) {
    Write-Host "Missing assets directory for team $teamCode" -ForegroundColor Red
    exit 1
  }

  $charts = Get-ChildItem -Path $teamAssetsDir -Filter '*.png' -File -ErrorAction SilentlyContinue
  if (-not $charts -or $charts.Count -lt 1) {
    Write-Host "No charts found for team $teamCode" -ForegroundColor Red
    exit 1
  }
}

$teamManifest = Get-Content $teamManifestPath -Raw | ConvertFrom-Json
if (-not $teamManifest.files -or $teamManifest.files.Count -lt 1) {
  Write-Host 'Team report manifest missing file entries.' -ForegroundColor Red
  exit 1
}

foreach ($entry in $teamManifest.files) {
  if (-not $entry.path -or -not $entry.sha256) {
    Write-Host 'Invalid manifest entry detected.' -ForegroundColor Red
    exit 1
  }
  if (-not $entry.size -or $entry.size -lt 0) {
    Write-Host 'Manifest entry missing size information.' -ForegroundColor Red
    exit 1
  }
}

$weeklySummaryPath = 'data/reports/2025_w8/weekly_summary.md'
if (-not (Test-Path $weeklySummaryPath)) {
  Write-Host "Weekly summary not found at $weeklySummaryPath" -ForegroundColor Red
  exit 1
}

$weeklySummaryContent = (Get-Content $weeklySummaryPath -Raw).Trim()
if (-not $weeklySummaryContent) {
  Write-Host 'Weekly summary is empty.' -ForegroundColor Red
  exit 1
}

Write-Host '== Reports QA == OK' -ForegroundColor Green

Write-Host '== API health (optional) ==' -ForegroundColor Cyan
# Optional: invoke FastAPI health check if uvicorn is available
# Start-Process -FilePath 'python' -ArgumentList '-m uvicorn app.api:app --port 8765' -PassThru | Out-Null
# Start-Sleep -Seconds 2
# try { (Invoke-WebRequest -Uri 'http://127.0.0.1:8765/health' -UseBasicParsing).StatusCode } catch { $_; exit 1 }
# Get-Process -Name 'uvicorn' -ErrorAction SilentlyContinue | Stop-Process

Write-Host "`nALL CHECKS PASSED." -ForegroundColor Green
