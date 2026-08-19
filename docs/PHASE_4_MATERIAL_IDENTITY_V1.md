# Fase 4 — Identidade material v1

## Resultado

A camada distingue explicitamente observação, hipótese e entidade material. Nenhuma
menção nominal é promovida automaticamente a pessoa ou órgão. O artefato JSON é
validado pelo contrato `identity-resolution/1.0`, persistido no PostgreSQL e ligado ao
ledger de proveniência.

Fluxo: `menção -> fragmento imutável -> decisão versionada -> entidade canônica`.

## Matriz executável v1

| Evidência | Classe | Decisão automática | Resultado |
|---|---:|---|---|
| Processo SEI normalizado | S | Mesmo identificador no escopo administrativo | `AUTO_LINK` para processo |
| CNPJ com dígitos válidos | U | Mesmo CNPJ e nenhuma divergência observada | `AUTO_LINK` para organização legal |
| CNPJ inválido | U inválida | Proibida | Caso `UNRESOLVED` |
| Nome de pessoa | N | Proibida | Fragmentos separados; grupo candidato se repetir |
| Cabeçalho de órgão | N | Proibida | Fragmentos separados; grupo candidato se repetir |
| Título de cargo | N | Proibida | Fragmentos separados; grupo candidato se repetir |

`U`: identificador único; `S`: único em um escopo; `N`: evidência nominal.

## Política de decisão

- O padrão é `KEEP_SEPARATE`.
- Fragmentos são evidências permanentes e não desaparecem após uma ligação.
- Coincidência nominal produz somente candidatura.
- Uma divergência não explicada suspende qualquer união.
- Ligações registram regra, motivo, versão e estado de revisão.
- Casos registram divergências e cadeia de análise, preservando decisões reversíveis.

## DODF 112 — linha de base

| Medida | Total |
|---|---:|
| Fragmentos observados | 1.645 |
| Afirmações nominais | 302 |
| Identificadores materiais | 1.343 |
| Entidades materializadas | 1.276 |
| Ligações automáticas | 1.342 |
| Grupos candidatos mantidos separados | 45 |
| Casos de resolução | 1 |
| Fragmentos ainda não ligados | 303 |

Por tipo: 1.140 fragmentos de processo, 203 de organização legal/CNPJ, 229 de
organização editorial, 49 de pessoa e 24 de cargo. Os 303 fragmentos não ligados são
as 302 menções nominais mais o CNPJ inválido; isso é comportamento intencional.

## Garantias verificadas

- Contrato JSON estrito e referências internas íntegras.
- Pessoa, organização editorial e cargo nunca recebem `AUTO_LINK` por nome.
- CNPJ inválido abre caso e não cria entidade canônica.
- Carga PostgreSQL repetível, com reconstrução segura da projeção semântica.
- Visões: `navigable_material_entities`, `navigable_identity_evidence` e
  `navigable_identity_review_queue`.

## Limite consciente desta versão

O CNPJ materializa uma organização legal identificada, mas ainda não atribui razão
social. Pessoas e órgãos dependem da próxima evolução: extração de CPF/matrícula,
vínculos temporais, hierarquia institucional, denominações legais e tratamento
formal de divergências. O futuro front deve exibir separadamente entidades materiais,
fragmentos candidatos e fila de casos, sem esconder o grau de certeza.
