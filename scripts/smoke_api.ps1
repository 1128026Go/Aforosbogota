Param(
  [string]$ApiBase = "http://localhost:3004",
  [string]$FrontendBase = "http://localhost:3000",
  [switch]$ShowHeaders
)

$ErrorActionPreference = 'Stop'

function Test-Endpoint([string]$Method, [string]$Url, [hashtable]$Headers=$null, [string]$Body=$null) {
  try {
    if ($Method -eq 'OPTIONS') {
      $res = Invoke-WebRequest -Method Options -Uri $Url -Headers $Headers -ErrorAction Stop
    } elseif ($Body) {
      $res = Invoke-WebRequest -Method $Method -Uri $Url -Headers $Headers -Body $Body -ContentType 'application/json' -ErrorAction Stop
    } else {
      $res = Invoke-WebRequest -Method $Method -Uri $Url -Headers $Headers -ErrorAction Stop
    }
    if ($ShowHeaders) { $res.Headers }
    return @{ ok = $true; status = $res.StatusCode; body = $res.Content }
  } catch {
    $status = $_.Exception.Response.StatusCode.Value__
    return @{ ok = $false; status = $status; error = $_.Exception.Message }
  }
}

Write-Host "[smoke] API base: $ApiBase"
Write-Host "[smoke] Frontend base (for CORS preflight): $FrontendBase"

# 1) Health
$health = Test-Endpoint -Method GET -Url "$ApiBase/health"
Write-Host "[smoke] GET /health -> $($health.status)" -ForegroundColor ($(if($health.ok){'Green'} else {'Red'}))

# 2) Metrics (puede estar deshabilitado en prod)
$metrics = Test-Endpoint -Method GET -Url "$ApiBase/metrics"
Write-Host "[smoke] GET /metrics -> $($metrics.status) (esperado 200 si METRICS_ENABLED=true)" -ForegroundColor ($(if($metrics.ok){'Green'} else {'Yellow'}))

# 3) Preflight CORS (cross-origin)
$preflightHeaders = @{
  'Origin' = $FrontendBase;
  'Access-Control-Request-Method' = 'GET'
}
$preflight = Test-Endpoint -Method OPTIONS -Url "$ApiBase/api/datasets" -Headers $preflightHeaders
Write-Host "[smoke] OPTIONS /api/datasets (preflight) -> $($preflight.status)" -ForegroundColor ($(if($preflight.ok){'Green'} else {'Red'}))

# 4) Lista de datasets (no requiere dataset cargado)
$datasets = Test-Endpoint -Method GET -Url "$ApiBase/api/datasets"
Write-Host "[smoke] GET /api/datasets -> $($datasets.status)" -ForegroundColor ($(if($datasets.ok){'Green'} else {'Red'}))

# 5) Resultado final
$allOk = $health.ok -and $datasets.ok
if ($allOk) {
  Write-Host "[smoke] Resultado: OK" -ForegroundColor Green
  exit 0
} else {
  Write-Host "[smoke] Resultado: con advertencias/errores (revisar arriba)" -ForegroundColor Yellow
  exit 1
}
