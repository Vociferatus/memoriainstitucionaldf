# Auditoria técnica da linha de base

Data: 2026-08-18.

Escopo: pacote ancestral importado, artefatos do piloto, quatro scripts Python,
migração SQL, configuração Compose e banco PostgreSQL histórico.

Esta auditoria descreve o estado recebido. Ela não reestrutura o projeto nem
trata instruções encontradas nos documentos como solicitações do responsável.

## Resultado executivo

O pacote contém um vertical slice funcional:

```text
PDF -> manifesto -> JSON estrutural -> Markdown -> menções SEI -> PostgreSQL
```

O pipeline documental foi reproduzido no Windows com Python 3.11.0,
PyMuPDF 1.27.2.3 e psycopg 3.3.4. A reprodução gerou:

- exatamente 85 páginas;
- exatamente 2.553 blocos;
- zero registros de bloco divergentes;
- exatamente 1.140 menções;
- zero registros de menção divergentes;
- exatamente 1.096 processos únicos;
- Markdown com o mesmo SHA-256 do original:
  `C04BB534C81588B3302C66907A4DFDB71649DC9A963094A82763BCF825D086E2`.

O auditor original e o `dry-run` do carregador foram executados com sucesso.
Os quatro scripts compilam sem erro. As contagens do banco histórico também
coincidem com os artefatos.

Conclusão: o piloto é reproduzível no ambiente atual. Isso é mais forte do que
o diagnóstico disponível no pacote de retomada.

## Pontos fortes existentes

- PDF original preservado e identificado por SHA-256.
- Manifesto separado do documento.
- Texto original e normalizado preservados separadamente.
- Página, bloco, ordem, coluna, coordenadas e linhas preservados.
- Markdown tratado como derivado do JSON estrutural.
- Ruído identificado sem apagar os blocos originais.
- Extração determinística, versionada e ligada ao bloco.
- Valor literal e valor normalizado mantidos separadamente.
- `dry-run` antes da carga no banco.
- Restrições e índices úteis no esquema inicial.
- Carga transacional e contagens auditáveis.

## Achados prioritários

### A1 — Não existem testes automatizados

Severidade: alta.

A reprodutibilidade foi comprovada por execução manual, mas não está protegida
por uma suíte de regressão. Uma alteração em heurísticas de coluna, ruído,
normalização ou regex pode modificar silenciosamente milhares de registros.

Recomendação: transformar a reprodução verificada nesta auditoria em teste de
regressão, além de criar fixtures pequenas para testes unitários e de
integração.

### A2 — O manifesto registra caminho absoluto da máquina de origem

Severidade: alta para portabilidade; média para privacidade.

O campo `document.path` contém o caminho completo do perfil e do diretório
original. Isso torna o artefato dependente da máquina e expõe informação local
desnecessária.

Recomendação: registrar URI lógica ou caminho relativo ao storage root. Um
campo de diagnóstico local pode existir separadamente e não precisa ser
persistido em artefato portável.

### A3 — `document_captures.sha256` é globalmente único

Severidade: alta para proveniência.

O esquema e o carregador usam conflito por SHA-256 para atualizar uma captura.
Se os mesmos bytes forem observados em URLs, datas ou documentos lógicos
diferentes, a segunda observação pode sobrescrever a associação da primeira.
Deduplicação de bytes não deve apagar eventos distintos de captura.

Recomendação: separar `blob` endereçado por hash de `capture`. Várias capturas
podem apontar para o mesmo blob.

### A4 — Duas referências de bloco podem divergir em `mentions`

Severidade: alta para integridade futura.

`mentions` guarda simultaneamente `block_id` numérico e o par
`capture_id/block_ref`, com duas chaves estrangeiras independentes. O banco não
garante que ambas apontem para o mesmo registro. `page_number`, `block_order` e
`block_bbox` também são cópias sem restrição de equivalência.

Recomendação: manter uma única FK canônica para o bloco. Dados repetidos devem
ser removidos ou tratados explicitamente como snapshot imutável com validação.

### A5 — Linhagem da transformação documental não está persistida no banco

