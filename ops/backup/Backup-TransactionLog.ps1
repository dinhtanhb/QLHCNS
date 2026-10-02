<#
.SYNOPSIS
    Backup transaction log cho qlhcns, chạy MỖI GIỜ theo docs/08_Deployment_
    Standards.md mục 18. Bắt buộc database đã ở chế độ FULL recovery (chạy
    Setup-RecoveryModel.sql một lần trước khi dùng script này — xem README.md).
#>

param(
    [string]$ServerInstance = "localhost\SQLEXPRESS",
    [Parameter(Mandatory = $true)][ValidatePattern("^[A-Za-z0-9_-]+$")][string]$Database,
    [string]$BackupRoot     = "D:\QLHCNS\Backups",
    [ValidateRange(30, 3650)][int]$RetentionDays = 30   # giữ ít nhất bằng cửa sổ Daily để không tự cắt chuỗi khôi phục
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "Backup-Common.ps1")
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss_fffffff"
$logDir    = Join-Path $BackupRoot "TransactionLog"
$logFile   = Join-Path $BackupRoot "backup-log.txt"

if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

function Write-BackupLog {
    param([string]$Message, [string]$Level = "INFO")
    $line = "[{0}] {1}: {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Level, $Message
    Add-Content -Path $logFile -Value $line -Encoding UTF8
    Write-Output $line
}

$backupFile = Join-Path $logDir "${Database}_log_$timestamp.trn"

try {
    Write-BackupLog "Bắt đầu TRANSACTION LOG backup -> $backupFile"

    $hash = New-VerifiedDatabaseBackup -ServerInstance $ServerInstance -Database $Database -BackupFile $backupFile -Kind LOG
    Write-BackupLog "Backup checksum/VERIFYONLY đạt; SHA256=$hash"

    Write-BackupLog "Log backup thành công: $backupFile"

    Get-ChildItem $logDir -Filter "${Database}_log_*.trn" |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$RetentionDays) } |
        ForEach-Object { Write-BackupLog "Xoá log backup quá hạn: $($_.Name)"; Remove-Item $_.FullName -Force }
}
catch {
    Write-BackupLog "LỖI LOG BACKUP: $($_.Exception.Message)" "ERROR"
    exit 1
}
