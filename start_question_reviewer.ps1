[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$frontendRoot = Join-Path $projectRoot 'frontend'
$logRoot = Join-Path $projectRoot '.tmp\question-reviewer'
$port = 5174

if (-not (Test-Path -LiteralPath (Join-Path $frontendRoot 'node_modules'))) {
    throw 'Frontend dependencies not found. Run npm install in frontend first.'
}

New-Item -ItemType Directory -Force -Path $logRoot | Out-Null

# Start-Process treats environment variable names case-insensitively on Windows.
# Normalize duplicate PATH/Path entries that some shells inject.
$processVariables = [Environment]::GetEnvironmentVariables('Process')
$processPath = [string]$processVariables['Path']
if (-not $processPath) {
    $processPath = [string]$processVariables['PATH']
}
[Environment]::SetEnvironmentVariable('PATH', $null, 'Process')
[Environment]::SetEnvironmentVariable('Path', $processPath, 'Process')

try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$port/reviewer.html" -TimeoutSec 2
    if ($response.StatusCode -eq 200) {
        Write-Host "Question reviewer is already running: http://127.0.0.1:$port/reviewer.html" -ForegroundColor Green
        exit 0
    }
}
catch {
    # Start a new reviewer process below.
}

$npm = (Get-Command npm.cmd -ErrorAction Stop).Source
$outLog = Join-Path $logRoot 'reviewer.out.log'
$errorLog = Join-Path $logRoot 'reviewer.error.log'
$command = "`"$npm`" run dev:reviewer"
$process = Start-Process -FilePath 'cmd.exe' `
    -ArgumentList @('/c', $command) `
    -WorkingDirectory $frontendRoot `
    -WindowStyle Hidden `
    -RedirectStandardOutput $outLog `
    -RedirectStandardError $errorLog `
    -PassThru

Set-Content -LiteralPath (Join-Path $logRoot 'reviewer.pid') -Value $process.Id

for ($attempt = 0; $attempt -lt 30; $attempt++) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$port/reviewer.html" -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            Write-Host "Question reviewer: http://127.0.0.1:$port/reviewer.html" -ForegroundColor Green
            Write-Host "Logs: $logRoot"
            exit 0
        }
    }
    catch {
        Start-Sleep -Milliseconds 500
    }
}

throw "Question reviewer failed to start. See: $errorLog"
