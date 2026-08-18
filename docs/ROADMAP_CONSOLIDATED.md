# Roadmap consolidado — Memória Institucional Navegável

Versão: 1.0
Data: 2026-08-18
Estado: planejamento aprovado para execução incremental.

## 1. Resultado pretendido

Construir uma infraestrutura capaz de consumir Diários Oficiais, preservar a
evidência original, estruturar matérias publicadas, localizar entidades e ações
administrativas, consolidar conhecimento entre documentos e produzir análises
e inferências auditáveis.

```text
fontes oficiais
    ↓
ledger de evidências
    ↓
base de conhecimento consolidado
    ↓
base analítica e de inferências
    ↓
busca, navegação, grafo e API
```

O desenvolvimento seguirá esta escala:

```text
1 edição impecável
→ 10 edições representativas
→ 1 mês completo
→ 1 ano completo
→ DODF 2019–2026
→ múltiplos Diários Oficiais
→ inferências longitudinais governadas
```

Nenhuma fase avança apenas porque o software “rodou”. Cada passagem depende de
critérios verificáveis de cobertura, qualidade, proveniência e
reprodutibilidade.

## 2. Princípios permanentes

1. Documento é evidência.
2. Nada derivado existe sem fonte.
3. Bytes originais nunca são sobrescritos.
4. Documento lógico, captura e blob são objetos diferentes.
5. Texto original e normalizado são campos diferentes.
6. Matéria publicada, ação, evento, estado e inferência são camadas distintas.
7. Menção não é entidade consolidada.
8. Resolução de identidade é explicável, versionada e reversível.
9. Conflitos entre fontes são preservados.
10. Ausência no corpus não prova ausência no mundo.
11. Busca, grafo e analytics são projeções reconstruíveis.
12. Inferências informam método, cobertura, incerteza e evidências.

## 3. Arquitetura lógica-alvo

### 3.1 Armazenamento documental

Responsável por bytes originais e artefatos imutáveis:

- PDFs, XML, HTML, JSON e demais respostas de fonte;
- metadados HTTP/API;
- hashes;
- manifestos;
- JSONs estruturais;
- artefatos derivados versionados.

Começa em filesystem controlado, atrás de uma interface de storage. Pode
evoluir para MinIO ou armazenamento S3-compatible sem alterar o domínio.

### 3.2 Schema `evidence`

Registra o que foi observado:

- fontes e políticas;
- documentos lógicos;
- blobs e capturas;
- páginas e blocos;
- contextos editoriais;
- matérias publicadas;
- dispositivos e ações textuais;
- menções de entidades;
- evidências e execuções de transformação.

### 3.3 Schema `knowledge`

Registra consolidações explicáveis:

- entidades canônicas;
- aliases e nomes históricos;
- candidatos e decisões de resolução;
- organizações e relações institucionais;
- cargos e funções;
- eventos documentados;
- relações temporais;
- conflitos e revisões humanas.

### 3.4 Schema `analytics`

Registra derivados reconstruíveis:

- snapshots de entrada;
- estados institucionais;
- séries históricas;
- indicadores;
- padrões e anomalias;
- inferências;
- evidências favoráveis e contrárias;
- confiança, incerteza e classificação de sensibilidade.

### 3.5 Schema `audit`

Registra:

- versões de regras e modelos;
- revisões humanas;
- mudanças de decisão;
- execuções e falhas;
- consultas e exportações sensíveis;
- linhagem entre todas as camadas.

No início, os quatro schemas podem residir na mesma instância PostgreSQL. A
separação física ocorrerá somente quando volume, segurança ou operação a
justificarem.

## 4. Estado atual

### Concluído e verificado

- pacote ancestral preservado;
- PDF original da edição DODF 112 preservado e verificado por SHA-256;
- pipeline PDF → manifesto → JSON estrutural → Markdown;
- 85 páginas e 2.553 blocos reproduzidos exatamente;
- extrator determinístico de processos SEI;
- 1.140 menções e 1.096 processos únicos reproduzidos exatamente;
- zero menções sem bloco;
- migração e carga PostgreSQL do piloto;
- banco histórico localizado e auditado;
- proveniência e auditoria técnica registradas.

### Ausente ou insuficiente

- testes automatizados;
- contratos JSON formais;
- pacote Python organizado;
- ledger geral de artefatos e transformações;
- separação correta entre blob e captura;
- modelo de matéria publicada;
- segmentação de atos;
- pessoas, organizações, cargos e ações administrativas;
- revisão humana e conjunto ouro;
- coletor de edições;
- inventário de cobertura;
- schemas `knowledge`, `analytics` e `audit`.