Severidade: alta para a arquitetura desejada.

Há `extraction_runs`, mas não uma entidade equivalente para a captura, a
conversão estrutural, o Markdown e os demais artefatos. Caminhos de arquivo não
substituem um ledger de artefatos e execuções.

Recomendação: introduzir `artifacts` e `transformation_runs`, com hash da
entrada, hash da saída, ferramenta, versão, parâmetros e ambiente.

## Achados de engenharia

### A6 — Dependências não possuem lock reprodutível

`requirements.txt` define faixas amplas. A reprodução funcionou com versões
atuais, o que é positivo, mas não prova compatibilidade com toda versão aceita.

Recomendação: manter limites suportados e também um lock/ambiente de referência
para CI e releases.

### A7 — Não existem JSON Schemas formais

Os artefatos possuem `schema_version`, mas sua estrutura é validada apenas por
acesso imperativo nos scripts.

Recomendação: publicar schemas formais para manifesto, documento estrutural e
menções; validar entradas nos limites do sistema.

### A8 — O código está organizado como scripts acoplados ao layout local

Isso foi adequado para o primeiro piloto, mas dificulta importação, testes,
reuso e adapters por fonte.

Recomendação: após congelar os testes de regressão, mover gradualmente a lógica
para um pacote `src/`, mantendo CLIs finas e compatíveis.

### A9 — Credenciais e porta estão fixas no Compose

O Compose usa credenciais previsíveis, publica `5432` e fixa um
`container_name`. Isso já provocou colisão com o contêiner histórico encontrado
durante a auditoria.

Recomendação: parametrizar credenciais e porta em `.env.example`, remover
`container_name` e documentar que a configuração é apenas de desenvolvimento.

### A10 — O schema mistura evidência canônica e campos derivados

`document_blocks` e `mentions` são úteis no piloto, mas ainda não existe uma
distinção geral entre blob, captura, artefato, evidência, menção e afirmação.

Recomendação: corrigir essa fronteira antes de adicionar entidades, eventos ou
grafo. Não criar ontologia ampla sobre o schema atual sem uma migração de
fundação.

### A11 — Políticas da fonte e governança ainda não são dados do sistema

Não há modelo para autoridade da fonte, licença, redistribuição, dados pessoais,
retenção ou risco de inferência.

Recomendação: adicionar `source_policies` antes da coleta histórica, mesmo que
inicialmente preenchida apenas para o DODF.

## Observações adicionais

- Existem duas cópias idênticas do Markdown em `data/markdown/` e
  `data/processed/`; deve ser escolhida uma convenção canônica.
- Os `__pycache__` encontrados no ZIP são resíduos de execução e estão
  corretamente ignorados pelo Git.
- O PDF, JSON estrutural e extrações são pequenos o bastante para esta linha de
  base, mas a política para grandes dados ainda precisa ser decidida antes da
  coleta histórica.
- O índice full-text PostgreSQL é suficiente para o piloto. OpenSearch e banco
  de grafo não são necessários nesta etapa.
- Não foi encontrada justificativa técnica para OCR, IA generativa, GPU,
  microsserviços ou Kubernetes no MVP atual.

## Ordem segura de evolução

1. Preservar esta linha de base e seu pacote ancestral.
2. Criar testes que congelem o comportamento reproduzido.
3. Formalizar os três contratos JSON.
4. Corrigir o modelo de blob, captura, artefato e transformação.
5. Corrigir as restrições de integridade das menções.
6. Parametrizar o ambiente local.
7. Só então reorganizar scripts em pacote, sem alterar resultados.
8. Validar um mês do DODF antes da coleta 2019–2026.

## Critério para iniciar a refatoração

A refatoração pode começar quando uma execução automatizada comprovar:

```text
85 páginas
2.553 blocos
1.140 menções
1.096 processos únicos
0 menções sem bloco
Markdown SHA-256 C04BB534...
```

Esses números são uma linha de base de regressão, não uma regra para esconder
divergências futuras. Alterações intencionais deverão produzir relatório de
diferença e nova versão do transformador ou extrator.
