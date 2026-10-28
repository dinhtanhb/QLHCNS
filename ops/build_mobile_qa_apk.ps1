param(
    [string]$JavaHome = $env:JAVA_HOME,
    [string]$AndroidSdk = $env:ANDROID_HOME,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [string]$ApiUrl = '',
    [switch]$AllowLocalHttp,
    [string]$Architectures = 'arm64-v8a,x86_64'
)
$ErrorActionPreference = 'Stop'
function Invoke-CheckedNative {
    param([string]$Executable, [string[]]$Arguments)
    $previous = $ErrorActionPreference
    try {
        # Windows PowerShell represents stderr warnings as ErrorRecords. A
        # compiler warning is not a failed build; the native exit code decides.
        $ErrorActionPreference = 'Continue'
        & $Executable @Arguments
        if ($LASTEXITCODE -ne 0) { throw "Native command failed: $Executable (exit $LASTEXITCODE)" }
    } finally { $ErrorActionPreference = $previous }
}
$root = Split-Path -Parent $PSScriptRoot
$mobile = Join-Path $root 'mobile'
$destination = [IO.Path]::GetFullPath($OutputDirectory)
if ($destination -eq $root -or $destination.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'APK output must be outside the source repository.'
}
if (!(Test-Path -LiteralPath (Join-Path $JavaHome 'bin/java.exe')) -or !(Test-Path -LiteralPath $AndroidSdk)) {
    throw 'Supply a JDK and Android SDK via -JavaHome/-AndroidSdk or JAVA_HOME/ANDROID_HOME.'
}
if ($Architectures -notmatch '^(arm64-v8a|x86_64)(,(arm64-v8a|x86_64))*$') { throw 'Unsupported QA architecture list.' }
if ((& git -C $root branch --show-current) -ne 'main') { throw 'Build IHRMS only on main.' }
$env:JAVA_HOME = $JavaHome
$env:ANDROID_HOME = $AndroidSdk
$env:ANDROID_SDK_ROOT = $AndroidSdk
$env:PATH = (Join-Path $JavaHome 'bin') + ';' + $env:PATH
$env:CI = '1'
$env:MOBILE_VARIANT = 'qa'
$env:EXPO_PUBLIC_API_URL = $ApiUrl
$env:EXPO_PUBLIC_ALLOW_HTTP = if ($AllowLocalHttp) { 'true' } else { 'false' }
New-Item -ItemType Directory -Path $destination -Force | Out-Null
Push-Location $mobile
try {
    if (!(Test-Path -LiteralPath 'node_modules')) {
        Invoke-CheckedNative 'npm.cmd' @('ci')
    }
    & (Join-Path $PSScriptRoot 'prepare_mobile_hermes.ps1') -Directory (Join-Path $destination 'hermes')
    Invoke-CheckedNative 'npm.cmd' @('run', 'typecheck')
    Invoke-CheckedNative 'npm.cmd' @('run', 'lint')
    Invoke-CheckedNative 'npx.cmd' @('expo', 'prebuild', '--platform', 'android', '--no-install')
    Invoke-CheckedNative './android/gradlew.bat' @('-p', 'android', ':app:assembleRelease', "-PreactNativeArchitectures=$Architectures", '--no-daemon', '--max-workers=2')
    $source = Join-Path $mobile 'android/app/build/outputs/apk/release/app-release.apk'
    $target = Join-Path $destination 'IHRMS-QA.apk'
    Copy-Item -LiteralPath $source -Destination $target -Force
    $hash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
    $manifest = [ordered]@{
        artifact = 'IHRMS-QA.apk'; sha256 = $hash; package = 'vn.ihrms.internal.qa'
        source_commit = (& git -C $root rev-parse HEAD); source_tree_dirty = [bool](& git -C $root status --porcelain)
        local_http = [bool]$AllowLocalHttp; architectures = $Architectures
        signing = 'QA only: generated Android debug signing, not a production identity'
        production_release = $false
    }
    $manifest | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $destination 'apk-manifest.json') -Encoding UTF8
    Write-Output "QA APK: $target"
    Write-Output "SHA-256: $hash"
} finally { Pop-Location }
