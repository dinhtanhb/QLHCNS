<#
.SYNOPSIS
    Backup FULL cho database qlhcns trên SQL Server Express, kèm quy tắc lưu
    trữ Daily/Weekly/Monthly đúng theo docs/08_Deployment_Standards.md mục 19:
        - Daily backup:   giữ 30 ngày
        - Weekly backup:  giữ 12 tuần   (lấy bản backup của Chủ Nhật)
        - Monthly backup: giữ 12 tháng  (lấy bản backup ngày mùng 1)

.NOTES
    SQL Server Express KHÔNG có SQL Server Agent nên không lên lịch job được
    trong SSMS như bản Standard/Enterprise. Thay vào đó, dùng Windows Task
    Scheduler để chạy file .ps1 này hằng ngày lúc 22:00 (xem README.md cùng
    thư mục để biết cách đăng ký Task).
#>

param(
    [string]$ServerInstance = "localhost\SQLEXPRESS",
    [Parameter(Mandatory = $true)][ValidatePattern("^[A-Za-z0-9_-]+$")][string]$Database,
    [string]$BackupRoot     = "D:\QLHCNS\Backups"
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "Backup-Common.ps1")
$timestamp   = Get-Date -Format "yyyyMMdd_HHmmss_fffffff"
$dailyDir    = Join-Path $BackupRoot "Daily"
$weeklyDir   = Join-Path $BackupRoot "Weekly"
$monthlyDir  = Join-Path $BackupRoot "Monthly"
$logFile     = Join-Path $BackupRoot "backup-log.txt"

foreach ($dir in @($dailyDir, $weeklyDir, $monthlyDir)) {
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
}

function Write-BackupLog {
    param([string]$Message, [string]$Level = "INFO")
    $line = "[{0}] {1}: {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Level, $Message
    Add-Content -Path $logFile -Value $line -Encoding UTF8
    Write-Output $line
}

$backupFile = Join-Path $dailyDir "${Database}_full_$timestamp.bak"

try {
    Write-BackupLog "Bắt đầu FULL backup -> $backupFile"

    $hash = New-VerifiedDatabaseBackup -ServerInstance $ServerInstance -Database $Database -BackupFile $backupFile -Kind DATABASE
    Write-BackupLog "Backup checksum/VERIFYONLY đạt; SHA256=$hash"

    Write-BackupLog "FULL backup thành công: $backupFile"

    # -- Copy sang Weekly nếu hôm nay là Chủ Nhật ---------------------------
    if ((Get-Date).DayOfWeek -eq [System.DayOfWeek]::Sunday) {
        $weeklyFile = Join-Path $weeklyDir (Split-Path $backupFile -Leaf)
        Copy-Item -Path $backupFile -Destination $weeklyFile -Force
        if ((Get-FileHash -LiteralPath $weeklyFile -Algorithm SHA256).Hash -ne $hash) { throw "Weekly copy checksum mismatch." }
        Write-BackupLog "Đã sao chép sang Weekly: $weeklyFile"
    }

    # -- Copy sang Monthly nếu hôm nay là ngày mùng 1 -----------------------
    if ((Get-Date).Day -eq 1) {
        $monthlyFile = Join-Path $monthlyDir (Split-Path $backupFile -Leaf)
        Copy-Item -Path $backupFile -Destination $monthlyFile -Force
        if ((Get-FileHash -LiteralPath $monthlyFile -Algorithm SHA256).Hash -ne $hash) { throw "Monthly copy checksum mismatch." }
        Write-BackupLog "Đã sao chép sang Monthly: $monthlyFile"
    }

    # -- Dọn theo retention: Daily 30 ngày / Weekly 12 tuần / Monthly 12 tháng
    Get-ChildItem $dailyDir -Filter "${Database}_full_*.bak" |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
        ForEach-Object { Write-BackupLog "Xoá Daily quá hạn: $($_.Name)"; Remove-Item $_.FullName -Force }

    Get-ChildItem $weeklyDir -Filter "${Database}_full_*.bak" |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-84) } |
        ForEach-Object { Write-BackupLog "Xoá Weekly quá hạn: $($_.Name)"; Remove-Item $_.FullName -Force }

    Get-ChildItem $monthlyDir -Filter "${Database}_full_*.bak" |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddMonths(-12) } |
        ForEach-Object { Write-BackupLog "Xoá Monthly quá hạn: $($_.Name)"; Remove-Item $_.FullName -Force }

    # -- Backup luôn thư mục /Logs (Application Logs) theo mục 20 -----------
    $logsSource = "D:\QLHCNS\Logs"
    $logsBackupDir = Join-Path $BackupRoot "ApplicationLogs\$timestamp"
    if (Test-Path $logsSource) {
        Copy-Item -Path $logsSource -Destination $logsBackupDir -Recurse -Force
        Write-BackupLog "Đã backup Application Logs -> $logsBackupDir"

        Get-ChildItem (Join-Path $BackupRoot "ApplicationLogs") -Directory |
            Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
            ForEach-Object { Write-BackupLog "Xoá ApplicationLogs backup quá hạn: $($_.Name)"; Remove-Item $_.FullName -Recurse -Force }
    }

    Write-BackupLog "HOÀN TẤT backup ngày $timestamp."
}
catch {
    Write-BackupLog "LỖI BACKUP: $($_.Exception.Message)" "ERROR"
    # Thoát với mã lỗi khác 0 để Windows Task Scheduler ghi nhận Task thất bại
    # (hiện trong tab History dạng "The operation completed with exit code X").
    exit 1
}
