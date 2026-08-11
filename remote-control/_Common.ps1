<#
    _Common.ps1

    Helpers shared by Start-RemoteControl.ps1, Stop-RemoteControl.ps1 and
    Watch-Project.ps1. Dot-sourced by all three - not meant to be run on its own.

    Pid file format:  <process id>|<project folder>
#>

function Get-SafeName([string]$Name) {
    return ($Name -replace '[\\/:*?"<>|]', '_').Trim()
}

<#
    A short, stable token derived from the project folder, passed to the
    watchdog as -Tag and used to recognise it later in a process command line.

    Matching on the folder itself does not work: Windows reports the raw command
    line with quotes intact while other platforms report argv with quotes
    stripped, and one folder can be a prefix of another ("...\bots" inside
    "...\bots2"). A fixed-length token with no spaces has neither problem.
#>
function Get-ProjectTag([string]$ProjectPath) {
    $normalized = $ProjectPath.TrimEnd('\', '/').ToLowerInvariant()
    $sha = [System.Security.Cryptography.SHA1]::Create()
    try {
        $bytes = $sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($normalized))
    } finally {
        $sha.Dispose()
    }
    return 'CCRC-' + ((($bytes | ForEach-Object { $_.ToString('x2') }) -join '').Substring(0, 12))
}

function Get-ProcessCommandLine([int]$ProcessId) {
    try {
        $cim = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction Stop
        if ($cim -and $cim.CommandLine) { return [string]$cim.CommandLine }
    } catch {
        # Not Windows, or WMI unavailable - fall through.
    }

    $cmdlineFile = "/proc/$ProcessId/cmdline"
    if (Test-Path -LiteralPath $cmdlineFile) {
        try {
            $raw = [System.IO.File]::ReadAllBytes($cmdlineFile)
            return ([System.Text.Encoding]::UTF8.GetString($raw) -replace "`0", ' ').Trim()
        } catch {
            return $null
        }
    }

    return $null
}

function Get-ChildProcessId([int]$ProcessId) {
    try {
        $cim = @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$ProcessId" -ErrorAction Stop)
        return @($cim | ForEach-Object { [int]$_.ProcessId })
    } catch {
        # Not Windows - read parent ids out of /proc instead.
    }

    $children = @()
    if (Test-Path -LiteralPath '/proc') {
        foreach ($dir in (Get-ChildItem -LiteralPath '/proc' -Directory -ErrorAction SilentlyContinue)) {
            if ($dir.Name -notmatch '^\d+$') { continue }
            $statusFile = "/proc/$($dir.Name)/status"
            if (-not (Test-Path -LiteralPath $statusFile)) { continue }
            $ppidLine = Select-String -LiteralPath $statusFile -Pattern '^PPid:\s+(\d+)' -ErrorAction SilentlyContinue |
                Select-Object -First 1
            if ($ppidLine -and [int]$ppidLine.Matches[0].Groups[1].Value -eq $ProcessId) {
                $children += [int]$dir.Name
            }
        }
    }
    return $children
}

function Write-PidFile([string]$PidFile, [int]$ProcessId, [string]$ProjectPath) {
    Set-Content -LiteralPath $PidFile -Value ("{0}|{1}" -f $ProcessId, $ProjectPath) -Encoding UTF8
}

<#
    Reads $PidFile and returns @{ ProcessId; ProjectPath } when that process is
    still the watchdog it claims to be, or $null when the entry is dead.

    The identity check matters: process ids get recycled, and a stale pid file
    left over from a previous boot can easily point at an unrelated process.
    Acting on that id would either skip a project that is actually down, or -
    in Stop - kill something innocent.

    Start times are deliberately NOT used for this. Process.StartTime drifts by
    a few milliseconds between reads on some platforms, so comparing it exactly
    reports every live watchdog as dead and spawns duplicate sessions on every
    run.
#>
function Get-WatchdogInfo([string]$PidFile) {
    if (-not (Test-Path -LiteralPath $PidFile)) { return $null }

    $raw = Get-Content -LiteralPath $PidFile -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
    if (-not $raw) { return $null }

    $parts = $raw.Trim() -split '\|', 2
    if ($parts.Count -ne 2) { return $null }

    $processId = 0
    if (-not [int]::TryParse($parts[0], [ref]$processId)) { return $null }
    if ($processId -le 0) { return $null }

    $projectPath = $parts[1].Trim()
    if (-not $projectPath) { return $null }
    if (-not (Get-Process -Id $processId -ErrorAction SilentlyContinue)) { return $null }

    # Without a command line there is nothing to verify against, so treat the
    # entry as dead. Starting a second watchdog is recoverable; killing an
    # unrelated process tree is not.
    $cmdLine = Get-ProcessCommandLine $processId
    if (-not $cmdLine) { return $null }

    foreach ($needle in @('Watch-Project.ps1', (Get-ProjectTag $projectPath))) {
        $pattern = '*' + [System.Management.Automation.WildcardPattern]::Escape($needle) + '*'
        if ($cmdLine -notlike $pattern) { return $null }
    }

    return @{ ProcessId = $processId; ProjectPath = $projectPath }
}

# Killing the watchdog alone would orphan the claude server it launched,
# so walk the tree children-first.
function Stop-ProcessTree([int]$ProcessId) {
    foreach ($childId in (Get-ChildProcessId $ProcessId)) { Stop-ProcessTree $childId }
    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
}
