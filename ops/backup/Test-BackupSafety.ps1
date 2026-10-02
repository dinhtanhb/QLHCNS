# Synthetic command-level tests. No connection to SQL Server or real backups.
param([ValidateSet('Full', 'Log')][string]$Kind = 'Full',
      [ValidateSet('Express', 'Standard', 'Failure')][string]$Scenario = 'Express')
$ErrorActionPreference = 'Stop'
$root = Join-Path ([IO.Path]::GetTempPath()) ('ihrms-backup-test-' + [guid]::NewGuid())
New-Item -ItemType Directory -Path $root | Out-Null
$folder = if ($Kind -eq 'Full') { 'Daily' } else { 'TransactionLog' }
$extension = if ($Kind -eq 'Full') { 'bak' } else { 'trn' }
$directory = Join-Path $root $folder
New-Item -ItemType Directory -Path $directory | Out-Null
$old = Join-Path $directory "TestDB_old.$extension"
$other = Join-Path $directory "OtherDB_old.$extension"
# Match actual retention prefixes.
$prefix = if ($Kind -eq 'Full') { 'full' } else { 'log' }
$old = Join-Path $directory "TestDB_${prefix}_old.$extension"
$other = Join-Path $directory "OtherDB_${prefix}_old.$extension"
Set-Content $old 'synthetic old backup'
Set-Content $other 'synthetic unrelated backup'
(Get-Item $old).LastWriteTime = (Get-Date).AddYears(-2)
(Get-Item $other).LastWriteTime = (Get-Date).AddYears(-2)
$global:BackupTestQueries = @()
function global:sqlcmd {
    $arguments = @($args)
    foreach ($required in @('-b','-V','-x')) {
        if ($required -notin $arguments) { throw "Missing checked sqlcmd flag: $required" }
    }
    $query = $arguments[[Array]::IndexOf($arguments, '-Q') + 1]
    $global:BackupTestQueries += $query
    $global:LASTEXITCODE = 0
    if ($query -match 'EngineEdition') {
        if ($Scenario -eq 'Standard') { return '2' }
        return '4'
    }
    if ($query.Contains("SERVERPROPERTY('Edition')")) {
        if ($Scenario -eq 'Standard') { return '1' }
        return '0'
    }
    if ($query -notmatch 'RESTORE VERIFYONLY' -or $query -notmatch 'CHECKSUM') { throw 'Verification missing' }
    if ($query -match "TO DISK = N'([^']+)'") { Set-Content -LiteralPath $Matches[1] 'synthetic new backup' }
    if ($Scenario -eq 'Failure') { $global:LASTEXITCODE = 1; return 'simulated verification failure' }
}
try {
    # Parser checks every operational script, not just the chosen path.
    foreach ($file in Get-ChildItem $PSScriptRoot -Filter 'Backup-*.ps1') {
        $tokens = $null; $parseErrors = $null
        [void][Management.Automation.Language.Parser]::ParseFile($file.FullName, [ref]$tokens, [ref]$parseErrors)
        if ($parseErrors.Count) { throw "PowerShell parse failed: $($file.Name)" }
    }
    $script = if ($Kind -eq 'Full') { 'Backup-FullDatabase.ps1' } else { 'Backup-TransactionLog.ps1' }
    # Script exits 1 on failure, so test failure via a child process harness.
    if ($Scenario -eq 'Failure') {
        $helper = Join-Path $root 'run-failure.ps1'
        $mock = (Get-Item function:sqlcmd).Definition
        $target = Join-Path $PSScriptRoot $script
        Set-Content $helper "`$Scenario = 'Failure'; function global:sqlcmd { $mock }; & '$target' -Database TestDB -BackupRoot '$root'; exit `$LASTEXITCODE"
        $output = & (Join-Path $PSHOME 'pwsh') -NoProfile -File $helper 2>&1
        if ($LASTEXITCODE -ne 1) { throw 'Failure did not return exit 1' }
        if (-not (Test-Path $old)) { throw 'Failure deleted old valid backup' }
        if (Get-ChildItem $directory -Filter '*.sha256') { throw 'Failure recorded verified checksum' }
    } else {
        & (Join-Path $PSScriptRoot $script) -Database TestDB -BackupRoot $root
        if (Test-Path $old) { throw 'Successful verified backup did not apply retention' }
        if (-not (Test-Path $other)) { throw 'Retention deleted another database backup' }
        if (-not (Get-ChildItem $directory -Filter '*.sha256')) { throw 'No verified checksum' }
        $backupQuery = $global:BackupTestQueries[-1]
        if ($Scenario -eq 'Express' -and $backupQuery -notmatch 'NO_COMPRESSION') { throw 'Express compressed backup' }
        if ($Scenario -eq 'Standard' -and $backupQuery -match 'NO_COMPRESSION') { throw 'Standard compression unavailable' }
    }
    # Expected child exit 1 was asserted above; do not leak it to a CI shell.
    $global:LASTEXITCODE = 0
    Write-Output "PASS: $Kind / $Scenario (sqlcmd mocked; real SQL restore not tested)"
} finally {
    Remove-Item function:sqlcmd -ErrorAction SilentlyContinue
    Remove-Item $root -Recurse -Force
}
