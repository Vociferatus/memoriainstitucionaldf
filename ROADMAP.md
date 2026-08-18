# Memoria Institucional Navegavel - Roadmap

## Proposito

Consumir, preservar, estruturar e consolidar documentos publicos para permitir a
reconstrucao auditavel da historia institucional do Distrito Federal.

O sistema produz observacoes verificaveis, nao interpretacoes. Todo dado
derivado deve apontar para o documento, a pagina e, quando possivel, o trecho
que lhe deu origem.

## Principios inegociaveis

- [ ] Documento e evidencia.
- [ ] Nada existe sem fonte.
- [ ] Todo fato e rastreavel ao documento.
- [ ] Dados brutos sao imutaveis e permanentes.
- [ ] Transformacoes sao reproduziveis e versionadas.
- [ ] Ontologia pode evoluir sem apagar o historico.
- [ ] Interpretacoes, quando existirem, ficam separadas dos dados observados.
- [ ] Ausencia de dado nao e evidencia de ausencia.

## Estado atual

- [x] Repositorio local criado.
- [x] Primeiro PDF textual do DODF preservado em `data/raw/`.
- [x] Conversor inicial de PDF para Markdown criado.
- [x] Conversor validado em uma edicao de 85 paginas.
- [x] Manifesto SHA-256 inicial gerado para uma edicao.
- [x] JSON estrutural inicial gerado para uma edicao.
- [x] Primeiro extrator deterministico criado para numeros de processo SEI.
- [x] Migracao SQL inicial criada para PostgreSQL.
- [x] Carregador inicial para PostgreSQL criado.
- [x] Auditor simples de artefatos criado para conferir uma edicao processada.
- [x] PostgreSQL local configurado via Docker.
- [x] Primeira edicao carregada no PostgreSQL.
- [ ] Convencoes de armazenamento e identificacao definidas.
- [x] Banco de dados e esquema inicial criados.
- [ ] Coletor historico do DODF criado.
- [ ] Conjunto inicial de extratores deterministas criado.

## Definicao do MVP

Cobertura inicial: DODF de 2019 a 2026.

Fluxo inicial:

```text
PDF -> estrutura documental -> extracao -> consolidacao -> PostgreSQL
```

Entidades e referencias inicialmente extraidas:

- processos;
- atos administrativos;
- orgaos;
- empresas;
- pessoas;
- normas.

Fora do MVP inicial:

- explicacoes causais;
- classificacao generativa por IA;
- inferencias sem regra explicita;
- interface publica definitiva;
- ingestao completa de todas as fontes simultaneamente.

## Arquitetura de proveniencia

Cada artefato derivado deve registrar, no minimo:

- identificador estavel do documento;
- fonte e URL original;
- data e hora da coleta;
- hash criptografico do arquivo bruto;
- tipo e tamanho do arquivo;
- versao do coletor ou transformador;
- pagina e coordenadas do trecho, quando disponiveis;
- regra e versao da regra que produziram a extracao;
- data e hora da transformacao.

Os arquivos brutos nunca devem ser sobrescritos. Uma nova versao publicada na
origem deve ser armazenada como nova captura, mesmo que use o mesmo nome.

## Etapa 0 - Fundacoes do projeto

Objetivo: tornar o trabalho reproduzivel antes da coleta em escala.

- [ ] Definir nomenclatura de arquivos e identificadores de documentos.
- [ ] Definir diretorios para `raw`, metadados, estrutura, extracoes e logs.
- [ ] Separar arquivos versionaveis de grandes dados locais no `.gitignore`.
- [ ] Escolher estrategia de preservacao dos brutos: disco, objeto remoto e backup.
- [ ] Definir hashes, inicialmente SHA-256, e manifesto de ingestao.
- [ ] Definir configuracao por ambiente e gerenciamento de segredos.
- [ ] Criar logging estruturado e relatorio de falhas.
- [ ] Criar testes automatizados e amostras pequenas versionadas.
- [ ] Documentar instalacao, execucao e recuperacao do pipeline.
- [ ] Registrar versoes de Python e PostgreSQL suportadas.

**Criterio de conclusao:** uma pessoa consegue reproduzir a ingestao e a
transformacao de uma edicao de exemplo sem alterar manualmente os dados.

## Etapa 1 - Inventario e aquisicao das fontes

Objetivo: descobrir como obter os dados, sua cobertura e suas restricoes antes
de implementar todos os coletores.

### DODF - prioridade do MVP

