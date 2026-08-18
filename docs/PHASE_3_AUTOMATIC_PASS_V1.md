# Fase 3 — Passe automático v1 do DODF 112

Data: 2026-08-18. Status: primeiro passe automático concluído; a Fase 3 continua
aberta para ampliar a cobertura, e a revisão humana integral pertence à Fase 4.

## Resultado

O DODF 112 agora pode ser percorrido por seção, contexto editorial, matéria,
ação, entidade, processo, página, bloco, bbox e span. Nenhuma saída automática é
tratada como entidade canônica ou evento consolidado.

Contagens congeladas do passe v1:

- 2.553 blocos classificados exatamente uma vez;
- 3 seções, iniciando nas páginas 1, 31 e 50;
- 133 contextos editoriais, incluindo cabeçalhos unidos;
- 403 matérias, das quais 33 preservadas como `unclassified`;
- 54 matérias atravessam páginas;
- 834 dispositivos `Art.`;
- 114 ações administrativas prioritárias;
- 145 menções editoriais de organizações, 49 pessoas e 24 cargos;
- 49 relações explícitas ação → participante;
- 203 CNPJs (202 válidos e 1 inválido preservado);
- 547 valores monetários e 646 referências normativas.

## Navegação disponível

As views `navigable_published_items`, `navigable_entity_occurrences`,
`navigable_process_items` e `navigable_action_entities` suportam os caminhos:

```text
edição → seção → breadcrumb → matéria
matéria → ação → pessoa
pessoa/órgão/cargo → ocorrências → matéria
processo → matéria
ocorrência → página → bloco → bbox/span
```

Exemplo validado: o processo `04018-00001552/2021-01` conduz à Ordem de Serviço
nº 90, página 1, bloco `p0001-b0043`. A pessoa `TELMA APOSTOLO EVANGELISTA`
conduz à ação `DESIGNAR` na Portaria de 19 de junho de 2026, página 37.

## Limites deliberados

- Contextos editoriais são observados; não representam hierarquia institucional
  canônica.
- Pessoas são candidatas extraídas de ações prioritárias; assinaturas e demais
  papéis ainda exigem ampliação e revisão.
- Empresas citadas por CNPJ não são consolidadas automaticamente.
- O único CNPJ com dígito inválido permanece marcado como inválido.
- Matrículas e identificadores administrativos pessoais não são promovidos.
- Efeito, vigência, retificação e revogação entre matérias ainda necessitam de
  regras e conjunto ouro antes de consolidação.
- Precisão e recall não são declarados sem revisão manual das 85 páginas.

## Validação

- bateria local completa aprovada na validação final;
- base existente migrada e carga repetida idempotente para o mesmo artefato;
- base limpa produziu `3|133|403|114|218|1396|49`;
- todo span automático foi comparado ao literal do bloco de origem.
