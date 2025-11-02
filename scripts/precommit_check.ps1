$ErrorActionPreference = "Stop"

Write-Host "Running ruff..." -ForegroundColor Cyan
python -m ruff check .
if ($LASTEXITCODE -ne 0) { Write-Host "ruff failed" -ForegroundColor Red; exit $LASTEXITCODE }

Write-Host "Running black (check)..." -ForegroundColor Cyan
python -m black --check .
if ($LASTEXITCODE -ne 0) { Write-Host "black --check failed" -ForegroundColor Red; exit $LASTEXITCODE }

Write-Host "Running pytest..." -ForegroundColor Cyan
python -m pytest -q
if ($LASTEXITCODE -ne 0) { Write-Host "pytest failed" -ForegroundColor Red; exit $LASTEXITCODE }

Write-Host "All checks passed." -ForegroundColor Green
