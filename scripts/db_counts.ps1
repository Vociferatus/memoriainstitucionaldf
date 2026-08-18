$ErrorActionPreference = "Stop"

docker compose exec -T postgres psql `
  -U memoria `
  -d memoria_institucional `
  -c "SELECT 'sources' AS tabela, count(*) FROM sources UNION ALL SELECT 'documents', count(*) FROM documents UNION ALL SELECT 'document_captures', count(*) FROM document_captures UNION ALL SELECT 'document_pages', count(*) FROM document_pages UNION ALL SELECT 'document_blocks', count(*) FROM document_blocks UNION ALL SELECT 'extraction_runs', count(*) FROM extraction_runs UNION ALL SELECT 'mentions', count(*) FROM mentions;"

docker compose exec -T postgres psql `
  -U memoria `
  -d memoria_institucional `
  -c "SELECT mention_type, count(*) AS total, count(DISTINCT value_normalized) AS unicos FROM mentions GROUP BY mention_type;"
