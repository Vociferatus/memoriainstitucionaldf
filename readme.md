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

Foi criada a primeira migracao SQL:

```text
db/migrations/001_initial_schema.sql
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

O próximo passo é ampliar a cobertura semântica da Fase 3, construir o conjunto
ouro e medir precisão e recall antes de consolidar inferências.

## Roadmap

A lista principal de acoes esta em:

```text
ROADMAP.md
```

Ela deve ser tratada como a lista viva do projeto.
