[CmdletBinding()]
param(
    [switch]$SkipConnectionCheck
)

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot
$envPath = Join-Path $projectRoot ".env"
$examplePath = Join-Path $projectRoot ".env.example"

if (-not (Test-Path -LiteralPath $envPath)) {
    Copy-Item -LiteralPath $examplePath -Destination $envPath
}

Write-Host ""
Write-Host "拾光 AI 配置（DeepSeek）" -ForegroundColor Cyan
Write-Host "API Key 只会保存到已被 Git 忽略的本地 .env 文件。"
Write-Host ""

$secureKey = Read-Host "请输入 DeepSeek API Key" -AsSecureString
$keyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
try {
    $apiKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPointer)
}
finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($keyPointer)
}

if ([string]::IsNullOrWhiteSpace($apiKey)) {
    throw "API Key 不能为空。"
}

function Set-EnvValue {
    param(
        [string[]]$Lines,
        [string]$Name,
        [string]$Value
    )
    $replacement = "$Name=$Value"
    $matched = $false
    $updated = foreach ($line in $Lines) {
        if ($line -match "^$([regex]::Escape($Name))=") {
            $matched = $true
            $replacement
        }
        else {
            $line
        }
    }
    if (-not $matched) {
        $updated += $replacement
    }
    return [string[]]$updated
}

$lines = [IO.File]::ReadAllLines($envPath)
$lines = Set-EnvValue $lines "LLM_ENABLED" "true"
$lines = Set-EnvValue $lines "LLM_BASE_URL" "https://api.deepseek.com"
$lines = Set-EnvValue $lines "LLM_API_KEY" $apiKey
$lines = Set-EnvValue $lines "LLM_MODEL" "deepseek-v4-flash"
$lines = Set-EnvValue $lines "LLM_TIMEOUT_SECONDS" "20"
$lines = Set-EnvValue $lines "LLM_MAX_RETRIES" "2"
[IO.File]::WriteAllLines($envPath, $lines, [Text.UTF8Encoding]::new($false))

$apiKey = $null
Set-Location -LiteralPath $projectRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    $python = "python"
}

Write-Host ""
Write-Host "配置已保存，正在执行安全检查……" -ForegroundColor Green
if ($SkipConnectionCheck) {
    & $python -m app.cli.ai doctor
}
else {
    & $python -m app.cli.ai doctor --check-connection
}
if ($LASTEXITCODE -ne 0) {
    throw "AI配置已保存，但连通性检查失败。请检查Key、余额和网络后重试。"
}

Write-Host ""
Write-Host "AI接入成功。请重启FastAPI使正在运行的服务读取新配置。" -ForegroundColor Green