- [ ] Localizar catalogo oficial e mecanismo de consulta historica.
- [ ] Verificar cobertura real entre 2019 e 2026.
- [ ] Identificar edicoes normais, extras, suplementos e republicacoes.
- [ ] Verificar se ha API, indice ou padrao estavel de URLs.
- [ ] Registrar formatos, tamanhos, falhas e PDFs sem camada textual.
- [ ] Verificar termos de uso, limites de acesso e politica de robots.
- [ ] Criar inventario esperado de edicoes por data e tipo.
- [ ] Criar coletor retomavel, com limite de requisicoes e novas tentativas.
- [ ] Detectar duplicatas por hash, sem descartar metadados de origem.
- [ ] Comparar inventario esperado com arquivos efetivamente coletados.

### SINJ

- [ ] Mapear consulta, filtros, identificadores e documentos disponiveis.
- [ ] Determinar cobertura temporal e historico de alteracoes normativas.
- [ ] Verificar API, exportacao ou necessidade de coleta de paginas.
- [ ] Avaliar como relacionar normas do SINJ com citacoes no DODF.

### Dados Abertos DF / CKAN

- [ ] Inventariar organizacoes, conjuntos, recursos e APIs.
- [ ] Preservar metadados CKAN alem dos arquivos publicados.
- [ ] Detectar atualizacoes, substituicoes e recursos indisponiveis.
- [ ] Definir quais conjuntos apoiam o MVP e quais ficam para depois.

### Transparencia, contratos e convenios

- [ ] Identificar portais, endpoints, relatorios e formatos de exportacao.
- [ ] Mapear chaves de ligacao: processo, CNPJ, contrato, convenio e unidade.
- [ ] Avaliar cobertura, granularidade, atualizacao e dados pessoais.
- [ ] Registrar restricoes legais e operacionais por fonte.

**Criterio de conclusao:** cada fonte possui uma ficha com acesso, cobertura,
licenca, formatos, chaves, limitacoes e uma decisao de prioridade.

## Etapa 2 - Ingestao imutavel do DODF

Objetivo: preservar todas as edicoes do escopo com prova de integridade.

- [ ] Criar modelo de manifesto de documento e captura.
- [ ] Implementar download atomico e retomavel.
- [ ] Validar assinatura, tamanho e legibilidade basica de cada PDF.
- [ ] Calcular SHA-256 e registrar metadados HTTP.
- [ ] Distinguir documento logico de suas diferentes capturas/versoes.
- [ ] Classificar edicao normal, extra, suplemento ou republicacao.
- [ ] Criar fila de falhas e comando de reprocessamento.
- [ ] Produzir relatorio de cobertura por data e tipo de edicao.
- [ ] Executar coleta piloto de um mes.
- [ ] Auditar o piloto antes da coleta de 2019-2026.
- [ ] Executar coleta historica em lotes verificaveis.

**Criterio de conclusao:** o inventario informa o que existe, o que foi
coletado, o que falhou e o hash de cada captura.

## Etapa 3 - Estruturacao documental

Objetivo: representar o conteudo do PDF sem interpretacao administrativa.

- [ ] Definir JSON estrutural canonico antes de usar Markdown como dado mestre.
- [ ] Preservar pagina, bloco, linha, coluna, coordenadas e ordem de leitura.
- [ ] Preservar texto original e texto normalizado separadamente.
- [ ] Preservar secoes, titulos, tabelas e imagens detectadas.
- [ ] Detectar PDF textual versus PDF que exige OCR.
- [ ] Implementar caminho de OCR sem substituir o arquivo original.
- [ ] Registrar confianca e mecanismo de obtencao de cada trecho.
- [ ] Tratar cabecalhos, rodapes, hifenizacao e quebras entre paginas.
- [ ] Gerar Markdown como visualizacao derivada do JSON estrutural.
- [ ] Montar conjunto ouro com paginas representativas e anotacao manual.
- [ ] Medir ordem de leitura, perda textual e segmentacao no conjunto ouro.
- [ ] Versionar o transformador e permitir reprocessamento integral.

**Criterio de conclusao:** qualquer trecho estruturado pode ser localizado
visualmente no PDF, e a qualidade e medida em uma amostra conhecida.

## Etapa 4 - Extracao determinista

Objetivo: localizar mencoes por regex, dicionarios e regras explicitas.

