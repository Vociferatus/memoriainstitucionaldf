$ErrorActionPreference = "Stop"

foreach ($migration in @(
  "001_initial_schema.sql",
  "002_evidence_ledger_v2.sql",
  "003_semantic_navigation.sql",
  "004_material_identity.sql"
)) {
  $command = 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" ' +
    "-v ON_ERROR_STOP=1 -f /workspace/db/migrations/$migration"
  docker compose exec -T postgres sh -c $command

  if ($LASTEXITCODE -ne 0) {
    throw "Falha ao aplicar $migration (código $LASTEXITCODE)."
  }
}
