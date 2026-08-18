# Fase 3 — Segmentação automática v2 do DODF 112

Data: 2026-08-18. Status: baseline automático de matérias atualizado e protegido
por regressão.

## Problemas corrigidos

O passe v1 preservava 33 itens como `unclassified`. A inspeção mostrou que essa
contagem misturava três problemas diferentes:

- cabeçalhos institucionais em blocos `h3` ou `paragraph` tratados como matéria;
- expediente gráfico no meio da ordem de leitura interrompendo matéria
  multipágina;
- tipos legítimos ainda ausentes do vocabulário automático.

O passe v2 distingue sequências de cabeçalhos pela matéria que vem em seguida,
mantém a matéria aberta ao atravessar cabeçalho e expediente de página e inclui
reconhecimento de dívida, notificação, julgamento, chamamento, resultado de
habilitação, resultado de licitação e atos da diretoria colegiada.

## Baseline v2

- 2.553 blocos classificados exatamente uma vez;
- 3 seções e 202 contextos editoriais;
- 457 matérias, sem descarte e sem `unclassified`;
- 53 matérias multipágina;
- 114 ações administrativas prioritárias;
- 302 menções de pessoas, organizações e cargos;
- 834 dispositivos `Art.` e 1.396 referências complementares.

Foram adicionadas regressões explícitas para a Ordem de Serviço nº 26, que
atravessa as páginas 1 e 2, e para o Edital nº 39/2026, cujo título ocupa vários
blocos na página 64. Nomes de signatários e empresas em `h3` não podem ser
promovidos a contexto editorial apenas por estarem em caixa alta.

## Interpretação correta

Zero `unclassified` significa que todas as matérias detectadas receberam um tipo
automático conhecido. Não significa que a segmentação tenha precisão e recall
humanamente certificados. Essa medição continua reservada ao conjunto ouro da
Fase 4.
