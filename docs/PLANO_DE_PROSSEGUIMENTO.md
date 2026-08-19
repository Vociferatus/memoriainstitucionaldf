# Plano de prosseguimento cauteloso

Versão: 1.0
Data: 2026-08-18
Estado: plano executivo vigente.

## 1. Objetivo

Concluir uma edição do DODF com qualidade conhecida antes de aumentar o corpus.
Executar uma etapa com sucesso técnico não autoriza a etapa seguinte: cada avanço
depende de evidência, métricas, riscos residuais registrados e decisão explícita.

Este documento é o plano operacional imediato. O roadmap consolidado continua a
descrever a trajetória completa do projeto.

## 2. Posição atual

O DODF 112 possui cadeia técnica completa até a identidade material v1:

```text
PDF → estrutura → menções → matérias e ações → fragmentos de identidade
    → entidades materiais → PostgreSQL → projeções navegáveis
```

O resultado automático está reproduzido e protegido por testes, mas ainda não foi
comparado integralmente com uma anotação humana. Portanto:

- a fundação técnica está verificada;
- a cobertura automática é conhecida;
- a acurácia semântica ainda não é conhecida;
- a identidade material v1 é uma fundação antecipada da futura base de
  conhecimento, não a conclusão da consolidação histórica;
- a expansão para dez edições permanece bloqueada pelo portão de qualidade do
  DODF 112.

## 3. Regras de execução

1. Não alterar artefatos de referência manualmente para fazer métricas passarem.
2. Anotação humana e saída automática são artefatos distintos.
3. Correções são feitas em regras versionadas e exigem reprocessamento integral.
4. Nomes nunca são usados, sozinhos, para unir pessoas ou organizações.
5. Um falso merge material interrompe a expansão de identidade até análise.
6. Toda métrica informa universo, versão, itens excluídos e motivo da exclusão.
7. Toda exceção de layout é uma regra geral ou uma variação documentada; nunca um
   patch pelo nome do arquivo.
8. A interface ajuda a revisar, mas não se torna fonte de verdade.
9. Dados pessoais adicionais só entram após política de acesso e minimização.
10. Inferências permanecem fora do escopo até o corpus e a qualidade estarem
    explícitos.

## 4. Passo a passo vigente

### Passo 0 — Integrar e congelar o marco automático

- revisar e integrar a PR da identidade material v1;
- criar tag ou registro de versão do benchmark automático;
- executar pipeline, banco e CI a partir de checkout limpo;
- registrar hashes, contagens, versões e limitações conhecidas;
- alinhar README, roadmaps e documentos de fase.

**Portão 0:** todos os checks verdes, árvore limpa, carga idempotente e baseline
automático identificável por commit.

### Passo 1 — Validar por revisão assistida e risco

Estado atual:

- [x] contrato `human-annotation/1.0` criado;
- [x] modos cego, independente, assistido e adjudicação separados;
- [x] guia 1.0 criado como rascunho de calibração;
- [x] templates válidos e validador de lote criados;
- [x] páginas 37 e 51 congeladas para calibração;
- [x] interface cega criada com PDF primário, localizador de blocos e exportação
  `human-annotation/1.0`;
- [x] fila assistida inicial gerada com casos críticos, alto risco, amostra
  aleatória e amostra negativa;
- [x] interface de decisões rápidas criada;
- [ ] revisar os casos críticos e uma amostra de 60–100 decisões;
- [ ] medir precisão, omissões, tempo por decisão e risco residual;
- [ ] converter erros dominantes em testes e reprocessar.

- criar contrato versionado para anotação humana;
- definir rótulos, campos obrigatórios e estados `confirmado`, `rejeitado`,
  `ausente`, `ambíguo` e `não aplicável`;
- escrever guia com exemplos positivos, negativos e limítrofes;
- definir como anotar limites de matéria, contexto, pessoa, organização, cargo,
  ação, processo, CNPJ, norma e datas;
- separar desacordo de anotação, erro de fonte e erro do extrator;
- definir amostragem, segunda revisão e adjudicação.

**Portão 1:** todos os casos críticos foram decididos, a amostra aleatória e
negativa permite estimar precisão e omissões, os erros encontrados viraram
testes e o risco residual está documentado. A anotação cega permanece disponível
como instrumento opcional, não como obrigação operacional.

### Passo 2 — Revisar uma amostra estratificada

Selecionar inicialmente 12 páginas, sem escolher apenas páginas fáceis:

- páginas das três seções;
- início, meio e fim da edição;
- matéria curta e matéria multipágina;
- ações de pessoal;
- licitação, contrato ou resultado;
- tabela ou diagramação difícil;
- página com muitos processos, normas ou valores;
- cabeçalhos organizacionais simples e profundos.

Executar a anotação sem consultar a classificação automática quando isso for
viável. Fazer segunda revisão de pelo menos 20% da amostra.

**Portão 2:** guia estabilizado, taxonomia de erros criada e nenhum erro crítico
sem estratégia de correção.

### Passo 3 — Medir e corrigir por categoria

Produzir matriz de confusão e métricas por tipo, nunca apenas uma média global.
Para cada falha:

1. localizar a evidência;
2. classificar a causa;
3. decidir se é regra, estrutura, anotação, fonte ou ambiguidade real;
4. adicionar teste positivo e negativo;
5. versionar a correção;
6. reprocessar a edição inteira;
7. comparar com o baseline anterior.

Metas iniciais para autorizar a revisão integral:

