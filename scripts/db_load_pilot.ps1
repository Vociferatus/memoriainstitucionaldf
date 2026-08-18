$ErrorActionPreference = "Stop"

if (-not $env:DATABASE_URL) {
  $db = if ($env:POSTGRES_DB) { $env:POSTGRES_DB } else { "memoria_institucional" }
  $user = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "memoria" }
  $password = if ($env:POSTGRES_PASSWORD) { $env:POSTGRES_PASSWORD } else { "memoria_local" }
  $port = if ($env:POSTGRES_PORT) { $env:POSTGRES_PORT } else { "5432" }
  $env:DATABASE_URL = "postgresql://${user}:${password}@localhost:${port}/${db}"
}

$python = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
  $python = "python"
}

& $python scripts\load_to_postgres.py `
  --manifest "data\manifests\DODF 112 22-06-2026 INTEGRA.manifest.json" `
  --structured "data\structured\DODF 112 22-06-2026 INTEGRA.structured.json" `
  --mentions "data\extractions\DODF 112 22-06-2026 INTEGRA.mentions.json"

if ($LASTEXITCODE -ne 0) {
  throw "Falha ao carregar o piloto (código $LASTEXITCODE)."
}
