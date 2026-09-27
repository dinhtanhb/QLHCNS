$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$logDir = Join-Path $repoRoot 'Logs'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$logFile = Join-Path $logDir ("lifecycle-reminders-{0}.log" -f (Get-Date -Format 'yyyyMMdd'))

$pythonPath = $env:IHRMS_PYTHON
if (-not $pythonPath) {
    $pythonPath = Join-Path $repoRoot 'venv\Scripts\python.exe'
}
if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
    throw "Python executable not found: $pythonPath. Set IHRMS_PYTHON or create the project venv."
}

Push-Location $repoRoot
try {
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'
    Add-Content -LiteralPath $logFile -Value "[$timestamp] --- Bat dau chay send_lifecycle_reminders ---"

    # QUAN TRONG: khi stdout/stderr cua python.exe bi redirect ra file (khong con la
    # console that), Windows mac dinh dung bang ma cua he thong (vd cp1252 - Tay Au),
    # bang ma nay KHONG co chu tieng Viet co dau ("Đ", "ạ"...) -> crash
    # UnicodeEncodeError ngay khi Django in thong bao tieng Viet ra output. Ep bien moi
    # truong nay de python.exe luon dung UTF-8 cho stdout/stderr, bat ke co redirect
    # hay khong - day la cach sua chuan cho dung loi nay tren Windows.
    $env:PYTHONIOENCODING = 'utf-8'
    $env:PYTHONUTF8 = '1'

    & $pythonPath 'src\manage.py' 'send_lifecycle_reminders' *>> $logFile
    $exitCode = $LASTEXITCODE

    Add-Content -LiteralPath $logFile -Value "[$timestamp] --- Ket thuc, exit code: $exitCode ---"

    if ($exitCode -ne 0) {
        throw "Reminder command failed with exit code $exitCode. See $logFile"
    }
}
finally {
    Pop-Location
}