param([string]$Project = (Get-Location).Path, [string]$Python)
# Discovery only: does not install software or change PATH, registry or policy.
$ErrorActionPreference = 'Stop'
$candidates = [System.Collections.Generic.List[string]]::new()
function Add-Candidate([string]$Value) {
    if ($Value -and -not $candidates.Contains($Value)) { $candidates.Add($Value) }
}
if ($Python) { Add-Candidate $Python }
elseif ($env:INDUSTRIAL_LAYOUT_PYTHON) { Add-Candidate $env:INDUSTRIAL_LAYOUT_PYTHON }
else {
    Add-Candidate (Join-Path $Project '.venv/Scripts/python.exe')
    Add-Candidate (Join-Path $Project '.venv/bin/python')
    foreach ($name in @('python', 'python3')) {
        foreach ($command in @(Get-Command $name -CommandType Application -ErrorAction SilentlyContinue)) {
            Add-Candidate $command.Source
        }
    }
    foreach ($base in @('HKCU:\Software\Python\PythonCore', 'HKLM:\Software\Python\PythonCore', 'HKLM:\Software\WOW6432Node\Python\PythonCore')) {
        foreach ($version in @(Get-ChildItem -LiteralPath $base -ErrorAction SilentlyContinue)) {
            $key = Get-Item -LiteralPath ($version.PSPath + '\InstallPath') -ErrorAction SilentlyContinue
            if ($key) {
                Add-Candidate $key.GetValue('ExecutablePath')
                $directory = $key.GetValue('')
                if ($directory) { Add-Candidate (Join-Path $directory 'python.exe') }
            }
        }
    }
    if ($env:LOCALAPPDATA) {
        $base = Join-Path $env:LOCALAPPDATA 'Programs/Python'
        foreach ($directory in @(Get-ChildItem -LiteralPath $base -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending)) {
            Add-Candidate (Join-Path $directory.FullName 'python.exe')
        }
    }
}
$failures = @()
$probe = Join-Path $PSScriptRoot 'runtime_probe.py'
foreach ($candidate in $candidates) {
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { continue }
    # Do not launch Windows Store execution aliases as interpreters.
    if ($candidate -match '[\\/]Microsoft[\\/]WindowsApps[\\/]') { continue }
    try {
        $raw = & $candidate -B $probe 2>&1
        if ($LASTEXITCODE -ne 0) { throw "Probe exit $LASTEXITCODE : $raw" }
        $result = ($raw -join "`n") | ConvertFrom-Json
        if ($result.version[0] -ne 3 -or $result.version[1] -lt 11) { throw 'Python 3.11+ required' }
        if (-not $result.ready) { throw $result.reason }
        [ordered]@{ ready=$true; executable=$result.executable; version=$result.version; dependencies=$result.dependencies; rejected=$failures } | ConvertTo-Json -Depth 5
        exit 0
    } catch { $failures += @{ candidate=$candidate; reason=$_.Exception.Message } }
}
[ordered]@{ ready=$false; executable=$null; rejected=$failures; reason='No usable Python 3.11+ with numpy and Pillow found. Provide -Python with an existing interpreter or provision an isolated environment; do not bypass the workflows.' } | ConvertTo-Json -Depth 5
exit 1
