param(
    [string]$ComposeFile = "docker\docker-compose.yml",
    [string]$BaseUrl = "http://localhost:8000",
    [string]$TraceId = "e2e_trace_001",
    [int]$TimeoutSec = 120,
    [switch]$RunNaturalLanguageQuery,
    [switch]$ShutdownAfter,
    [switch]$CollectLogs
)

$ErrorActionPreference = "Stop"

function Wait-ForHealthy {
    param(
        [string]$Url,
        [int]$Timeout
    )

    $start = Get-Date
    while (((Get-Date) - $start).TotalSeconds -lt $Timeout) {
        try {
            $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
            if ($resp.StatusCode -eq 200) {
                return $true
            }
        } catch {
            Start-Sleep -Seconds 2
        }
    }
    return $false
}

Write-Host "==> Starting services" -ForegroundColor Cyan
& docker compose -f $ComposeFile up -d --build | Out-Host

Write-Host "==> Waiting for healthz" -ForegroundColor Cyan
if (-not (Wait-ForHealthy -Url "$BaseUrl/healthz" -Timeout $TimeoutSec)) {
    Write-Host "Health check timeout" -ForegroundColor Red
    exit 1
}

Write-Host "==> POST trace" -ForegroundColor Cyan
$trace = @{
    trace_id = $TraceId
    attributes = @{ system_prompt = "You are helpful" }
    spans = @(
        @{
            span_id = "span_001"
            name = "LLM Inference"
            start_time = "2025-02-06T10:00:00Z"
            end_time = "2025-02-06T10:00:01Z"
            attributes = @{ "toolbrain.span.type" = "llm_inference" }
        }
    )
}

Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/traces" -ContentType "application/json" -Body ($trace | ConvertTo-Json -Depth 8) | Out-Host

Write-Host "==> GET traces" -ForegroundColor Cyan
Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/v1/traces?skip=0&limit=5" | Out-Host

Write-Host "==> GET trace by id" -ForegroundColor Cyan
Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/v1/traces/$TraceId" | Out-Host

Write-Host "==> POST feedback" -ForegroundColor Cyan
$feedback = @{ rating = 5; comment = "E2E ok" }
Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/traces/$TraceId/feedback" -ContentType "application/json" -Body ($feedback | ConvertTo-Json) | Out-Host

Write-Host "==> GET stats" -ForegroundColor Cyan
Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/v1/stats" | Out-Host

$nlqFailed = $false
if ($RunNaturalLanguageQuery) {
    Write-Host "==> POST natural language query" -ForegroundColor Cyan
    $nlq = @{ query = "Show recent traces" }
    $nlqResp = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/natural_language_query" -ContentType "application/json" -Body ($nlq | ConvertTo-Json)
    $nlqResp | Out-Host
    if ($nlqResp.answer -match "error" -or $nlqResp.answer -match "internal") {
        $nlqFailed = $true
    }
}

Write-Host "==> E2E completed" -ForegroundColor Green

if ($ShutdownAfter) {
    if ($CollectLogs -or $nlqFailed) {
        Write-Host "==> Collecting tracing-api logs" -ForegroundColor Cyan
        if (-not (Test-Path -Path "logs")) {
            New-Item -ItemType Directory -Path "logs" | Out-Null
        }
        & docker compose -f $ComposeFile logs tracing-api | Out-File -FilePath "logs\e2e_tracing_api.log" -Encoding utf8
        Write-Host "Logs saved to logs\e2e_tracing_api.log" -ForegroundColor Yellow
    }
    Write-Host "==> Shutting down services" -ForegroundColor Cyan
    & docker compose -f $ComposeFile down | Out-Host
}
