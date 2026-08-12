param(
    [Parameter(Mandatory = $true)]
    [string]$EnvFile
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$composeFile = Join-Path $projectRoot 'infra\snipeit\docker-compose.yml'
$runtimeDir = Join-Path $projectRoot 'report\ci-runtime'
$environmentMarker = Join-Path $runtimeDir 'snipeit-environment.state'

function Get-DotEnvValue {
    param(
        [string]$Path,
        [string]$Name
    )

    foreach ($rawLine in Get-Content -LiteralPath $Path) {
        $line = $rawLine.Trim()
        if (-not $line -or $line.StartsWith('#') -or -not $line.Contains('=')) {
            continue
        }
        $parts = $line.Split('=', 2)
        if ($parts[0].Trim() -eq $Name) {
            return $parts[1].Trim().Trim('"').Trim("'")
        }
    }
    return $null
}

if (-not (Test-Path -LiteralPath $EnvFile -PathType Leaf)) {
    throw "Snipe-IT environment file not found: $EnvFile"
}
if (-not (Test-Path -LiteralPath $composeFile -PathType Leaf)) {
    throw "Snipe-IT compose file not found: $composeFile"
}

$resolvedEnvFile = (Resolve-Path -LiteralPath $EnvFile).Path
$env:SNIPEIT_RUNTIME_ENV_FILE = $resolvedEnvFile
$baseUrl = Get-DotEnvValue -Path $resolvedEnvFile -Name 'SNIPEIT_BASE_URL'
if (-not $baseUrl) {
    $baseUrl = Get-DotEnvValue -Path $resolvedEnvFile -Name 'APP_URL'
}
if (-not $baseUrl) {
    $baseUrl = 'http://localhost:8090'
}
$baseUrl = $baseUrl.TrimEnd('/')

New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null

& docker version --format '{{.Server.Version}}' | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw 'Docker Engine is not available.'
}

$allServicesWereRunning = $true
foreach ($service in @('app', 'db')) {
    $containerId = (& docker compose --env-file $resolvedEnvFile -f $composeFile ps -q $service).Trim()
    if (-not $containerId) {
        $allServicesWereRunning = $false
        continue
    }
    $state = (& docker inspect --format '{{.State.Status}}' $containerId 2>$null).Trim()
    if ($state -ne 'running') {
        $allServicesWereRunning = $false
    }
}

if ($allServicesWereRunning) {
    'REUSED' | Set-Content -LiteralPath $environmentMarker -Encoding ASCII
    Write-Host 'Reusing the running Snipe-IT and MySQL containers.'
} else {
    & docker compose --env-file $resolvedEnvFile -f $composeFile up -d
    if ($LASTEXITCODE -ne 0) {
        throw 'Starting the Snipe-IT Docker Compose environment failed.'
    }
    'STARTED' | Set-Content -LiteralPath $environmentMarker -Encoding ASCII
    Write-Host 'Snipe-IT Docker Compose environment started by this build.'
}

$dbContainerId = (& docker compose --env-file $resolvedEnvFile -f $composeFile ps -q db).Trim()
if (-not $dbContainerId) {
    throw 'MySQL container was not created.'
}

$databaseReady = $false
for ($attempt = 1; $attempt -le 60; $attempt++) {
    $health = (& docker inspect --format '{{.State.Health.Status}}' $dbContainerId 2>$null).Trim()
    if ($health -eq 'healthy') {
        $databaseReady = $true
        break
    }
    if ($health -eq 'unhealthy') {
        throw 'MySQL container became unhealthy.'
    }
    Start-Sleep -Seconds 2
}
if (-not $databaseReady) {
    throw 'Timed out waiting for MySQL to become healthy.'
}
Write-Host 'MySQL is healthy.'

$appContainerId = (& docker compose --env-file $resolvedEnvFile -f $composeFile ps -q app).Trim()
if (-not $appContainerId) {
    throw 'Snipe-IT container was not created.'
}

$applicationReady = $false
for ($attempt = 1; $attempt -le 90; $attempt++) {
    $state = (& docker inspect --format '{{.State.Status}}' $appContainerId 2>$null).Trim()
    if ($state -eq 'exited' -or $state -eq 'dead') {
        throw "Snipe-IT container stopped during startup. State: $state"
    }
    try {
        $response = Invoke-WebRequest -Uri $baseUrl -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) {
            $applicationReady = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}
if (-not $applicationReady) {
    throw "Timed out waiting for Snipe-IT: $baseUrl"
}

Write-Host "Snipe-IT is ready at $baseUrl"
