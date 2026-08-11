<#
    Start-RemoteControl.ps1

    Reads rc-projects.txt and starts one supervised "claude remote-control"
    server per project, so every project shows up as its own session in the
    Claude app on your phone (Code tab).

    Already-running projects are left alone, so it is safe to run this twice.
#>
[CmdletBinding()]
param(
    [string]$ConfigFile,
    [string]$LogDir,
    [ValidateSet('Minimized', 'Hidden')][string]$WindowStyle = 'Minimized'
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ConfigFile) { $ConfigFile = Join-Path $root 'rc-projects.txt' }
if (-not $LogDir) { $LogDir = Join-Path $root 'logs' }
$runDir = Join-Path $root 'run'
$watchScript = Join-Path $root 'Watch-Project.ps1'
$commonScript = Join-Path $root '_Common.ps1'

foreach ($dir in @($LogDir, $runDir)) {
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
}

if (-not (Test-Path -LiteralPath $commonScript)) {
    Write-Host "[X] _Common.ps1 is missing next to this script." -ForegroundColor Red
    exit 1
}
. $commonScript

Write-Host ''
Write-Host '=== Claude Remote Control ===' -ForegroundColor Cyan
Write-Host ''

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
    Write-Host '[X] Claude Code is not installed, or not on PATH.' -ForegroundColor Red
    Write-Host '    Install it, then open a NEW terminal window and try again:' -ForegroundColor Red
    Write-Host '    npm install -g @anthropic-ai/claude-code' -ForegroundColor Yellow
    Write-Host ''
    exit 1
}

if (-not (Test-Path -LiteralPath $ConfigFile)) {
    Write-Host "[X] Config file not found: $ConfigFile" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath $watchScript)) {
    Write-Host "[X] Watch-Project.ps1 is missing next to this script." -ForegroundColor Red
    exit 1
}

$started = 0
$skipped = 0
$failed = 0
$lineNumber = 0

foreach ($line in (Get-Content -LiteralPath $ConfigFile -Encoding UTF8)) {
    $lineNumber++
    $trimmed = $line.Trim()
    if (-not $trimmed -or $trimmed.StartsWith('#')) { continue }

    $parts = $trimmed -split '\|', 2
    if ($parts.Count -ne 2) {
        Write-Host "[!] Line ${lineNumber}: expected 'Name|C:\path', got: $trimmed" -ForegroundColor Yellow
        $failed++
        continue
    }

    $name = $parts[0].Trim() -replace '"', ''
    $projectPath = $parts[1].Trim().TrimEnd('\') -replace '"', ''

    if (-not $name -or -not $projectPath) {
        Write-Host "[!] Line ${lineNumber}: empty name or path" -ForegroundColor Yellow
        $failed++
        continue
    }

    if (-not (Test-Path -LiteralPath $projectPath -PathType Container)) {
        Write-Host "[!] $name -- folder not found: $projectPath" -ForegroundColor Yellow
        $failed++
        continue
    }

    $pidFile = Join-Path $runDir ("{0}.pid" -f (Get-SafeName $name))

    $existing = Get-WatchdogInfo $pidFile
    if ($existing -and $existing.ProjectPath -eq $projectPath) {
        Write-Host "[=] $name -- already running" -ForegroundColor DarkGray
        $skipped++
        continue
    }

    # Same name, different folder: the path was edited in rc-projects.txt while
    # the old watchdog was still up. Retire it before starting the new one,
    # otherwise both keep publishing a session under this name.
    if ($existing) {
        Write-Host "[~] $name -- folder changed, restarting" -ForegroundColor Yellow
        Stop-ProcessTree $existing.ProcessId
    }

    # Build the argument line by hand: -ArgumentList with an array does not
    # quote items, and session names like "Персональный астролог" have spaces.
    # -Tag is what makes this process recognisable on the next run.
    $argLine = '-NoProfile -ExecutionPolicy Bypass -File "{0}" -Name "{1}" -Path "{2}" -LogDir "{3}" -Tag {4}' -f `
        $watchScript, $name, $projectPath, $LogDir, (Get-ProjectTag $projectPath)

    try {
        $proc = Start-Process -FilePath 'powershell.exe' -ArgumentList $argLine `
            -WindowStyle $WindowStyle -PassThru
        Write-PidFile $pidFile $proc.Id $projectPath
        Write-Host "[+] $name -- started ($projectPath)" -ForegroundColor Green
        $started++
    } catch {
        Write-Host "[X] $name -- failed to start: $($_.Exception.Message)" -ForegroundColor Red
        $failed++
    }
}

Write-Host ''
Write-Host "Started: $started   Already running: $skipped   Problems: $failed"
Write-Host "Logs: $LogDir"
Write-Host ''

if ($started -gt 0 -or $skipped -gt 0) {
    Write-Host 'Open the Claude app on your phone -> Code tab.' -ForegroundColor Cyan
    Write-Host 'Sessions with a computer icon and a green dot are this machine.' -ForegroundColor Cyan
    Write-Host 'First connection can take up to a minute.' -ForegroundColor DarkGray
} else {
    Write-Host 'Nothing was started. Check rc-projects.txt.' -ForegroundColor Yellow
}
Write-Host ''
