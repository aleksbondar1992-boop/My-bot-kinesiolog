<#
    Install-Autostart.ps1

    Registers a Scheduled Task that runs Start-RemoteControl.ps1 every time you
    log in, so switching the computer on is enough to make every project
    reachable from your phone.

    Runs as your own user, so no administrator rights are needed.
#>
[CmdletBinding()]
param(
    [string]$TaskName = 'ClaudeRemoteControl',
    [int]$DelaySeconds = 30,
    [switch]$PreventSleep
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$startScript = Join-Path $root 'Start-RemoteControl.ps1'

Write-Host ''
Write-Host '=== Installing autostart ===' -ForegroundColor Cyan
Write-Host ''

if (-not (Test-Path -LiteralPath $startScript)) {
    Write-Host "[X] Start-RemoteControl.ps1 not found next to this script." -ForegroundColor Red
    exit 1
}

if (-not (Get-Command Register-ScheduledTask -ErrorAction SilentlyContinue)) {
    Write-Host '[X] This Windows version has no ScheduledTasks PowerShell module.' -ForegroundColor Red
    Write-Host '    Put a shortcut to start.bat into the Startup folder instead:' -ForegroundColor Yellow
    Write-Host '    Win+R -> shell:startup -> Enter' -ForegroundColor Yellow
    exit 1
}

$user = "$env:USERDOMAIN\$env:USERNAME"

$action = New-ScheduledTaskAction -Execute 'powershell.exe' `
    -Argument ('-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}"' -f $startScript) `
    -WorkingDirectory $root

# The delay gives Wi-Fi time to associate; without it the first launch often
# starts before the network is up and burns a restart cycle.
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
$trigger.Delay = "PT${DelaySeconds}S"

$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited

# ExecutionTimeLimit 0 = never kill it: these servers are meant to run all day.
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew

try {
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
        -Principal $principal -Settings $settings -Force | Out-Null
    Write-Host "[+] Scheduled task '$TaskName' registered for $user" -ForegroundColor Green
    Write-Host "    It runs $DelaySeconds s after every logon." -ForegroundColor DarkGray
} catch {
    Write-Host "[X] Could not register the task: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

if ($PreventSleep) {
    Write-Host ''
    Write-Host 'Disabling automatic sleep (a sleeping machine is unreachable)...'
    try {
        & powercfg /change standby-timeout-ac 0
        & powercfg /change hibernate-timeout-ac 0
        Write-Host '[+] Sleep on AC power disabled.' -ForegroundColor Green
    } catch {
        Write-Host '[!] powercfg failed - set it by hand in Settings > System > Power.' -ForegroundColor Yellow
    }
}

Write-Host ''
Write-Host 'Done. Starting everything now so you can test it right away...' -ForegroundColor Cyan
Write-Host ''

& $startScript
