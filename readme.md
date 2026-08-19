# Memoria Institucional Navegavel

Este projeto organiza documentos publicos do Distrito Federal para que seja
possivel reconstruir, com evidencias, a historia institucional publicada em
fontes oficiais.

A regra central e simples:

```text
documento primeiro, interpretacao depois
```

Ou seja: antes de explicar qualquer coisa, o sistema precisa guardar o documento
original, mostrar de onde cada informacao saiu e permitir conferir a pagina e o
trecho usados como evidencia.

## O Que Ja Existe

Hoje o projeto ja consegue processar uma edicao do DODF em quatro camadas.

### 1. Arquivo bruto

Pasta: `data/raw/`

Aqui fica o PDF original. Ele e tratado como evidencia. A ideia e nunca alterar
esse arquivo.

Exemplo atual:

```text
data/raw/DODF 112 22-06-2026 INTEGRA.pdf
```

### 2. Manifesto

Pasta: `data/manifests/`

O manifesto e uma ficha tecnica do arquivo bruto. Ele guarda informacoes como:

- nome do arquivo;
- tamanho;
- quantidade de paginas;
- data de processamento;
- hash SHA-256.

O hash funciona como uma impressao digital do PDF. Se o arquivo mudar, o hash
muda tambem.

### 3. Estrutura do documento

Pasta: `data/structured/`

Aqui fica um JSON estrutural. Ele e uma versao organizada do PDF, preservando:

- paginas;
- blocos de texto;
- ordem de leitura;
- colunas;
- coordenadas do texto na pagina;
- texto original;
- texto normalizado.

Esse arquivo ainda nao interpreta nada. Ele so transforma o PDF em uma estrutura
mais facil de consultar.

### 4. Markdown para leitura humana

Pasta: `data/markdown/`

O Markdown e uma visualizacao mais confortavel para ler o conteudo extraido.
Ele nao e a fonte principal dos dados; a fonte principal derivada e o JSON
estrutural.

### 5. Extracoes

Pasta: `data/extractions/`

Aqui ficam achados objetivos localizados por regras. O primeiro extrator criado
busca numeros de processo SEI.

Cada mencao extraida guarda:

- tipo da mencao;
- valor como apareceu no documento;
- valor normalizado;
- pagina;
- bloco;
- trecho de contexto;
- regra que encontrou a mencao.

Isso permite conferir cada achado de volta no documento.

### 6. Projeção semântica navegável

O passe automático preserva a ligação com a evidência e organiza a edição por:

- seção e contexto editorial;
- matéria publicada e dispositivos `Art.`;
- ações administrativas prioritárias;
- menções de pessoas, órgãos e cargos;
- processos, CNPJs, valores monetários e referências normativas.

Essas observações não são promovidas automaticamente a entidades canônicas ou
eventos consolidados. A cobertura e os limites atuais estão documentados em
`docs/PHASE_3_AUTOMATIC_PASS_V1.md`.

### 7. Identidade material conservadora

A camada de identidade preserva cada menção como fragmento antes de qualquer
consolidação. Processos podem ser materializados pelo número SEI e organizações
legais por CNPJ válido. Pessoas, órgãos editoriais e cargos nunca são unidos
automaticamente apenas pelo nome.

O DODF 112 produz atualmente:

```text
1645 fragmentos
1276 entidades materiais
1342 ligações automáticas por identificador material
45 grupos candidatos mantidos separados
1 caso de resolução
```

A implementação, os limites e a matriz estão documentados em
`docs/MATERIAL_IDENTITY_V1.md`.

## Scripts Criados

Para instalar o ambiente e executar toda a edição piloto com um único comando,
consulte `docs/DEVELOPMENT.md`. A implementação vive no pacote `src/min_df`; os
arquivos em `scripts/` preservam compatibilidade com os comandos históricos.

### `scripts/dodf_to_markdown.py`

Le o PDF do DODF e gera:

- manifesto;
- JSON estrutural;
- Markdown.

Uso atual:

```powershell
python scripts\dodf_to_markdown.py "data\raw\DODF 112 22-06-2026 INTEGRA.pdf" --page-markers
```

