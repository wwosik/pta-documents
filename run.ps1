# Human-facing launcher. A reserved verb runs a built-in action; anything else is treated as
# the name of a tool under ./tools (tools/<name>/<name>.py). Run with no arguments to list both.
$ErrorActionPreference = 'Stop'

$repoRoot = $PSScriptRoot
$toolsDir = Join-Path $repoRoot 'tools'
$venv = Join-Path $repoRoot '.venv'
$py = if ($IsWindows -or $env:OS -eq 'Windows_NT') { Join-Path $venv 'Scripts/python.exe' } else { Join-Path $venv 'bin/python' }
$verbs = @('setup', 'test', 'lint', 'format', 'typecheck', 'build')

function Show-List {
    Write-Output 'Verbs:'
    $verbs | ForEach-Object { Write-Output "  $_" }
    Write-Output ''
    Write-Output 'Tools:'
    $tools = if (Test-Path $toolsDir) { Get-ChildItem $toolsDir -Directory | Sort-Object Name } else { @() }
    if ($tools.Count -gt 0) { $tools | ForEach-Object { Write-Output "  $($_.Name)" } } else { Write-Output '  (none yet)' }
    Write-Output ''
    Write-Output "Usage: $PSCommandPath <verb|tool> [args...]"
}

function Invoke-Setup {
    if (-not (Test-Path $py)) {
        $python = if (Get-Command python3 -ErrorAction SilentlyContinue) { 'python3' } else { 'python' }
        & $python -m venv $venv
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
    & $py -m pip install --quiet --upgrade pip
    & $py -m pip install --quiet -e "$repoRoot[dev,pdf,svg,diagrams]"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    # mermaid-cli for mermaid blocks (E06-S03), repo-local in a fixed version; only with Node.js.
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        Push-Location (Join-Path $repoRoot 'tools/mermaid')
        & npm ci --no-audit --no-fund --silent
        if ($LASTEXITCODE -ne 0) { Write-Warning 'npm ci in tools/mermaid failed; mermaid blocks stay code.' }
        Pop-Location
    } else {
        Write-Host 'Node.js not found: mermaid blocks stay code (see docs/verwendung.md, Mermaid).'
    }
}

function Confirm-Venv { if (-not (Test-Path $py)) { Invoke-Setup } }

if ($args.Count -eq 0) { Show-List; exit 0 }
$command = $args[0]
$rest = @($args | Select-Object -Skip 1)

Push-Location $repoRoot
try {
    switch ($command) {
        'setup' { Invoke-Setup }
        'test' { Confirm-Venv; & $py -m pytest @rest }
        'lint' { Confirm-Venv; & $py -m ruff check @rest }
        'format' { Confirm-Venv; & $py -m ruff check --fix --select I @rest; & $py -m ruff format @rest }
        'typecheck' { Confirm-Venv; & $py -m pyright @rest }
        'build' { Confirm-Venv; & $py -m pip wheel --quiet --no-deps --wheel-dir (Join-Path $repoRoot 'dist') $repoRoot }
        default {
            $entry = Join-Path $toolsDir "$command/$command.py"
            if (-not (Test-Path $entry)) {
                Write-Error "Unknown verb or tool '$command'. Run $PSCommandPath with no arguments to list both."
                exit 1
            }
            Confirm-Venv
            & $py $entry @rest
        }
    }
    exit $LASTEXITCODE
}
finally { Pop-Location }
