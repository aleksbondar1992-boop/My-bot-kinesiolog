<#
    Uninstall-Autostart.ps1

    Removes the scheduled task and stops anything still running.
#>
[CmdletBinding()]
param(
    [string]$TaskName = 'ClaudeRemoteControl'
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ''
Write-Host '=== Removing autostart ===' -ForegroundColor Cyan
Write-Host ''

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "[-] Scheduled task '$TaskName' removed." -ForegroundColor Green
} else {
    Write-Host "[=] No scheduled task named '$TaskName'." -ForegroundColor DarkGray
}

& (Join-Path $root 'Stop-RemoteControl.ps1')
