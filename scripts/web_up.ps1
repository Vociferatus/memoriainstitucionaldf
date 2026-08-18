$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
  $python = "python"
}

& $python (Join-Path $PSScriptRoot "build_explorer_data.py") `
  --structured (Join-Path $projectRoot "data\structured\DODF 112 22-06-2026 INTEGRA.structured.json") `
  --mentions (Join-Path $projectRoot "data\extractions\DODF 112 22-06-2026 INTEGRA.mentions.json") `
  --output (Join-Path $projectRoot "web\public\dodf112.json")
if ($LASTEXITCODE -ne 0) {
  throw "Falha ao preparar os dados do explorador (código $LASTEXITCODE)."
}

$webRoot = Join-Path $projectRoot "web"
if (-not (Test-Path -LiteralPath (Join-Path $webRoot "node_modules"))) {
  Push-Location $webRoot
  try {
    npm ci --ignore-scripts --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) {
      throw "Falha ao instalar o painel (código $LASTEXITCODE)."
    }
  }
  finally {
    Pop-Location
  }
}

Write-Host "Explorador disponível em http://localhost:3000"
Push-Location $webRoot
try {
  npm run dev
}
finally {
  Pop-Location
}
