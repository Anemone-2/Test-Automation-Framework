param(
    [Parameter(Mandatory = $true)]
    [string]$EnvFile
)

$ErrorActionPreference = 'Continue'
$projectRoot = Split-Path -Parent $PSScriptRoot
$composeFile = Join-Path $projectRoot 'infra\snipeit\docker-compose.yml'
$environmentMarker = Join-Path $projectRoot 'report\ci-runtime\snipeit-environment.state'

if (-not (Test-Path -LiteralPath $environmentMarker -PathType Leaf)) {
    Write-Host 'No Snipe-IT CI environment marker was found; containers were left unchanged.'
    exit 0
}

$environmentState = (Get-Content -LiteralPath $environmentMarker -Raw).Trim()
if ($environmentState -eq 'REUSED') {
    Write-Host 'Snipe-IT was already running before this build and was left running.'
    Remove-Item -LiteralPath $environmentMarker -Force -ErrorAction SilentlyContinue
    exit 0
}

if (-not (Test-Path -LiteralPath $EnvFile -PathType Leaf)) {
    Write-Warning "Snipe-IT environment file not found during cleanup: $EnvFile"
    exit 0
}

$resolvedEnvFile = (Resolve-Path -LiteralPath $EnvFile).Path
$env:SNIPEIT_RUNTIME_ENV_FILE = $resolvedEnvFile
$composeOutput = & docker compose --env-file $resolvedEnvFile -f $composeFile down 2>&1
$composeOutput | ForEach-Object { Write-Host $_ }
if ($LASTEXITCODE -ne 0) {
    Write-Warning 'Stopping the Snipe-IT Docker Compose environment returned a non-zero exit code.'
    exit $LASTEXITCODE
}

Remove-Item -LiteralPath $environmentMarker -Force -ErrorAction SilentlyContinue
Write-Host 'Stopped the Snipe-IT environment started by this build. Persistent volumes were preserved.'
