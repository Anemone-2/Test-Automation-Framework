$ErrorActionPreference = 'Continue'
$projectRoot = Split-Path -Parent $PSScriptRoot
$composeFile = Join-Path $projectRoot 'infra\docker-compose.yml'
$pidFile = Join-Path $projectRoot 'report\ci-runtime\mock-server.pid'
$environmentMarker = Join-Path $projectRoot 'report\ci-runtime\jenkins-environment.started'

if (Test-Path -LiteralPath $pidFile) {
    $savedPid = (Get-Content -LiteralPath $pidFile -Raw).Trim()
    if ($savedPid -and $savedPid -ne 'EXTERNAL') {
        $process = Get-Process -Id ([int]$savedPid) -ErrorAction SilentlyContinue
        if ($process -and $process.ProcessName -match '^python') {
            Stop-Process -Id $process.Id -Force
            Write-Host "Stopped Mock service. PID=$savedPid"
        }
    } else {
        Write-Host 'The Mock service was started outside Jenkins and was left running.'
    }
    Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
}

if (Test-Path -LiteralPath $environmentMarker) {
    $composeOutput = & docker compose -f $composeFile down 2>&1
    $composeOutput | ForEach-Object { Write-Host $_ }
    if ($LASTEXITCODE -ne 0) {
        Write-Warning 'docker compose down returned a non-zero exit code'
    }
    Remove-Item -LiteralPath $environmentMarker -Force -ErrorAction SilentlyContinue
} else {
    Write-Host 'The Jenkins test environment was not started; Docker resources were left unchanged.'
}
