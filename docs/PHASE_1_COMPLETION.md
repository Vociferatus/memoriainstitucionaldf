# Conclusão da Fase 1 — Fundação reproduzível

Data de validação: 2026-08-18.

## Resultado

A referência recuperada foi convertida em pacote Python instalável, protegida
por contratos e testes, sem modificar o PDF ou os derivados históricos.

- pacote `min_df` em layout `src/` e wrappers das CLIs anteriores;
- ambiente de referência registrado e PyMuPDF 1.27.2.3 fixado;
- comando único `scripts/run_pilot.ps1`;
- contratos JSON Schema para manifesto, estrutura e menções;
- Compose parametrizado, sem nome fixo de contêiner;
- lint, tipos e testes automatizados em CI;
- scripts PowerShell com falha explícita quando comandos externos falham.

## Evidências de validação

- 13 testes aprovados;
- Ruff: zero ocorrências;
- mypy: zero ocorrências em 8 arquivos;
- reprodução: 85 páginas, 2.553 blocos, 179 ruídos;
- extração: 1.140 menções, 1.096 valores únicos, zero órfãs;
- PDF SHA-256: `17389d23375c9b9b747c8a0f74305ce20ee4b52dbc20e23d92bef780ec4709fc`;
- Markdown SHA-256: `c04bb534c81588b3302c66907a4dfdb71649dc9a963094a82763bcf825d086e2`;
- duas cargas sucessivas mantiveram 1 documento, 85 páginas, 2.553 blocos,
  1 rodada de extração e 1.140 menções;
- backup restaurado em base temporária e conferido como `85|2553|1140`;
- base e dump temporários foram removidos após a prova.

## Decisão de passagem

Os critérios técnicos da Fase 1 foram cumpridos. O próximo trabalho é a Fase 2:
evoluir o ledger de evidências sem introduzir ainda inferências ou resolução de
entidades no banco mestre.
