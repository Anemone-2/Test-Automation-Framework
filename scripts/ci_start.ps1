param(
    [Parameter(Mandatory = $true)]
    [string]$PythonExe
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$composeFile = Join-Path $projectRoot 'infra\docker-compose.yml'
$runtimeDir = Join-Path $projectRoot 'report\ci-runtime'
$pidFile = Join-Path $runtimeDir 'mock-server.pid'
$environmentMarker = Join-Path $runtimeDir 'jenkins-environment.started'
$mockErrorLog = Join-Path $runtimeDir 'mock-server.err.log'

New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null

if (-not (Test-Path -LiteralPath $PythonExe)) {
    throw "Python executable not found: $PythonExe"
}

Write-Host 'Starting MySQL, Redis, MongoDB and ClickHouse...'
& docker compose -f $composeFile up -d
if ($LASTEXITCODE -ne 0) {
    throw 'docker compose up failed'
}
'STARTED' | Set-Content -LiteralPath $environmentMarker

$services = @('mysql', 'redis', 'mongodb', 'clickhouse')
foreach ($service in $services) {
    $containerId = (& docker compose -f $composeFile ps -q $service).Trim()
    if (-not $containerId) {
        throw "Container was not created for service: $service"
    }

    $healthy = $false
    for ($attempt = 1; $attempt -le 60; $attempt++) {
        $status = (& docker inspect --format '{{.State.Health.Status}}' $containerId 2>$null).Trim()
        if ($status -eq 'healthy') {
            $healthy = $true
            break
        }
        if ($status -eq 'unhealthy') {
            throw "Container became unhealthy: $service"
        }
        Start-Sleep -Seconds 2
    }

    if (-not $healthy) {
        throw "Timed out waiting for healthy container: $service"
    }
    Write-Host "$service is healthy"
}

$mockUri = 'http://127.0.0.1:8787/index'
try {
    $existing = Invoke-RestMethod -Uri $mockUri -TimeoutSec 3
    if (-not $existing.data_stores_enabled) {
        throw 'Port 8787 is occupied by a Mock service without real data stores enabled. Stop it before running Jenkins.'
    }
    'EXTERNAL' | Set-Content -LiteralPath $pidFile
    Write-Host 'Reusing the existing data-store-enabled Mock service.'
    exit 0
} catch {
    if ($_.Exception.Message -like 'Port 8787 is occupied*') {
        throw
    }
}

$mockLauncher = Join-Path $projectRoot 'scripts\ci_mock_service.py'
$commandLine = '"{0}" "{1}"' -f $PythonExe, $mockLauncher
$created = Invoke-CimMethod `
    -ClassName Win32_Process `
    -MethodName Create `
    -Arguments @{ CommandLine = $commandLine }
if ($created.ReturnValue -ne 0 -or -not $created.ProcessId) {
    throw "Failed to create detached Mock service process. WMI return value: $($created.ReturnValue)"
}
$process = Get-Process -Id $created.ProcessId -ErrorAction Stop
$process.Id | Set-Content -LiteralPath $pidFile

$ready = $false
for ($attempt = 1; $attempt -le 30; $attempt++) {
    if ($process.HasExited) {
        throw "Mock service exited during startup. See $mockErrorLog"
    }
    try {
        $status = Invoke-RestMethod -Uri $mockUri -TimeoutSec 3
        if ($status.data_stores_enabled) {
            $ready = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}

if (-not $ready) {
    throw "Timed out waiting for Mock service. See $mockErrorLog"
}

Write-Host "Mock service is ready. PID=$($process.Id)"