### Etapa atual

```text
Fase 0 concluída parcialmente
Fase 1 é o próximo trabalho executável
```

## 5. Fase 0 — Preservação e linha de base

Objetivo: impedir perda ou reinterpretação silenciosa do piloto original.

### Entregáveis

- [x] Preservar o ZIP ancestral e registrar SHA-256.
- [x] Importar o projeto sem reestruturar o código.
- [x] Verificar o hash do PDF contra o manifesto.
- [x] Reproduzir estrutura, Markdown e menções.
- [x] Consultar o banco histórico.
- [x] Registrar proveniência e auditoria técnica.
- [ ] Revisar os arquivos que entrarão no primeiro commit.
- [ ] Criar commit imutável da linha de base.
- [ ] Criar tag de recuperação, por exemplo `recovered-pilot-v1`.
- [ ] Definir política de versionamento de dados grandes e pacotes-fonte.

### Critério de saída

O histórico Git permite identificar exatamente o material recebido antes de
qualquer refatoração.

## 6. Fase 1 — Fundação reproduzível

Objetivo: transformar o protótipo em referência executável protegida por
testes.

### Engenharia

- [ ] Criar `pyproject.toml` e pacote em layout `src/`.
- [ ] Manter CLIs compatíveis durante a migração.
- [ ] Registrar ambiente de referência e lock de dependências.
- [ ] Adicionar lint, formatação, checagem de tipos e testes em CI.
- [ ] Criar comando único para processar e auditar a edição piloto.
- [ ] Parametrizar PostgreSQL, porta e credenciais.
- [ ] Remover `container_name` fixo do Compose.
- [ ] Criar `.env.example` sem segredos reais.

### Testes de regressão

- [ ] Congelar 85 páginas.
- [ ] Congelar 2.553 blocos.
- [ ] Congelar 179 blocos de ruído.
- [ ] Congelar 1.140 menções SEI.
- [ ] Congelar 1.096 valores únicos.
- [ ] Garantir zero menções órfãs.
- [ ] Conferir o hash do Markdown de referência.
- [ ] Testar reprocessamento idempotente.
- [ ] Testar banco criado do zero.
- [ ] Testar backup e restauração.

### Contratos

- [ ] Criar JSON Schema para manifesto.
- [ ] Criar JSON Schema para documento estrutural.
- [ ] Criar JSON Schema para menções.
- [ ] Validar inputs e outputs nos limites do pipeline.
- [ ] Definir política de compatibilidade e migração de schema.

### Critério de saída

Uma máquina limpa reproduz o DODF 112 com um comando, executa todos os testes e
produz relatório de auditoria sem intervenção manual.

## 7. Fase 2 — Ledger de evidências v2

Objetivo: criar a fundação correta antes de introduzir novas entidades.

### Modelo documental

- [ ] Separar `blob`, `document`, `capture` e `artifact`.
- [ ] Permitir múltiplas capturas apontando para os mesmos bytes.
- [ ] Criar `transformation_runs` para todas as transformações.
- [ ] Registrar hashes de entrada e saída, ferramenta, versão e parâmetros.
- [ ] Substituir caminhos absolutos por URIs ou caminhos portáveis.
- [ ] Corrigir referências redundantes de bloco em menções.
- [ ] Garantir integridade entre menção, bloco, página e captura.
- [ ] Registrar políticas e autoridade da fonte.

### Migração

- [ ] Criar migração v2 sem apagar o schema original.
- [ ] Migrar a edição 112.
- [ ] Comparar contagens e hashes antes/depois.
- [ ] Documentar rollback.

### Critério de saída

Todo artefato e registro derivado possui linhagem completa, e nenhuma forma de
deduplicação apaga eventos distintos de captura.

## 8. Fase 3 — Consumo semântico integral do DODF 112

Objetivo: tornar a edição individualizada e navegável.

### 8.1 Contexto editorial

- [ ] Identificar Seções I, II e III.
- [ ] Unir cabeçalhos quebrados em múltiplos blocos.
- [ ] Construir breadcrumbs editoriais.
- [ ] Separar contexto editorial de hierarquia institucional canônica.
- [ ] Classificar sumário, expediente, cabeçalhos, rodapés e conteúdo útil.

### 8.2 Matérias publicadas

- [ ] Criar `PublishedItem` como unidade geral.
- [ ] Segmentar início e fim de cada matéria.
- [ ] Permitir matérias que atravessam páginas.
- [ ] Classificar portaria, ordem de serviço, edital, aviso, extrato, ata,
  decisão, retificação e outros tipos.
