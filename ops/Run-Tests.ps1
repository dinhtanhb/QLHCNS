$repoRoot = Split-Path -Parent $PSScriptRoot
$sourceDirectory = Join-Path $repoRoot 'src'
$managePy = Join-Path $sourceDirectory 'manage.py'
$venvPython = Join-Path $repoRoot 'venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $managePy -PathType Leaf)) {
    [Console]::Error.WriteLine("Cannot find Django manage.py at $managePy")
    exit 2
}

if (Test-Path -LiteralPath $venvPython -PathType Leaf) {
    $pythonCommand = $venvPython
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCommand = 'python'
} else {
    [Console]::Error.WriteLine('Python was not found. Create the project venv or install Python on PATH.')
    exit 2
}

$scriptExitCode = 0
Push-Location -LiteralPath $sourceDirectory
try {
    $testOutput = & $pythonCommand manage.py test --verbosity 1 2>&1
    $pythonExitCode = $LASTEXITCODE
    foreach ($line in $testOutput) {
        if ($line -is [System.Management.Automation.ErrorRecord]) {
            Write-Output $line.Exception.Message
        } else {
            Write-Output $line
        }
    }

    $foundLine = $testOutput |
        ForEach-Object { $_.ToString() } |
        Where-Object { $_ -match 'Found\s+\d+\s+test\(s\)\.' } |
        Select-Object -First 1

    if (-not $foundLine) {
        [Console]::Error.WriteLine('Django did not report a discovered-test count; treating this run as failed.')
        $scriptExitCode = if ($pythonExitCode -ne 0) { $pythonExitCode } else { 2 }
    } else {
        $countMatch = [regex]::Match($foundLine, 'Found\s+(\d+)\s+test\(s\)\.')
        $discoveredTestTotal = [int]$countMatch.Groups[1].Value
        Write-Output "Discovered tests: $discoveredTestTotal"

        if ($discoveredTestTotal -eq 0) {
            [Console]::Error.WriteLine('No tests were discovered. Run from the project wrapper; do not treat zero tests as success.')
            $scriptExitCode = 2
        } else {
            $scriptExitCode = $pythonExitCode
        }
    }
} finally {
    Pop-Location
}

exit $scriptExitCode