| Medida | Meta mínima |
|---|---:|
| Registros derivados com documento, página, bloco e span | 100% |
| Registros órfãos | 0 |
| Precisão dos limites de matéria | ≥ 98% |
| Recall dos limites de matéria | ≥ 98% |
| Precisão das entidades prioritárias | ≥ 95% |
| Recall das entidades prioritárias | ≥ 90% |
| Precisão das ações prioritárias | ≥ 95% |
| Recall das ações prioritárias | ≥ 90% |
| Auto-links sem identificador material válido | 0 |
| Falsos merges materiais conhecidos | 0 |

As metas podem mudar somente por decisão registrada, com justificativa e impacto.

**Portão 3:** metas alcançadas na amostra ou exceções explicitamente rejeitadas,
corrigidas ou aceitas por ADR.

### Passo 4 — Construir o conjunto ouro integral do DODF 112

- revisar as 85 páginas;
- validar as 457 matérias e seus limites;
- revisar contextos editoriais e breadcrumbs;
- revisar entidades, ações e referências prioritárias;
- registrar omissões, falsos positivos, ambiguidades e desacordos;
- realizar segunda revisão de pelo menos 20% do conjunto e 100% dos casos de
  identidade ou divergência;
- adjudicar os desacordos sem sobrescrever as anotações originais;
- publicar relatório de precisão, recall, custo e tempo por página.

**Portão 4:** conjunto ouro versionado, métricas reproduzíveis, zero evidências
órfãs e riscos residuais aceitos explicitamente.

### Passo 5 — Validar a identidade material e a temporalidade

- revisar todos os grupos candidatos de pessoa e organização;
- revisar todos os casos de resolução;
- validar cada regra de `AUTO_LINK` contra o conjunto ouro;
- registrar evidências favoráveis, contrárias e ausentes;
- modelar publicação, assinatura, vigência e efeito separadamente;
- introduzir `valid_time` e `system_time` antes de derivar ocupações ou estados;
- testar desfazer, rejeitar e reabrir decisões sem perder fragmentos.

**Portão 5:** false merge rate conhecido e igual a zero no conjunto revisado;
decisões reversíveis; divergências navegáveis e temporalmente explicáveis.

### Passo 6 — Formalizar governança de dados pessoais

Antes de CPF, matrícula ou identificadores equivalentes:

- definir finalidade e necessidade de cada campo;
- classificar sensibilidade e publicabilidade;
- aplicar minimização, mascaramento e controle de acesso;
- definir retenção, logs, correção e contestação;
- realizar revisão jurídica antes de distribuição ampliada.

**Portão 6:** política aprovada e implementável; nenhum identificador sensível é
publicado apenas porque apareceu no Diário Oficial.

### Passo 7 — Atualizar a experiência de revisão e navegação

O frontend deverá separar visualmente:

- menção observada;
- fragmento de identidade;
- entidade material;
- grupo candidato;
- decisão e versão;
- caso de resolução;
- divergência e cadeia de análise;
- evidência documental e posição no PDF.

Primeiro será construída a interface de revisão; a apresentação pública virá
depois que estados, permissões e linguagem de incerteza estiverem validados.

**Portão 7:** nenhuma tela apresenta candidato como entidade confirmada, nem
ausência de observação como inexistência.

### Passo 8 — Selecionar dez edições representativas

Congelar a seleção antes de examinar resultados, cobrindo edição normal, extra,
suplemento, republicação, tamanhos distintos, tabelas, PDF degradado e período
diferente. Executar o mesmo pipeline sem correções específicas por arquivo.

Para cada edição:

- preservar e manifestar;
- processar em checkout limpo;
- anotar amostra ouro;
- medir as mesmas categorias do DODF 112;
- classificar regressões e variações de layout;
- registrar tempo, bytes, páginas, falhas e necessidade de OCR.

**Portão 8:** contratos comuns aprovados nas dez edições, qualidade dentro das
metas ou lacunas documentadas, e nenhuma regra especial baseada no nome do PDF.

### Passo 9 — Autorizar um mês completo

Somente após o Portão 8:

- mapear catálogo oficial e inventário esperado;
- implementar captura retomável, retries, rate limit e quarentena;
- distinguir edição normal, extra, suplemento e republicação;
- processar um mês fechado;
- publicar cobertura, lacunas, custos e reprocessamento.

**Portão 9:** o sistema distingue o que esperava, encontrou, coletou, processou,
rejeitou e não conseguiu obter.

## 5. Condições de parada

O trabalho de expansão deve parar e voltar à etapa apropriada quando ocorrer:

- qualquer falso merge de pessoa ou organização;
- perda de vínculo entre derivado e evidência;
- alteração de bytes brutos;
- queda de métrica abaixo do limiar aprovado;
- nova classe de layout sem tratamento explícito;
- divergência de contagens sem explicação;
- inclusão de dado sensível sem política;
- necessidade de correção manual em artefato derivado;
- resultado agregado sem denominador ou cobertura;
- inferência apresentada como fato observado.

Parar não significa fracasso: significa impedir que um erro local se transforme
em história institucional falsa em escala.

## 6. Registro mínimo de cada passagem

Cada portão deverá produzir:

- commit e versão dos contratos;
- artefatos e hashes relevantes;
- comandos executados;
- resultado dos testes e auditorias;
- métricas e universo avaliado;
- falhas conhecidas;
- riscos residuais;
- decisão explícita: `APROVADO`, `APROVADO COM RESSALVAS` ou `REPROVADO`;
- responsável e data da decisão.

## 7. Próxima ação autorizada

Executar o **Passo 0** e, depois, iniciar o contrato e o guia de anotação do
**Passo 1**. A coleta de dez edições, o uso de novos identificadores pessoais e
qualquer camada de inferência permanecem bloqueados pelos portões correspondentes.
