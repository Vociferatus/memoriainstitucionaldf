# Proveniência da linha de base

Data da consolidação: 2026-08-18.

## Origem

O conteúdo inicial deste repositório foi importado, sem reestruturação, do
pacote ancestral preservado em:

```text
source-packages/Historia-Institucional-do-DF-original-2026-06-27.zip
```

SHA-256 do pacote:

```text
4FB61581FA375BFADA32952E38318784B5535D2469823081915252DA65359BC7
```

O ZIP possuía uma raiz chamada `História Institucional do DF/`. Seu conteúdo
foi importado para a raiz deste repositório. Os diretórios vazios `.git/` e
`.agents/` presentes no ZIP não foram importados. Nenhum arquivo do projeto
colidiu com arquivo preexistente durante a importação.

## Evidência documental do piloto

Documento:

```text
data/raw/DODF 112 22-06-2026 INTEGRA.pdf
```

- tamanho: `2.041.246` bytes;
- páginas: `85`;
- SHA-256:
  `17389d23375c9b9b747c8a0f74305ce20ee4b52dbc20e23d92bef780ec4709fc`.

O hash calculado após a importação coincide com o valor registrado no
manifesto original.

## Artefatos relacionados

O pacote contém, para a mesma captura:

- manifesto versão `1.0`;
- JSON estrutural produzido por `dodf_to_markdown.py` versão `0.2.0`;
- Markdown derivado;
- extração produzida por `extract_mentions.py` versão `0.1.0`;
- migração PostgreSQL `001_initial_schema`;
- carregador e auditor do piloto.

As contagens preservadas e novamente verificadas são:

| Medida | Total |
|---|---:|
| páginas | 85 |
| blocos | 2.553 |
| blocos marcados como ruído | 179 |
| menções de processo SEI | 1.140 |
| processos SEI únicos | 1.096 |
| menções sem bloco | 0 |

## Banco histórico encontrado

Foi localizado o contêiner original
`memoria_institucional_postgres`, criado pelo projeto Compose
`histriainstitucionaldodf`, e o volume
`histriainstitucionaldodf_postgres_data`.

A consulta somente leitura em 2026-08-18 confirmou:

| Tabela | Linhas |
|---|---:|
| `sources` | 1 |
| `documents` | 1 |
| `document_captures` | 1 |
| `document_pages` | 85 |
| `document_blocks` | 2.553 |
| `extraction_runs` | 1 |
| `mentions` | 1.140 |

A migração `001_initial_schema` estava registrada como aplicada em
`2026-06-23 00:50:09.614885+00`. O contêiner foi parado novamente após a
consulta e o volume não foi removido nem modificado deliberadamente.

## Relação com o pacote de retomada

O pacote `dodf-codex-starter-2026-08-16.zip` é posterior e foi construído sem
acesso conhecido a todos os artefatos deste ancestral. Declarações desse pacote
de que código, PDF, manifesto, JSONs ou banco não haviam sido recuperados
descrevem o estado daquela recuperação, não a inexistência histórica desses
componentes.