- [ ] Definir contrato comum de extracao e evidencias.
- [ ] Extrair numeros de processos SEI e normalizar sua representacao.
- [ ] Extrair CNPJ e validar digitos verificadores.
- [ ] Extrair CPF apenas quando necessario e permitido, com politica de acesso.
- [ ] Extrair valores com moeda e contexto imediato.
- [ ] Extrair referencias a normas, artigos e atos.
- [ ] Extrair nomes de orgaos por dicionario temporal versionado.
- [ ] Extrair pessoas e empresas sem consolidar identidades prematuramente.
- [ ] Classificar tipos de atos por padroes de titulo e formula normativa.
- [ ] Guardar texto, pagina, coordenadas, regra e versao para cada mencao.
- [ ] Criar testes positivos, negativos e casos ambiguos para cada extrator.
- [ ] Medir precisao e cobertura no conjunto ouro.

**Criterio de conclusao:** toda mencao extraida possui evidencia e pode ser
reproduzida pela mesma versao da regra.

## Etapa 5 - Banco e modelo inicial

Objetivo: persistir documentos e extracoes sem confundir mencao, entidade,
evento e fato.

Tabelas candidatas:

- `sources`;
- `documents`;
- `document_captures`;
- `document_sections`;
- `document_blocks`;
- `extraction_runs`;
- `mentions`;
- `entities`;
- `entity_aliases`;
- `processes`;
- `events`;
- `facts`;
- `relationships`;
- `evidence_links`.

Acoes:

- [ ] Modelar documento logico separado de captura e arquivo.
- [ ] Modelar mencao separada de entidade consolidada.
- [ ] Tornar proveniencia obrigatoria por restricoes do banco.
- [ ] Adotar intervalos temporais com inicio e fim possivelmente desconhecidos.
- [ ] Preservar valores originais junto aos valores normalizados.
- [ ] Definir IDs internos estaveis, sem usar nomes como chave primaria.
- [ ] Criar migracoes de banco versionadas.
- [ ] Criar indices para documento, processo, CNPJ, data e tipo de evento.
- [ ] Definir politica de exclusao: derivados podem ser refeitos; brutos nao.
- [ ] Testar carga, reprocessamento idempotente e reversao de derivacoes.

**Criterio de conclusao:** reprocessar um documento nao duplica registros e
nenhum fato existe sem ligacao de evidencia.

## Etapa 6 - Consolidacao de entidades

Objetivo: relacionar mencoes equivalentes sem apagar ambiguidade ou historia.

- [ ] Definir consolidacao exata por identificadores oficiais quando existirem.
- [ ] Criar cadastro temporal de orgaos, siglas e denominacoes.
- [ ] Representar criacao, extincao, fusao, cisao e recriacao de orgaos.
- [ ] Tratar mudanca de nome separadamente de identidade institucional.
- [ ] Consolidar empresas prioritariamente por CNPJ.
- [ ] Definir politica conservadora para pessoas homonimas.
- [ ] Registrar regra, evidencia, confianca e responsavel por cada vinculo.
- [ ] Manter fila de casos ambiguos para revisao humana.
- [ ] Permitir desfazer uma consolidacao sem perder as mencoes originais.
- [ ] Criar testes historicos para siglas e orgaos que mudaram no tempo.

**Criterio de conclusao:** cada consolidacao e explicavel, reversivel e nao
transforma similaridade nominal em identidade automaticamente.

## Etapa 7 - Eventos e fatos observaveis

Objetivo: representar verbos administrativos explicitamente publicados.

- [ ] Definir diferenca operacional entre mencao, evento, fato e relacionamento.
- [ ] Comecar por poucos eventos de alta precisao.
- [ ] Modelar nomeacao, exoneracao, designacao e dispensa.
- [ ] Modelar credenciamento, descredenciamento e revogacao.
- [ ] Modelar contratacao, aditamento, rescisao e resultado.
- [ ] Preservar verbo e texto administrativo original.
- [ ] Relacionar sujeito, objeto, processo, norma, orgao, data e evidencia.
- [ ] Representar datas desconhecidas e efeitos retroativos sem inventar valores.
- [ ] Distinguir data de publicacao, assinatura, vigencia e efeito.
- [ ] Criar validacoes por tipo de evento sem exigir campos ausentes na fonte.
- [ ] Avaliar cada novo tipo no conjunto ouro antes de ampliar a coleta.

**Criterio de conclusao:** eventos selecionados podem ser reconstruidos desde o
banco ate o trecho e a pagina do documento original.

## Etapa 8 - Observacoes e consultas

Objetivo: responder perguntas descritivas com universo e metodo explicitos.

- [ ] Definir consultas de controle antes das perguntas analiticas.
- [ ] Contar credenciamentos por periodo, orgao e regra de classificacao.
- [ ] Listar empresas por numero de mencoes e por numero de eventos distintos.
- [ ] Identificar normas mais citadas, alteradas ou revogadas.
- [ ] Identificar processos recorrentes e documentos em que aparecem.
- [ ] Exibir denominador, cobertura documental e lacunas em toda contagem.
- [ ] Permitir abrir as evidencias que compoem cada resultado agregado.
- [ ] Exportar consultas com data, versao do banco e parametros.
- [ ] Impedir que observacao derivada seja apresentada como causalidade.

