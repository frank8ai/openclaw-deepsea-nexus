param(
    [switch]$Check,
    [switch]$Json
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = if ($env:NEXUS_PYTHON_PATH) { $env:NEXUS_PYTHON_PATH } else { "python" }

$passCount = 0
$warnCount = 0
$failCount = 0
$results = New-Object System.Collections.Generic.List[object]

function Add-Result {
    param(
        [string]$Level,
        [string]$Name,
        [string]$Message
    )

    switch ($Level) {
        "PASS" { $script:passCount++ }
        "WARN" { $script:warnCount++ }
        "FAIL" { $script:failCount++ }
    }

    $script:results.Add([pscustomobject]@{
        level = $Level
        name = $Name
        message = $Message
    })
}

function Invoke-JsonCommand {
    param(
        [string]$Name,
        [string[]]$CommandArgs
    )

    try {
        $output = & $python @CommandArgs 2>&1
        if ($LASTEXITCODE -ne 0) {
            Add-Result "FAIL" $Name (($output | Out-String).Trim())
            return $null
        }
        $text = ($output | Out-String).Trim()
        $lines = $text -split "`r?`n"
        $startIndex = -1
        for ($index = 0; $index -lt $lines.Length; $index++) {
            $trimmed = $lines[$index].Trim()
            if ($trimmed.StartsWith("{") -or $trimmed.StartsWith("[")) {
                $startIndex = $index
                break
            }
        }
        if ($startIndex -ge 0) {
            $jsonText = ($lines[$startIndex..($lines.Length - 1)] -join "`n").Trim()
        } else {
            $jsonText = $text
        }
        return $jsonText | ConvertFrom-Json
    } catch {
        Add-Result "FAIL" $Name $_.Exception.Message
        return $null
    }
}

function Invoke-TextCommand {
    param(
        [string]$Name,
        [string[]]$CommandArgs
    )

    try {
        $output = & $python @CommandArgs 2>&1
        if ($LASTEXITCODE -ne 0) {
            Add-Result "FAIL" $Name (($output | Out-String).Trim())
            return $null
        }
        return ($output | Out-String).Trim()
    } catch {
        Add-Result "FAIL" $Name $_.Exception.Message
        return $null
    }
}

if (Get-Command $python -ErrorAction SilentlyContinue) {
    Add-Result "PASS" "python" "runtime: $python"
} else {
    Add-Result "FAIL" "python" "runtime not found: $python"
}

$health = Invoke-JsonCommand -Name "health" -CommandArgs @("-m", "deepsea_nexus", "health", "--json")
if ($health) {
    if ($health.available -and $health.initialized) {
        Add-Result "PASS" "health" "package=$($health.package_version) plugins active"
    } else {
        Add-Result "FAIL" "health" "runtime available=$($health.available) initialized=$($health.initialized)"
    }
}

$paths = Invoke-JsonCommand -Name "paths" -CommandArgs @("-m", "deepsea_nexus", "paths", "--json")
if ($paths) {
    $memoryRoot = [string]$paths.memory_v5_root
    if (Test-Path $memoryRoot) {
        Add-Result "PASS" "paths" "memory_v5_root exists: $memoryRoot"
    } else {
        Add-Result "WARN" "paths" "memory_v5_root missing: $memoryRoot"
    }
}

$smoke = Invoke-JsonCommand -Name "memory_v5_smoke" -CommandArgs @("scripts/memory_v5_smoke.py")
if ($smoke) {
    if ($smoke.ok) {
        Add-Result "PASS" "memory_v5_smoke" "hits=$($smoke.hits)"
    } else {
        Add-Result "FAIL" "memory_v5_smoke" "smoke returned ok=false"
    }
}

$recall = Invoke-TextCommand -Name "recall" -CommandArgs @("-m", "deepsea_nexus", "recall", "framework decision", "-n", "3")
if ($recall) {
    Add-Result "PASS" "recall" "recall returned output"
}

$maintenance = Invoke-TextCommand -Name "maintenance" -CommandArgs @("scripts/memory_v5_maintenance.py", "--dry-run")
if ($maintenance) {
    Add-Result "PASS" "maintenance" "dry-run completed"
}

$summary = [pscustomobject]@{
    ok = ($failCount -eq 0)
    pass = $passCount
    warn = $warnCount
    fail = $failCount
    mode = if ($Check) { "check" } else { "check" }
    results = $results
}

if ($Json) {
    $summary | ConvertTo-Json -Depth 6
} else {
    foreach ($row in $results) {
        Write-Output ("[{0}] {1}: {2}" -f $row.level, $row.name, $row.message)
    }
    Write-Output ("Summary: pass={0} warn={1} fail={2}" -f $passCount, $warnCount, $failCount)
}

if ($failCount -gt 0) {
    exit 1
}

exit 0
