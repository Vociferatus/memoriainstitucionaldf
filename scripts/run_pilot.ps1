$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Ambiente ausente. Execute: python -m venv .venv; .\.venv\Scripts\python -m pip install -e `".[dev]`""
}

& $python -m min_df.pipeline `
  "data\raw\DODF 112 22-06-2026 INTEGRA.pdf" `
  --output-dir ".artifacts\pilot" `
  --verify-pilot-baseline

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

