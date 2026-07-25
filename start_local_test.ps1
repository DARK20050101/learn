[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$alembic = Join-Path $projectRoot '.venv\Scripts\alembic.exe'
$frontendRoot = Join-Path $projectRoot 'frontend'
$postgresRoot = Join-Path $projectRoot '.tmp\postgresql-validation'
$postgresBin = Join-Path $postgresRoot 'runtime\pgsql\bin'
$postgresData = Join-Path $postgresRoot 'data'
$postgresLog = Join-Path $postgresRoot 'postgres.log'
$localLogRoot = Join-Path $projectRoot '.tmp\local-test'
$backendPort = 8000
$frontendPort = 5173
$postgresPort = 55432

function Assert-PathExists([string]$path, [string]$description) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "$description not found: $path"
    }
}

function Test-HttpEndpoint([string]$uri) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $uri -TimeoutSec 2
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
    }
    catch {
        return $false
    }
}

function Wait-HttpEndpoint([string]$uri, [int]$attempts = 30) {
    for ($attempt = 0; $attempt -lt $attempts; $attempt++) {
        if (Test-HttpEndpoint $uri) {
            return $true
        }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Get-LocalLanIPv4 {
    try {
        $configuration = Get-NetIPConfiguration -ErrorAction Stop |
            Where-Object { $_.IPv4DefaultGateway -and $_.NetAdapter.Status -eq 'Up' } |
            Select-Object -First 1
        $address = $configuration.IPv4Address |
            Where-Object { $_.IPAddress -and $_.IPAddress -notlike '169.254.*' } |
            Select-Object -First 1 -ExpandProperty IPAddress
        if ($address) {
            return $address
        }
    }
    catch {
        # Some restricted shells cannot query the NetTCPIP CIM provider.
    }

    $addresses = [System.Net.Dns]::GetHostAddresses([System.Net.Dns]::GetHostName()) |
        Where-Object {
            $_.AddressFamily -eq [System.Net.Sockets.AddressFamily]::InterNetwork -and
            $_.IPAddressToString -ne '127.0.0.1' -and
            $_.IPAddressToString -notlike '169.254.*'
        }
    $privateAddress = $addresses |
        Where-Object { $_.IPAddressToString -match '^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)' } |
        Select-Object -First 1
    if ($privateAddress) {
        return $privateAddress.IPAddressToString
    }
    return ($addresses | Select-Object -First 1).IPAddressToString
}

Assert-PathExists $python 'Python virtual environment'
Assert-PathExists $alembic 'Alembic'
Assert-PathExists (Join-Path $frontendRoot 'node_modules') 'Frontend dependencies; run npm install in frontend first'
Assert-PathExists (Join-Path $postgresBin 'pg_isready.exe') 'PostgreSQL runtime'
Assert-PathExists (Join-Path $postgresData 'PG_VERSION') 'PostgreSQL data directory'

New-Item -ItemType Directory -Force -Path $localLogRoot | Out-Null

$pgIsReady = Join-Path $postgresBin 'pg_isready.exe'
$pgCtl = Join-Path $postgresBin 'pg_ctl.exe'
& $pgIsReady -h 127.0.0.1 -p $postgresPort -q
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Starting PostgreSQL...' -ForegroundColor Cyan
    & $pgCtl -D $postgresData -l $postgresLog -o "-p $postgresPort -c listen_addresses=127.0.0.1" start
    if ($LASTEXITCODE -ne 0) {
        throw "PostgreSQL failed to start. See: $postgresLog"
    }
}
& $pgIsReady -h 127.0.0.1 -p $postgresPort -q
if ($LASTEXITCODE -ne 0) {
    throw 'PostgreSQL is not accepting connections.'
}
Write-Host 'PostgreSQL is ready.' -ForegroundColor Green

$env:DATABASE_URL = "postgresql+asyncpg://postgres@127.0.0.1:$postgresPort/ai_study_validation"
$env:LLM_ENABLED = 'false'
$env:VITE_API_BASE_URL = '/api/v1'

Write-Host 'Applying database migrations...' -ForegroundColor Cyan
& $alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    throw 'Alembic migration failed.'
}

$backendPidPath = Join-Path $localLogRoot 'backend.pid'
if (Test-Path -LiteralPath $backendPidPath) {
    $managedBackendPid = [int](Get-Content -Raw -LiteralPath $backendPidPath)
    $managedBackend = Get-Process -Id $managedBackendPid -ErrorAction SilentlyContinue
    if ($managedBackend -and $managedBackend.Path -eq $python) {
        Write-Host 'Restarting managed FastAPI process to load current code...' -ForegroundColor Cyan
        Stop-Process -Id $managedBackendPid -Force
        Start-Sleep -Milliseconds 500
    }
}

$backendHealth = "http://127.0.0.1:$backendPort/health"
if (-not (Test-HttpEndpoint $backendHealth)) {
    $backendOut = Join-Path $localLogRoot 'backend.out.log'
    $backendError = Join-Path $localLogRoot 'backend.error.log'
    $backendProcess = Start-Process -FilePath $python `
        -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', "$backendPort") `
        -WorkingDirectory $projectRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $backendOut `
        -RedirectStandardError $backendError `
        -PassThru
    Set-Content -LiteralPath $backendPidPath -Value $backendProcess.Id
    if (-not (Wait-HttpEndpoint $backendHealth)) {
        throw "FastAPI failed to start. See: $backendError"
    }
}
Write-Host "FastAPI is listening on 0.0.0.0:$backendPort." -ForegroundColor Green

$frontendHealth = "http://127.0.0.1:$frontendPort"
if (-not (Test-HttpEndpoint $frontendHealth)) {
    $frontendOut = Join-Path $localLogRoot 'frontend.out.log'
    $frontendError = Join-Path $localLogRoot 'frontend.error.log'
    $npm = (Get-Command npm.cmd -ErrorAction Stop).Source
    $frontendCommand = "`"$npm`" run dev -- --host 0.0.0.0 --port $frontendPort"
    $frontendProcess = Start-Process -FilePath 'cmd.exe' `
        -ArgumentList @('/c', $frontendCommand) `
        -WorkingDirectory $frontendRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $frontendOut `
        -RedirectStandardError $frontendError `
        -PassThru
    Set-Content -LiteralPath (Join-Path $localLogRoot 'frontend.pid') -Value $frontendProcess.Id
    if (-not (Wait-HttpEndpoint $frontendHealth)) {
        throw "Vite failed to start. See: $frontendError"
    }
}
Write-Host "Vite is listening on 0.0.0.0:$frontendPort." -ForegroundColor Green

$lanIPv4 = Get-LocalLanIPv4
Write-Host ''
Write-Host 'Local mobile test is running.' -ForegroundColor Green
Write-Host "PC URL:     http://127.0.0.1:$frontendPort"
if ($lanIPv4) {
    Write-Host "Phone URL:  http://${lanIPv4}:$frontendPort" -ForegroundColor Yellow
    Write-Host "API health: http://${lanIPv4}:$backendPort/health"
}
else {
    Write-Warning 'LAN IPv4 was not detected. Run ipconfig and find the active Wi-Fi IPv4 address.'
    Write-Host "Phone URL format: http://<PC-IPv4>:$frontendPort"
}
Write-Host ''
Write-Host 'Keep the phone and PC on the same Wi-Fi. If Windows Firewall prompts, allow Python and Node.js on private networks.'
Write-Host "Logs: $localLogRoot"
