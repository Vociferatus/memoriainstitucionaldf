$ErrorActionPreference = "Stop"

docker compose exec -T postgres psql `
  -U memoria `
  -d memoria_institucional `
  -v ON_ERROR_STOP=1 `
  -f /workspace/db/migrations/001_initial_schema.sql