### `scripts/extract_mentions.py`

Le o JSON estrutural e extrai mencoes objetivas. Por enquanto, extrai numeros
de processo SEI.

Uso atual:

```powershell
python scripts\extract_mentions.py "data\structured\DODF 112 22-06-2026 INTEGRA.structured.json"
```

Resultado validado na edicao atual:

```text
1140 mencoes de processos SEI
1096 processos SEI unicos
```

### `scripts/load_to_postgres.py`

Prepara e executa a carga idempotente dos dados no PostgreSQL configurado.

Sem banco, ja da para validar se os arquivos combinam entre si:

```powershell
python scripts\load_to_postgres.py --dry-run --manifest "data\manifests\DODF 112 22-06-2026 INTEGRA.manifest.json" --structured "data\structured\DODF 112 22-06-2026 INTEGRA.structured.json" --mentions "data\extractions\DODF 112 22-06-2026 INTEGRA.mentions.json"
```

Resultado validado:

```text
85 paginas
2553 blocos
1140 mencoes
0 mencoes sem bloco correspondente
```

## Banco De Dados

Pasta: `db/migrations/`

Existem quatro migrações incrementais:

```text
db/migrations/001_initial_schema.sql
db/migrations/002_evidence_ledger_v2.sql
db/migrations/003_semantic_navigation.sql
db/migrations/004_material_identity.sql
```

Ela define tabelas para guardar:

- fontes;
- documentos;
- capturas dos documentos;
- paginas;
- blocos;
- rodadas de extracao;
- mencoes extraidas.

O objetivo do banco nao e explicar os fatos. O objetivo inicial e guardar
evidencias e relacoes verificaveis.

### Como ligar o PostgreSQL local

O banco local roda em Docker. Para ligar:

```powershell
.\scripts\db_up.ps1
```

Para criar as tabelas:

```powershell
.\scripts\db_migrate.ps1
```

Para carregar a edicao piloto:

```powershell
.\scripts\db_load_pilot.ps1
```

Para conferir os totais gravados:

```powershell
.\scripts\db_counts.ps1
```

Resultado atual no PostgreSQL:

```text
sources: 1
documents: 1
document_captures: 1
document_pages: 85
document_blocks: 2553
extraction_runs: 1
mentions: 1140
```

As mencoes carregadas hoje sao:

```text
processo_sei: 1140 mencoes, 1096 valores unicos
```

## Situacao Atual

O projeto ja tem um piloto de uma edicao do DODF:

```text
PDF -> manifesto -> JSON estrutural -> Markdown -> mencoes SEI -> PostgreSQL
```

Também existe um explorador web para analisar como esses dados foram formados:

```powershell
.\scripts\web_up.ps1
```

Ele oferece navegação por matérias, entidades, ações, processos e referências,
sempre exibindo a evidência documental correspondente.

O passe automático do DODF 112 e a identidade material v1 estão implementados.
O projeto está agora no portão de qualidade: construir anotação humana, medir
precisão, recall e false merge rate e revisar a edição antes de ampliar o corpus.

A ordem cautelosa é:

```text
congelar benchmark automático
→ revisar amostra estratificada
→ medir e corrigir
→ revisar as 85 páginas
→ validar identidade e temporalidade
→ adaptar a interface de revisão
→ testar dez edições representativas
```

CPF, matrícula, expansão para um mês e inferências permanecem bloqueados até os
respectivos portões de qualidade e governança.

O contrato `human-annotation/1.0`, os templates e o guia de calibração já estão
disponíveis em `annotations/` e `docs/ANNOTATION_GUIDE_DODF.md`. Um lote pode ser
validado com:

```powershell
python -m min_df.annotation caminho\para\lote.json
```

## Roadmap

A trajetória geral está em:

```text
docs/ROADMAP_CONSOLIDATED.md
```

O passo a passo vigente está em:

```text
docs/PLANO_DE_PROSSEGUIMENTO.md
```

`ROADMAP.md` permanece como backlog estratégico por domínio.
