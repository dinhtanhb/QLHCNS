<#
.SYNOPSIS
    Backup transaction log cho qlhcns, chạy MỖI GIỜ theo docs/08_Deployment_
    Standards.md mục 18. Bắt buộc database đã ở chế độ FULL recovery (chạy
    Setup-RecoveryModel.sql một lần trước khi dùng script này — xem README.md).
#>

param(
    [string]$ServerInstance = "localhost\SQLEXPRESS",
    [string]$Database       = "qlhcns",
    [string]$BackupRoot     = "D:\QLHCNS\Backups",
    [int]$RetentionDays     = 3   # log backup chỉ cần giữ ngắn ngày, đủ để khôi phục điểm-trong-thời-gian giữa 2 lần full backup
)

$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logDir    = Join-Path $BackupRoot "TransactionLog"
$logFile   = Join-Path $BackupRoot "backup-log.txt"

if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

function Write-BackupLog {
    param([string]$Message, [string]$Level = "INFO")
    $line = "[{0}] {1}: {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Level, $Message
    Add-Content -Path $logFile -Value $line -Encoding UTF8
    Write-Output $line
}

$backupFile = Join-Path $logDir "qlhcns_log_$timestamp.trn"

try {
    Write-BackupLog "Bắt đầu TRANSACTION LOG backup -> $backupFile"

    $sql = @"
BACKUP LOG [$Database]
TO DISK = N'$backupFile'
WITH INIT, COMPRESSION, CHECKSUM;
"@

    sqlcmd -S $ServerInstance -E -Q $sql
    if ($LASTEXITCODE -ne 0) {
        throw "sqlcmd trả về mã lỗi $LASTEXITCODE. Kiểm tra database có đang ở chế độ FULL recovery không (chạy Setup-RecoveryModel.sql nếu chưa)."
    }

    Write-BackupLog "Log backup thành công: $backupFile"

    Get-ChildItem $logDir -Filter "*.trn" |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$RetentionDays) } |
        ForEach-Object { Write-BackupLog "Xoá log backup quá hạn: $($_.Name)"; Remove-Item $_.FullName -Force }
}
catch {
    Write-BackupLog "LỖI LOG BACKUP: $($_.Exception.Message)" "ERROR"
    exit 1
}