<#
    Watch-Project.ps1

    Keeps one "claude remote-control" server alive for a single project folder.
    Started by Start-RemoteControl.ps1 - you normally do not run this by hand.

    If the server exits (network drop longer than ~10 minutes, machine wakes
    from sleep, crash), this script starts it again.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Name,
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][string]$LogDir,

    # Identity token from Get-ProjectTag. Never read here - it exists so this
    # process can be recognised by its command line on the next start.
    [string]$Tag
)

# Session names may contain Cyrillic - keep every stream on UTF-8.
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
try { $Host.UI.RawUI.WindowTitle = "Claude RC: $Name" } catch { }

# Shared with Start-RemoteControl so the log file and the pid file for a
# project always end up under the same sanitised name.
. (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) '_Common.ps1')

$logFile = Join-Path $LogDir ("{0}.log" -f (Get-SafeName $Name))

function Write-Log([string]$message) {
    $line = "[{0}] {1}" -f (Get-Date).ToString('yyyy-MM-dd HH:mm:ss'), $message
    Add-Content -LiteralPath $logFile -Value $line -Encoding UTF8
    Write-Host $line
}

Write-Log "=== watchdog started (name: $Name, folder: $Path) ==="

if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
    Write-Log "FATAL: folder does not exist: $Path"
    Write-Log "Fix the path in rc-projects.txt, then run start.bat again."
    Start-Sleep -Seconds 30
    exit 1
}

# Backoff grows only while the server keeps dying instantly, which means a
# config problem rather than a blip. A session that ran a while resets it.
$delay = 5
$maxDelay = 300

while ($true) {
    Write-Log "launching: claude remote-control --name `"$Name`""
    $startedAt = Get-Date
    $exitCode = -1

    try {
        Push-Location -LiteralPath $Path
        & claude remote-control --name $Name *>> $logFile
        $exitCode = $LASTEXITCODE
    } catch {
        Write-Log "launch failed: $($_.Exception.Message)"
    } finally {
        Pop-Location -ErrorAction SilentlyContinue
    }

    $ranForSeconds = [int]((Get-Date) - $startedAt).TotalSeconds
    Write-Log "server exited (code $exitCode) after $ranForSeconds s"

    if ($ranForSeconds -ge 60) { $delay = 5 } else { $delay = [Math]::Min($delay * 2, $maxDelay) }

    Write-Log "restarting in $delay s"
    Start-Sleep -Seconds $delay
}
