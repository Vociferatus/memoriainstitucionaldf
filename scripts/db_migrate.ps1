$ErrorActionPreference = "Stop"

docker compose exec -T postgres sh -c `
  'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -f /workspace/db/migrations/001_initial_schema.sql'

if ($LASTEXITCODE -ne 0) {
  throw "Falha ao aplicar a migração (código $LASTEXITCODE)."
}