- [ ] Preservar matéria não classificada sem descartá-la.
- [ ] Extrair número, data, título, órgão, unidade e autoridade.
- [ ] Relacionar retificação, republicação, revogação e referência entre
  matérias.

### 8.3 Dispositivos e ações

- [ ] Segmentar artigos, incisos, itens e parágrafos quando presentes.
- [ ] Localizar ações administrativas explícitas.
- [ ] Começar por `NOMEAR`, `EXONERAR`, `DESIGNAR`, `DISPENSAR`,
  `CESSAR OS EFEITOS`, `TORNAR SEM EFEITO` e `RETIFICAR`.
- [ ] Separar verbo, pessoa, cargo, órgão, data de efeito e processo.
- [ ] Manter ação textual distinta de evento consolidado.

### 8.4 Entidades prioritárias

- [ ] `PersonMention`.
- [ ] `OrganizationMention`.
- [ ] `PositionMention`.
- [x] `ProcessMention` inicial para SEI.
- [ ] Papéis de participação de pessoas e organizações.
- [ ] Datas tipadas: publicação, assinatura, efeito e vigência.

### 8.5 Referências complementares

- [ ] CNPJ com validação de dígitos.
- [ ] Empresas sem consolidação prematura.
- [ ] Normas e dispositivos citados.
- [ ] Contratos e instrumentos.
- [ ] Valores monetários e contexto.
- [ ] Matrículas e outros identificadores administrativos conforme política de
  privacidade.

### 8.6 Navegação da evidência

- [ ] Navegar edição → seção → contexto → matéria.
- [ ] Navegar matéria → ação → entidade.
- [ ] Navegar entidade → ocorrências → matérias.
- [ ] Navegar processo → matérias → entidades.
- [ ] Abrir página e destacar bbox ou span de origem.
- [ ] Mostrar texto literal, normalizado, regra e revisão.

### Critério de saída

Todo bloco útil pertence a uma matéria, contexto editorial ou categoria
documental explícita. Toda matéria e entidade prioritária pode ser aberta e
conferida visualmente no PDF.

## 9. Fase 4 — Conjunto ouro e qualidade da edição 112

Objetivo: transformar o DODF 112 em benchmark do projeto.

### Anotação e revisão

- [ ] Revisar manualmente as 85 páginas.
- [ ] Validar limites de todas as matérias.
- [ ] Validar contextos editoriais.
- [ ] Validar entidades prioritárias.
- [ ] Validar ações administrativas selecionadas.
- [ ] Registrar ambiguidades e desacordos.
- [ ] Versionar a anotação sem misturá-la com a saída automática.

### Métricas

- [ ] Precisão e recall da segmentação de matérias.
- [ ] Precisão e recall por tipo de entidade.
- [ ] Precisão e recall por tipo de ação.
- [ ] Taxa de entidades sem evidência: zero.
- [ ] Taxa de matérias sem contexto conhecido.
- [ ] Taxa de revisão pendente.
- [ ] Tempo e custo por página.

### Critério de saída

O DODF 112 é um conjunto ouro integral, com resultados automáticos comparáveis
a uma revisão humana e divergências explicitamente registradas.

## 10. Fase 5 — Dez edições representativas

Objetivo: provar que o sistema reconhece o DODF, não apenas uma edição.

### Seleção

Escolher uma amostra que contenha:

1. edição normal semelhante à referência;
2. edição extensa;
3. edição curta;
4. edição extra;
5. suplemento;
6. republicação ou correção;
7. layout difícil ou mudança tipográfica;
8. muitas tabelas;
9. PDF degradado ou parcialmente sem texto;
10. edição de período diferente.

### Execução

- [ ] Preservar e manifestar as dez edições.
- [ ] Criar amostras ouro por edição.
- [ ] Executar pipeline sem correções manuais nos derivados.
- [ ] Classificar falhas por fonte, estrutura, entidade e regra.
- [ ] Medir variação de layout e qualidade.
- [ ] Implementar OCR somente para páginas que falharem no teste textual.
- [ ] Produzir relatório comparativo.

### Critério de saída

As dez edições passam pelos mesmos contratos; exceções são modeladas como
variações explícitas, não como patches por nome de arquivo.

## 11. Fase 6 — Um mês completo

Objetivo: validar cobertura e operação contínua.

