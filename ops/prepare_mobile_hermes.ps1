param([Parameter(Mandatory = $true)][string]$Directory)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$dest = [IO.Path]::GetFullPath($Directory)
if ($dest -eq $root -or $dest.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Portable compiler must stay outside the source repository.'
}
$compiler = Join-Path $root 'mobile/node_modules/hermes-compiler/hermesc/win64-bin/hermesc.exe'
if (!(Test-Path -LiteralPath $compiler)) { throw 'Run npm ci in mobile first.' }
$bin = Join-Path $dest 'build/bin'
New-Item -ItemType Directory -Path $bin -Force | Out-Null
foreach ($name in @('hermesc.exe', 'hermesc')) {
    $copy = Join-Path $bin $name
    Copy-Item -LiteralPath $compiler -Destination $copy -Force
    if ((Get-FileHash -LiteralPath $compiler).Hash -ne (Get-FileHash -LiteralPath $copy).Hash) { throw 'Compiler SHA-256 mismatch.' }
}
# Same locked package, unchanged binary; the supported RN override avoids the
# reproducible file-output failure when executing from this Windows node_modules.
$inputFile = Join-Path $dest 'smoke.js'
$outputFile = Join-Path $dest 'smoke.hbc'
Set-Content -LiteralPath $inputFile -Value 'var ihrmsBuildCheck = 1;' -Encoding ASCII
& (Join-Path $bin 'hermesc.exe') -emit-binary -out $outputFile $inputFile -O
if ($LASTEXITCODE -ne 0 -or !(Test-Path -LiteralPath $outputFile)) { throw 'Hermes file-output smoke check failed.' }
$env:REACT_NATIVE_OVERRIDE_HERMES_DIR = $dest.Replace('\', '/')
Write-Output ('Verified portable Hermes SHA-256: ' + (Get-FileHash -LiteralPath $compiler -Algorithm SHA256).Hash.ToLowerInvariant())
