$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Pythonw = Join-Path $RepoRoot ".venv\Scripts\pythonw.exe"
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Script = Join-Path $RepoRoot "scripts\variant_b_daily_bot_gui.py"

if (Test-Path $Pythonw) {
    Start-Process -FilePath $Pythonw -ArgumentList "`"$Script`"" -WorkingDirectory $RepoRoot
} elseif (Test-Path $Python) {
    Start-Process -FilePath $Python -ArgumentList "`"$Script`"" -WorkingDirectory $RepoRoot
} else {
    throw "Nie znaleziono .venv\Scripts\python.exe"
}
