$ErrorActionPreference = "Stop"

docker compose exec -T postgres sh -c `
  'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT ''sources'' AS tabela, count(*) FROM sources UNION ALL SELECT ''documents'', count(*) FROM documents UNION ALL SELECT ''document_captures'', count(*) FROM document_captures UNION ALL SELECT ''document_pages'', count(*) FROM document_pages UNION ALL SELECT ''document_blocks'', count(*) FROM document_blocks UNION ALL SELECT ''extraction_runs'', count(*) FROM extraction_runs UNION ALL SELECT ''mentions'', count(*) FROM mentions;"'

if ($LASTEXITCODE -ne 0) {
  throw "Falha ao consultar contagens gerais (código $LASTEXITCODE)."
}

docker compose exec -T postgres sh -c `
  'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT mention_type, count(*) AS total, count(DISTINCT value_normalized) AS unicos FROM mentions GROUP BY mention_type;"'

if ($LASTEXITCODE -ne 0) {
  throw "Falha ao consultar contagens por tipo (código $LASTEXITCODE)."
}

docker compose exec -T postgres sh -c `
  'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT ''blobs'' AS tabela, count(*) FROM blobs UNION ALL SELECT ''captures'', count(*) FROM captures UNION ALL SELECT ''artifacts'', count(*) FROM artifacts UNION ALL SELECT ''transformation_runs'', count(*) FROM transformation_runs UNION ALL SELECT ''transformation_io'', count(*) FROM transformation_io UNION ALL SELECT ''evidence_mentions'', count(*) FROM evidence_mentions;"'

if ($LASTEXITCODE -ne 0) {
  throw "Falha ao consultar o ledger v2 (código $LASTEXITCODE)."
}