- [ ] Mapear o catálogo oficial.
- [ ] Criar inventário esperado por data, edição e tipo.
- [ ] Implementar adapter DODF retomável e idempotente.
- [ ] Registrar URL, headers, instante e política de captura.
- [ ] Distinguir normal, extra, suplemento e republicação.
- [ ] Implementar retries, rate limit e quarentena.
- [ ] Processar o mês completo.
- [ ] Publicar relatório de cobertura e lacunas.
- [ ] Medir reprocessamento integral.

### Critério de saída

O sistema informa o que esperava, encontrou, coletou, processou, rejeitou e não
conseguiu obter, sem converter ausência de coleta em ausência de publicação.

## 12. Fase 7 — Um ano completo

Objetivo: medir escala real antes de escolher infraestrutura maior.

- [ ] Processar um ano em lotes mensais fechados.
- [ ] Medir bytes, páginas, OCR e tempo por etapa.
- [ ] Medir crescimento do banco e dos derivados.
- [ ] Medir custo por mil páginas e milhão de menções.
- [ ] Medir mudanças de layout ao longo do ano.
- [ ] Executar restauração e reprocessamento completo.
- [ ] Avaliar necessidade real de object storage e busca dedicada.

### Critério de saída

Há um relatório de capacidade baseado em medições, não estimativas, e uma
decisão arquitetural registrada para a escala seguinte.

## 13. Fase 8 — DODF 2019–2026

Objetivo: construir o corpus histórico inicial.

- [ ] Dividir a cobertura em lotes mensais ou trimestrais.
- [ ] Fechar inventário e auditoria de cada lote.
- [ ] Registrar mudanças de fonte e layout.
- [ ] Preservar todas as capturas e republicações.
- [ ] Reprocessar derivados quando regras mudarem.
- [ ] Manter matriz pública de cobertura e qualidade.

### Critério de saída

O corpus 2019–2026 possui cobertura explícita, cadeia de custódia, qualidade
mensurada e possibilidade de reconstrução por lote.

## 14. Fase 9 — Base de conhecimento consolidado

Objetivo: relacionar o corpus sem apagar ambiguidade.

### Entidades

- [ ] Criar entidades canônicas com IDs estáveis.
- [ ] Manter menções e nomes originais.
- [ ] Consolidar empresas prioritariamente por CNPJ.
- [ ] Criar cadastro temporal de órgãos e unidades.
- [ ] Modelar mudanças de nome, fusão, cisão, criação e extinção.
- [ ] Adotar política conservadora para pessoas.

### Resolução

- [ ] Gerar candidatos com método e score.
- [ ] Preservar evidências favoráveis e contrárias.
- [ ] Criar fila de revisão humana.
- [ ] Medir false merge rate.
- [ ] Permitir desfazer qualquer decisão.

### Eventos

- [ ] Promover ações documentais validadas a eventos.
- [ ] Modelar participantes e papéis.
- [ ] Separar publicação, assinatura, vigência e efeito.
- [ ] Preservar conflitos entre eventos e fontes.

### Critério de saída

Toda entidade e evento consolidado pode ser explicado por decisões e evidências,
e nenhuma consolidação destrói as menções originais.

## 15. Fase 10 — Estado institucional temporal

Objetivo: reconstruir estados a partir de eventos documentados.

- [ ] Definir semântica de `valid_time` e `system_time`.
- [ ] Derivar ocupação de cargos e vigência de relações.
- [ ] Representar início ou fim desconhecido.
- [ ] Preservar intervalos abertos.
- [ ] Tratar retroatividade e republicação.
- [ ] Mostrar “não observado” em vez de afirmar inexistência.
- [ ] Versionar snapshots do conhecimento utilizado.

### Critério de saída

Uma resposta temporal pode ser percorrida até eventos, afirmações, matérias,
blocos e documentos que a sustentam.

## 16. Fase 11 — Base analítica e de inferências

Objetivo: produzir derivados analíticos sem contaminá-los com a evidência.

### Fundação

- [ ] Criar snapshots imutáveis de input.
- [ ] Definir contrato de inferência.
- [ ] Registrar proposição, método, versão, evidências e contraevidências.
- [ ] Registrar cobertura, confiança e incerteza.
- [ ] Classificar sensibilidade e publicabilidade.
- [ ] Implementar revisão e contestação.

### Primeiros produtos

- [ ] Contagens com denominador e cobertura explícitos.
- [ ] Recorrência de processos, entidades e atos.
- [ ] Mudanças de estrutura institucional.
- [ ] Sequências documentais auditáveis.
- [ ] Indicadores descritivos antes de inferências preditivas.

### Regra

O volume de dados não é, por si só, evidência de uma proposição. Toda inferência
deve indicar método, universo observado, lacunas e alternativas.