**Criterio de conclusao:** resultados agregados sao reproduziveis e permitem
inspecao de todos os registros e documentos que os sustentam.

## Etapa 9 - Navegacao e sequencias institucionais

Objetivo: navegar por encadeamentos documentados, sem inferir causalidade.

- [ ] Consultar sequencias por processo, entidade, norma e intervalo temporal.
- [ ] Exibir `Norma -> Ato -> Credenciamento -> Contrato -> Resultado` quando
      cada ligacao estiver documentada.
- [ ] Diferenciar ligacao explicita, consolidacao e simples proximidade temporal.
- [ ] Mostrar lacunas e elos ainda sem evidencia.
- [ ] Criar linha do tempo com versoes institucionais e vigencias.
- [ ] Permitir exportacao da sequencia e de suas evidencias.
- [ ] Avaliar a pergunta fundadora como estudo de caso, sem assumir sua premissa.

**Criterio de conclusao:** uma sequencia pode ser auditada elo a elo e nenhum
elo e apresentado como causal sem uma fonte que o declare.

## Questoes em aberto

- [ ] Qual e o catalogo oficial e completo de edicoes do DODF?
- [ ] Existem edicoes corrigidas no mesmo URL ou com o mesmo identificador?
- [ ] Qual proporcao dos PDFs de 2019-2026 exige OCR?
- [ ] Markdown sera apenas visualizacao ou tambem interface de revisao humana?
- [ ] Qual armazenamento de longo prazo recebera os arquivos brutos?
- [ ] Quais dados pessoais serao armazenados, mascarados ou restringidos?
- [ ] Qual definicao operacional separa `event` de `fact`?
- [ ] Como representar contradicoes entre documentos oficiais?
- [ ] Como versionar cadastros temporais de orgaos e suas competencias?
- [ ] Qual metrica minima de precisao autoriza um extrator a entrar em producao?
- [ ] Quais observacoes precisam de revisao humana antes de publicacao?
- [ ] Qual sera o mecanismo de citacao persistente de pagina e trecho?

## Riscos principais

- Mudancas ou bloqueios nos portais de origem.
- Cobertura historica incompleta ou nao documentada.
- PDFs digitalizados, corrompidos ou com ordem textual incorreta.
- Republicacoes e duplicatas tratadas incorretamente como um unico documento.
- Consolidacao indevida de homonimos, siglas ou orgaos recriados.
- Vazamento ou exposicao desnecessaria de dados pessoais.
- Mudancas ontologicas que tornem derivados antigos incomparaveis.
- Contagens apresentadas sem informar lacunas do corpus.
- Confusao entre sequencia temporal, relacao documental e causalidade.

## Proxima iteracao recomendada

Escopo: transformar o prototipo atual em um piloto auditavel de uma edicao e,
em seguida, de um mes completo.

- [x] Definir uma primeira versao do JSON estrutural canonico.
- [x] Adaptar `dodf_to_markdown.py` para gerar JSON e Markdown derivado.
- [x] Criar manifesto SHA-256 para o PDF de exemplo.
- [x] Implementar o primeiro extrator: numero de processo SEI.
- [x] Criar esquema PostgreSQL minimo para documento, bloco e mencao.
- [x] Criar carregador inicial para manifesto, estrutura e mencoes.
- [x] Criar auditor simples para conferir consistencia dos artefatos.
- [x] Carregar uma edicao de ponta a ponta.
- [ ] Selecionar paginas representativas para o conjunto ouro.
- [ ] Escrever testes de ordem de leitura e rastreabilidade.
- [ ] Auditar manualmente os resultados e registrar erros.
- [ ] Pesquisar o catalogo oficial para montar o inventario de um mes.
- [ ] Coletar e processar o mes piloto.
- [ ] Decidir o que precisa mudar antes da coleta historica.

## Registro de decisoes

Decisoes arquiteturais devem ser registradas em `docs/decisions/` quando esse
diretorio for criado. Cada registro deve conter contexto, alternativas, decisao,
consequencias e data. Questoes ainda sem evidencia permanecem neste roadmap e
nao devem ser convertidas silenciosamente em decisoes.

## Regra de execucao

Priorizar sempre:

```text
consumir -> preservar -> estruturar -> consolidar
```

Antes de:

```text
inferir -> explicar -> interpretar
```
