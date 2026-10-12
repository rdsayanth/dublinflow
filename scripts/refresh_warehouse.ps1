# Refresh the DublinFlow warehouse: load new raw data, rebuild dbt models, run tests.
#
# Steps:
#   1. Load new live GBFS snapshots from Azure Blob into PostgreSQL (skips files already loaded).
#   2. Reload Met Eireann hourly weather, at most once every 30 days (or always with -Weather).
#   3. dbt build: rebuild all models and run all tests. Stops here if anything fails.
#   4. dbt source freshness: warns if the live data is old (does not fail the run).
#
# Every run writes a log to logs\refresh\. The exit code is 0 on success and 1 on failure,
# so Windows Task Scheduler shows failed runs.
#
# Usage (from anywhere):
#   powershell -NoProfile -ExecutionPolicy Bypass -File C:\dev\dublinflow\scripts\refresh_warehouse.ps1
#   ... -Weather      also reload the weather now

param(
    [switch]$Weather
)

$ErrorActionPreference = 'Stop'
$Repo = Split-Path -Parent $PSScriptRoot
Set-Location $Repo

$Python = Join-Path $Repo '.venv\Scripts\python.exe'
$Dotenv = Join-Path $Repo '.venv\Scripts\dotenv.exe'
$Dbt = Join-Path $Repo '.venv\Scripts\dbt.exe'
$LogDir = Join-Path $Repo 'logs\refresh'
$WeatherStamp = Join-Path $LogDir 'last_weather_load.txt'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Log = Join-Path $LogDir ("refresh_{0}.log" -f (Get-Date -Format 'yyyyMMdd_HHmmss'))

function Write-Log([string]$Message) {
    $line = "{0}  {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    Write-Host $line
    Add-Content -Path $Log -Value $line -Encoding UTF8
}

# Run a program, copy its output (stdout and stderr) to the log, and stop the run if it fails.
function Invoke-Step([string]$Name, [string]$Exe, [string[]]$Arguments, [switch]$WarnOnly) {
    Write-Log "START $Name"
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'   # native programs write normal logs to stderr
    & $Exe @Arguments 2>&1 | ForEach-Object {
        $text = "$_"
        Write-Host $text
        Add-Content -Path $Log -Value $text -Encoding UTF8
    }
    $code = $LASTEXITCODE
    $ErrorActionPreference = $previous
    if ($code -ne 0) {
        if ($WarnOnly) {
            Write-Log "WARN  $Name exited with code $code (not stopping)"
            return
        }
        Write-Log "FAIL  $Name exited with code $code"
        throw "$Name failed"
    }
    Write-Log "OK    $Name"
}

$started = Get-Date
try {
    Write-Log "DublinFlow warehouse refresh started in $Repo"

    Invoke-Step 'Load live snapshots' $Python @('ingestion\load_raw_to_postgres.py')

    $weatherDue = $Weather -or -not (Test-Path $WeatherStamp) -or
        ((Get-Item $WeatherStamp).LastWriteTime -lt (Get-Date).AddDays(-30))
    if ($weatherDue) {
        Invoke-Step 'Load weather' $Python @('ingestion\load_weather_to_postgres.py')
        Set-Content -Path $WeatherStamp -Value (Get-Date -Format 's') -Encoding UTF8
    } else {
        Write-Log "SKIP  Load weather (last load $((Get-Item $WeatherStamp).LastWriteTime.ToString('yyyy-MM-dd')); runs every 30 days)"
    }

    Invoke-Step 'dbt build' $Dotenv @('run', '--', $Dbt, 'build')
    Invoke-Step 'dbt source freshness' $Dotenv @('run', '--', $Dbt, 'source', 'freshness') -WarnOnly

    Write-Log ("DONE  in {0:n1} minutes. Next: open powerbi\DublinFlow.pbip and click Refresh." -f ((Get-Date) - $started).TotalMinutes)
    $exitCode = 0
} catch {
    Write-Log "STOPPED: $($_.Exception.Message). See $Log"
    $exitCode = 1
}

# Keep the 30 most recent logs.
Get-ChildItem $LogDir -Filter 'refresh_*.log' | Sort-Object LastWriteTime -Descending |
    Select-Object -Skip 30 | Remove-Item -Force

exit $exitCode
