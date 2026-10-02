# Shared checked sqlcmd invocation. Run on the SQL Server host, or use a UNC
# BackupRoot accessible to both SQL Server and the scheduled-task account.
function Invoke-BackupSql {
    param([string]$ServerInstance, [string]$Query, [switch]$Scalar)
    $result = & sqlcmd -S $ServerInstance -E -b -V 11 -x -h -1 -W -Q $Query 2>&1
    if ($LASTEXITCODE -ne 0) { throw "sqlcmd failed (exit $LASTEXITCODE); backup/verification did not succeed." }
    if ($Scalar) { return (($result | Out-String).Trim()) }
    $result | Out-Host
}

function New-VerifiedDatabaseBackup {
    param([string]$ServerInstance, [string]$Database, [string]$BackupFile,
          [ValidateSet("DATABASE", "LOG")][string]$Kind)
    $edition = Invoke-BackupSql $ServerInstance "SET NOCOUNT ON; SELECT CAST(SERVERPROPERTY('EngineEdition') AS int);" -Scalar
    if ($edition -notmatch '^[234]$') { throw "Unsupported/unknown SQL Server edition: $edition" }
    # Explicit NO_COMPRESSION also overrides an incompatible server default on Express.
    # EngineEdition=2 includes Web, whose backup compression is unavailable.
    $canCompress = Invoke-BackupSql $ServerInstance "SET NOCOUNT ON; SELECT CASE WHEN CAST(SERVERPROPERTY('Edition') AS nvarchar(128)) LIKE '%Enterprise%' OR CAST(SERVERPROPERTY('Edition') AS nvarchar(128)) LIKE '%Standard%' OR CAST(SERVERPROPERTY('Edition') AS nvarchar(128)) LIKE '%Developer%' THEN 1 ELSE 0 END;" -Scalar
    if ($canCompress -notmatch '^[01]$') { throw "Cannot determine backup compression support." }
    $compression = if ($edition -ne '4' -and $canCompress -eq '1') { "COMPRESSION" } else { "NO_COMPRESSION" }
    $dbIdentifier = $Database.Replace("]", "]]")
    $fileLiteral = $BackupFile.Replace("'", "''")
    if (Test-Path -LiteralPath $BackupFile) { throw "Refusing to overwrite an existing backup." }
    $sql = "BACKUP $Kind [$dbIdentifier] TO DISK = N'$fileLiteral' WITH INIT, $compression, CHECKSUM; RESTORE VERIFYONLY FROM DISK = N'$fileLiteral' WITH CHECKSUM;"
    Invoke-BackupSql $ServerInstance $sql
    if (-not (Test-Path -LiteralPath $BackupFile -PathType Leaf)) { throw "Cannot confirm new backup file locally; use a shared BackupRoot." }
    if ((Get-Item -LiteralPath $BackupFile).Length -le 0) { throw "New backup is empty." }
    # A checksum is useful when copying; VERIFYONLY is not a restore drill.
    $hash = (Get-FileHash -LiteralPath $BackupFile -Algorithm SHA256).Hash
    Set-Content -LiteralPath "$BackupFile.sha256" -Value $hash -Encoding ASCII
    return $hash
}