### Critério de saída

A base analítica pode ser descartada e reconstruída a partir de um snapshot; a
base de evidências permanece inalterada.

## 17. Fase 12 — Múltiplos Diários Oficiais

Objetivo: ampliar fontes sem perder a semântica local.

- [ ] Definir contrato de `SourceAdapter`.
- [ ] Implementar segundo Diário Oficial como prova de interoperabilidade.
- [ ] Preservar modelo nativo da fonte.
- [ ] Mapear para núcleo comum apenas quando semanticamente justificável.
- [ ] Separar jurisdição, autoridade e política por fonte.
- [ ] Comparar identificadores e entidades entre fontes.
- [ ] Avaliar terceiro e demais Diários por prioridade e qualidade.

Núcleo comum pretendido:

```text
SourceRecord
Document
Capture
PublishedItem
EvidenceSpan
EntityMention
AdministrativeAction
```

### Critério de saída

Uma nova fonte pode ser adicionada por adapter e extensão de domínio, sem
alterar o ledger de evidências das fontes existentes.

## 18. Projeções e experiência de navegação

Busca e interface evoluem junto com as fases, sem se tornarem banco mestre.

### Navegação mínima

- edição → seção → contexto → matéria;
- matéria → ação → entidade;
- entidade → ocorrências → documentos;
- processo → matérias → organizações e pessoas;
- resultado → evidências → posição visual no PDF.

### Projeções futuras

- full-text;
- timelines;
- grafos;
- dashboards;
- API de consulta;
- exports reproduzíveis.

Toda projeção deverá ser regenerável a partir das camadas mestres.

## 19. Governança transversal

Esta frente começa antes da coleta em escala e acompanha todas as fases.

- [ ] Registry de fontes, autoridade, licença e termos.
- [ ] Política de dados pessoais.
- [ ] Minimização e retenção.
- [ ] Política de correção e contestação.
- [ ] Classificação de inferências por risco.
- [ ] Logs de consultas e exportações sensíveis.
- [ ] Threat model.
- [ ] Backups criptografados e teste de recuperação.
- [ ] Política de acesso por camada.
- [ ] Revisão jurídica antes de usos sensíveis ou distribuição ampliada.

Princípio:

```text
pesquisa histórica por padrão;
inferência operacional por decisão explícita.
```

## 20. Métricas permanentes

### Cobertura

- documentos esperados, encontrados, coletados e processados;
- páginas e matérias por edição;
- lacunas por fonte e período.

### Proveniência

- percentual de registros com documento, página, bloco e span;
- percentual de derivados com execução e versão;
- registros órfãos.

### Qualidade

- precisão e recall por extrator;
- precisão de segmentação;
- false merge rate;
- divergências abertas e revisadas.

### Operação

- bytes por documento;
- segundos por página;
- páginas OCR/total;
- custo por mil páginas;
- tempo de reprocessamento;
- tempo de restauração;
- taxa de falhas e retries.

### Inferência

- cobertura do corpus utilizado;
- evidências e contraevidências por proposição;
- inferências revisadas, rejeitadas e contestadas;
- distribuição de confiança e sensibilidade.

## 21. Regras de passagem

Uma fase só pode ser encerrada quando:

1. seus entregáveis obrigatórios estiverem versionados;
2. testes e auditorias passarem;
3. métricas forem registradas;
4. falhas conhecidas estiverem documentadas;
5. riscos residuais forem aceitos explicitamente;
6. a decisão de avançar for registrada.

Não são critérios suficientes:

- “funcionou na minha máquina”;
- “as contagens parecem corretas”;
- “a interface ficou boa”;
- “o volume foi carregado”;
- “o modelo produziu uma resposta convincente”.

## 22. Próxima iteração executável

Escopo: Fase 0 final + início da Fase 1.

Ordem:

1. revisar e consolidar o commit da linha de base;
2. definir política de dados e arquivos grandes;
3. criar ambiente Python reproduzível;
4. transformar a reprodução manual em testes automatizados;
5. criar comando único de pipeline e auditoria;
6. criar os três JSON Schemas atuais;
7. testar banco limpo, idempotência, backup e restauração;
8. registrar decisão para iniciar o ledger v2.

### Marco de saída da próxima iteração

```text
Um comando processa o PDF original do DODF 112,
valida os contratos,
reproduz todos os artefatos,
carrega um banco limpo,
executa auditoria,
e encerra com testes verdes.
```

Somente depois começa a segmentação semântica integral das matérias do DODF
112.
