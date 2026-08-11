<#
    Stop-RemoteControl.ps1

    Stops every watchdog started by Start-RemoteControl.ps1, together with the
    "claude remote-control" server each one is supervising.

    Autostart stays registered - use Uninstall-Autostart.ps1 to remove that.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$runDir = Join-Path $root 'run'
$commonScript = Join-Path $root '_Common.ps1'

if (-not (Test-Path -LiteralPath $commonScript)) {
    Write-Host "[X] _Common.ps1 is missing next to this script." -ForegroundColor Red
    exit 1
}
. $commonScript

Write-Host ''
Write-Host '=== Stopping Claude Remote Control ===' -ForegroundColor Cyan
Write-Host ''

if (-not (Test-Path -LiteralPath $runDir)) {
    Write-Host 'Nothing is running.' -ForegroundColor DarkGray
    Write-Host ''
    exit 0
}

$stopped = 0
$stale = 0

foreach ($pidFile in (Get-ChildItem -LiteralPath $runDir -Filter '*.pid' -ErrorAction SilentlyContinue)) {
    $name = [System.IO.Path]::GetFileNameWithoutExtension($pidFile.Name)
    $info = Get-WatchdogInfo $pidFile.FullName

    if ($info) {
        Stop-ProcessTree $info.ProcessId
        Write-Host "[-] $name -- stopped" -ForegroundColor Green
        $stopped++
    } else {
        # Either already gone, or the recorded id now belongs to something else.
        # Get-WatchdogInfo refuses to confirm those, so nothing gets killed.
        Write-Host "[=] $name -- was not running" -ForegroundColor DarkGray
        $stale++
    }

    Remove-Item -LiteralPath $pidFile.FullName -Force -ErrorAction SilentlyContinue
}

Write-Host ''
Write-Host "Stopped: $stopped   Already gone: $stale"
Write-Host ''
