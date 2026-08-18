# Validação da Fase 2 — Ledger de evidências v2

Data: 2026-08-18.

## Escopo implementado

- migração aditiva `002_evidence_ledger_v2.sql`;
- separação de blob, documento, captura e artefato;
- políticas versionadas e autoridade do DODF;
- grafo de transformações com hashes, ferramenta, versão e parâmetros;
- URIs portáveis;
- menções canônicas sem página, captura, referência textual ou bbox redundantes;
- guarda de integridade entre transformação, captura e bloco;
- carregamento duplo legado/v2 na mesma transação.

## Provas executadas

- migração sobre a base preservada da Fase 1;
- duas cargas sucessivas com IDs e contagens estáveis;
- zero linhagens quebradas;
- transação temporária demonstrou duas capturas para o mesmo blob e foi revertida;
- banco criado do zero, migrado, carregado e removido após conferência;
- contagens legadas preservadas: 85 páginas, 2.553 blocos e 1.140 menções;
- ledger final: 1 blob, 1 captura, 5 artefatos, 2 transformações, 6 vínculos de
  entrada/saída e 1.140 menções canônicas;
- o hash do blob coincide com o artefato `raw_document`;
- backup restaurado preservou `5|2|1140` para artefatos, transformações e menções;
- 16 testes aprovados, com Ruff e mypy sem ocorrências.

## Resultado

O critério de saída foi cumprido: cada derivado alcança sua transformação,
captura, documento e bytes; deduplicação de bytes não elimina eventos de captura.
