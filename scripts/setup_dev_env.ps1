Param(
    [switch]$Merge,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

# Paths
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$rootReq = Join-Path $repoRoot 'requirements.txt'
$apiReq = Join-Path $repoRoot 'api\requirements.txt'
$devReq = Join-Path $repoRoot 'requirements.dev.txt'

Write-Host "[setup_dev_env] Repo: $repoRoot"
Write-Host "[setup_dev_env] Root requirements: $rootReq"
Write-Host "[setup_dev_env] API requirements:  $apiReq"

if (!(Test-Path $rootReq)) { throw "No se encontró requirements.txt en la raíz: $rootReq" }
if (!(Test-Path $apiReq))  { throw "No se encontró api/requirements.txt: $apiReq" }

function Get-EffectiveLines([string]$path) {
    Get-Content -Path $path | ForEach-Object { $_.Trim() } | Where-Object {
        $_ -and -not $_.StartsWith('#')
    }
}

$rootLines = Get-EffectiveLines $rootReq
$apiLines  = Get-EffectiveLines $apiReq

# Unión de dependencias (case-insensitive, orden alfabético por legibilidad)
$merged = @($rootLines + $apiLines | Sort-Object -Unique)

"# Archivo generado por scripts/setup_dev_env.ps1 - no versionar en producción" | Set-Content -Encoding UTF8 $devReq
$merged | Add-Content -Encoding UTF8 $devReq

Write-Host "[setup_dev_env] Merged requirements -> $devReq"
Write-Host "[setup_dev_env] Total únicas: $($merged.Count)"

if ($DryRun) {
    Write-Host "[setup_dev_env] DryRun activo: no se instalarán paquetes."
    exit 0
}

# Determinar Python actual y pip
try {
    $pythonPath = (& python -c "import sys; print(sys.executable)" )
} catch {
    throw "Python no encontrado en PATH. Activa tu venv o instala Python."
}

Write-Host "[setup_dev_env] Usando Python: $pythonPath"

# Instalar paquetes
if ($Merge) {
    Write-Host "[setup_dev_env] Instalando desde requirements.dev.txt"
    & python -m pip install -r $devReq
} else {
    Write-Host "[setup_dev_env] Instalando desde archivos separados (root y api)"
    & python -m pip install -r $rootReq
    & python -m pip install -r $apiReq
}

# Verificación opcional de imports clave
try {
    & python -c "import prometheus_fastapi_instrumentator, opentelemetry, slowapi; print('Imports OK')"
    Write-Host "[setup_dev_env] Verificación de imports OK"
} catch {
    Write-Warning "[setup_dev_env] Algunos imports opcionales fallaron. Revisa la salida anterior."
}

Write-Host "[setup_dev_env] Listo. Si Pylance sigue marcando errores, confirma el intérprete activo en VS Code (Ctrl+Shift+P -> 'Python: Select Interpreter')."
