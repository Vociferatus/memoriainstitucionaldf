$ErrorActionPreference = "Stop"

$env:DATABASE_URL = "postgresql://memoria:memoria_local@localhost:5432/memoria_institucional"

python scripts\load_to_postgres.py `
  --manifest "data\manifests\DODF 112 22-06-2026 INTEGRA.manifest.json" `
  --structured "data\structured\DODF 112 22-06-2026 INTEGRA.structured.json" `
  --mentions "data\extractions\DODF 112 22-06-2026 INTEGRA.mentions.json"
