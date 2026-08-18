# Encerramento da Fase 0

Data: 2026-08-18
Fase: Preservação e linha de base
Status: concluída.

## Resultado

A linha de base do piloto DODF 112 foi preservada, importada, auditada,
inventariada e registrada no Git antes de qualquer refatoração.

## Evidências de conclusão

- pacote ancestral preservado com SHA-256
  `4FB61581FA375BFADA32952E38318784B5535D2469823081915252DA65359BC7`;
- PDF piloto preservado com SHA-256
  `17389D23375C9B9B747C8A0F74305CE20EE4B52DBC20E23D92BEF780EC4709FC`;
- 28 arquivos do inventário criptográfico verificados;
- 85 páginas reproduzidas;
- 2.553 blocos reproduzidos sem divergência;
- 179 blocos de ruído preservados;
- Markdown reproduzido byte a byte;
- 1.140 menções SEI reproduzidas sem divergência;
- 1.096 processos únicos;
- zero menções sem bloco;
- scripts compilados;
- auditor original aprovado;
- carga em `dry-run` aprovada;
- banco histórico consultado e preservado;
- política de dados e artefatos definida;
- primeiro commit criado;
- tag de recuperação criada.

## Registro Git

Commit da linha de base:

```text
3823f93 chore: preserve recovered DODF pilot baseline
```

Tag anotada:

```text
recovered-pilot-v1
```

A tag representa o snapshot histórico inventariado em
`BASELINE_SHA256SUMS.txt`. Mudanças posteriores não devem mover ou recriar essa
tag.

## Política adotada

O baseline de aproximadamente 18,7 MB foi preservado integralmente no Git como
exceção histórica. Novos PDFs, artefatos derivados e pacotes ZIP são ignorados
por padrão e só podem ser incorporados após registro explícito de proveniência.

Os bytes recuperados foram adicionados sem conversão automática de fim de
linha. Eventuais normalizações futuras deverão ocorrer em commits próprios.

## Estado de passagem

Todos os critérios da Fase 0 estão satisfeitos. A próxima etapa autorizável é:

```text
Fase 1 — Fundação reproduzível
```

Seu primeiro marco será transformar a reprodução manual já comprovada em uma
execução automatizada, contratada e protegida por testes.
