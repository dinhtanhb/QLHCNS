$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$logDir = Join-Path $repoRoot 'Logs'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$logFile = Join-Path $logDir ("activity-reminders-{0}.log" -f (Get-Date -Format 'yyyyMMdd'))

$pythonPath = $env:IHRMS_PYTHON
if (-not $pythonPath) {
    $pythonPath = Join-Path $repoRoot 'venv\Scripts\python.exe'
}
if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
    throw "Python executable not found: $pythonPath. Set IHRMS_PYTHON or create the project venv."
}

Push-Location $repoRoot
try {
    # Keep redirected Python output UTF-8 even when this script is run outside
    # a console, such as from Task Scheduler or a PowerShell pipeline.
    $env:PYTHONIOENCODING = 'utf-8'
    $env:PYTHONUTF8 = '1'

    $output = & $pythonPath 'src\manage.py' 'send_activity_report_reminders' 2>&1
    $exitCode = $LASTEXITCODE
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'
    Add-Content -LiteralPath $logFile -Value "[$timestamp] $($output -join [Environment]::NewLine)"
    if ($exitCode -ne 0) {
        throw "Reminder command failed with exit code $exitCode. See $logFile"
    }
}
finally {
    Pop-Location
}
