# Guia de anotação humana do DODF

Versão: 1.0
Data: 2026-08-18
Estado: protocolo inicial para calibração; ainda não aprovado pelo Portão 1.

## 1. Finalidade

Produzir uma referência humana independente para medir o sistema automático.
Anotar não significa corrigir o JSON automático nem confirmar a hipótese do
sistema: significa registrar o que o documento permite observar, inclusive
ambiguidade e ausência de informação.

## 2. Fonte de verdade da tarefa

A fonte primária é o PDF identificado por SHA-256. O JSON estrutural pode ajudar
a localizar blocos e spans, mas não prevalece sobre a página visual. Quando texto
e imagem divergirem, registrar `layout_failure` ou `source_ambiguity` e explicar.

Nunca usar conhecimento externo para completar nome, órgão, cargo, data ou
identidade que não esteja materialmente sustentada no escopo observado.

## 3. Modos de trabalho

### `blind_primary`

Primeira observação sem acesso às classificações automáticas. Registra somente
`observation`, com julgamento `PRESENT` ou `AMBIGUOUS` e `target: null`.

### `independent_second`

Segunda aplicação independente do mesmo guia. Não recebe as respostas da
primeira revisão nem as classificações automáticas.

### `assisted_review`

Compara uma saída automática com a fonte. Pode confirmar, rejeitar, apontar
omissão, marcar ambiguidade ou decidir identidade. Deve identificar hashes dos
artefatos automáticos usados.

### `adjudication`

Resolve desacordos entre lotes anteriores. Não altera os lotes originais; cria um
novo lote com `parent_batch_ids` e justificativa explícita.

## 4. Unidade e evidência

Cada registro deve ter uma tarefa, um julgamento e ao menos uma evidência. A
evidência aponta para documento, página e, quando aplicável, bloco, span e bbox.

- Use span para texto localizado dentro de um bloco.
- Use bloco sem span para estrutura ou matéria inteira.
- Use mais de uma evidência para limites, relações e decisões de identidade.
- Copie em `quote` apenas o mínimo necessário para conferir a decisão.
- Não invente coordenadas ausentes; use `null`.

Uma observação fora das páginas declaradas no lote é inválida.

## 5. Tarefas

### `document_structure`

Marcar seção, cabeçalho, rodapé, expediente, sumário, ruído, coluna ou falha de
ordem de leitura. Não interpretar hierarquia administrativa.

### `published_item_boundary`

Delimitar uma matéria publicada do primeiro ao último bloco. Uma matéria pode
atravessar páginas. Cabeçalho editorial não pertence automaticamente à matéria.
Retificação e republicação são matérias próprias, mesmo quando apontam para outra.

### `editorial_context`

Registrar o cabeçalho sob o qual a matéria foi publicada. Isso não prova que o
texto seja uma entidade institucional canônica nem que a hierarquia esteja vigente
fora daquela publicação.

### `entity_mention`

Marcar somente o texto que designa a entidade observada e classificar o tipo:

- `person`;
- `organization` para cabeçalho ou denominação institucional observada;
- `legal_organization` quando houver identificação material como CNPJ;
- `position` para cargo ou função;
- `process` para processo administrativo;
- `norm` para norma citada.

Nome semelhante não autoriza identidade. Cargo, órgão e pessoa são anotações
separadas, ainda que apareçam na mesma oração.

### `administrative_action`

Marcar o verbo administrativo expresso. Sujeito, cargo, órgão, processo e datas
são campos ou observações separados. Não promover uma ação textual a evento
histórico consolidado nesta etapa.

### `reference`

Marcar CNPJ, processo, norma, dispositivo, valor ou instrumento explicitamente
presente. Validar normalização separadamente da presença literal.

### `identity_resolution`

Usar somente em revisão assistida ou adjudicação. A decisão é:

- `SAME_ENTITY`: concordância material suficiente e nenhuma divergência aberta;
- `DISTINCT_ENTITIES`: evidência material incompatível;
- `UNRESOLVED`: evidência insuficiente ou divergência ainda explicável por tempo,
  escopo, retificação ou erro de fonte/extração.

São necessários ao menos dois fragmentos e justificativa. Nome, proximidade,
cargo semelhante ou mesmo órgão não bastam para `SAME_ENTITY`.

### `temporal_assertion`

Distinguir rigorosamente:

- `publication`: data da publicação;
- `signature`: data declarada de assinatura;
- `validity`: início ou intervalo de vigência;
- `effect`: data em que o ato declara produzir efeitos.

Não transportar uma data de um campo para outro sem declaração textual.

## 6. Julgamentos

| Julgamento | Uso |
|---|---|
| `PRESENT` | Observação humana encontrada sem comparar com saída automática |
| `CONFIRMED` | Registro automático correto no tipo, limite, papel e valor avaliados |
| `REJECTED` | Registro automático não sustentado pela fonte |
| `MISSING` | A fonte contém item que a saída automática omitiu |
| `AMBIGUOUS` | A fonte ou o guia não permitem decisão segura |
| `NOT_APPLICABLE` | O alvo não pertence à tarefa avaliada |
| `SAME_ENTITY` | Fragmentos materialmente da mesma entidade |
| `DISTINCT_ENTITIES` | Fragmentos materialmente incompatíveis |
| `UNRESOLVED` | Materialidade insuficiente para decidir |

Rejeição, ambiguidade e decisões de identidade exigem justificativa. Rejeição e
omissão exigem categoria de erro.

## 7. Taxonomia de erros

| Categoria | Definição |
|---|---|
| `false_positive` | O sistema criou algo não sustentado pela fonte |
| `false_negative` | A fonte contém algo que o sistema não criou |
| `boundary_error` | Início, fim ou span incorreto |
| `type_error` | Tipo ou classe incorreta |
| `role_error` | Participação ou papel incorreto |
| `normalization_error` | Valor literal correto, normalização incorreta |
| `link_error` | Relação ou consolidação incorreta |
| `temporal_error` | Tipo, valor ou intervalo temporal incorreto |
| `source_ambiguity` | O próprio documento não permite conclusão segura |
| `layout_failure` | Ordem, tabela, coluna, imagem ou extração visual falhou |
| `annotation_disagreement` | Revisores aplicaram o guia de modo diferente |

É permitido registrar mais de uma categoria. Não use `source_ambiguity` para
encobrir uma regra mal definida.

## 8. Confiança

- `certain`: a evidência e o guia sustentam uma única decisão;
- `probable`: a decisão é mais bem sustentada, mas há limitação documentada;
- `uncertain`: falta materialidade; normalmente acompanha `AMBIGUOUS` ou
  `UNRESOLVED`.

Confiança não substitui julgamento nem cria score de identidade.

## 9. Fluxo de calibração

1. selecionar duas páginas pequenas e representativas;
2. produzir um lote `blind_primary`;
3. após intervalo ou por segundo revisor, produzir `independent_second`;
4. comparar somente depois de fechar os dois lotes;
5. classificar desacordos;
6. ajustar o guia, nunca retroativamente os lotes;
7. criar lote de adjudicação;
8. repetir até que as decisões sejam compatíveis;
9. versionar o guia aprovado;
10. somente então iniciar as 12 páginas estratificadas.

## 10. Critério de compatibilidade do Portão 1

O protocolo pode avançar quando:

- não há desacordo sobre a definição de matéria e evidência;
- tipos prioritários são aplicados de forma consistente;
- toda diferença está classificada como erro, ambiguidade ou desacordo;
- decisões de identidade nunca usam somente nome ou proximidade;
- os lotes originais e a adjudicação permanecem preservados;
- qualquer mudança no guia gera nova versão.

Não estabeleceremos coeficiente estatístico definitivo com apenas duas páginas;
o objetivo da calibração é remover ambiguidades operacionais antes da amostra de
12 páginas.
