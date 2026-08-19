# Ambiente de desenvolvimento

## Instalação de referência

Requisitos: Python 3.11, PowerShell e Docker Desktop.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
```

`requirements-lock.txt` registra o ambiente Windows/CPython 3.11 validado. O
`pyproject.toml` é a definição canônica do pacote. PyMuPDF permanece fixado em
1.27.2.3 porque 1.28.2 mudou a segmentação do piloto de 2.553 para 2.402 blocos.

## Um comando para o piloto

```powershell
.\scripts\run_pilot.ps1
```

O comando recria os derivados em `.artifacts/pilot`, valida os quatro contratos,
audita referências, produz a projeção semântica e confere o baseline do DODF 112. Para carregar também o
banco, use `min-df-pipeline ... --load-db` com `DATABASE_URL` configurada.

O artefato `*.semantic.json` também pode ser gerado isoladamente com
`min-df-semantic CAMINHO_DO_STRUCTURED_JSON`. Ele contém observações navegáveis,
não entidades canônicas nem inferências consolidadas.

## Qualidade

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests scripts
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m pytest -q
```

O workflow `.github/workflows/quality.yml` executa os mesmos portões no Windows.

## PostgreSQL local

Copie `.env.example` para `.env` apenas se precisar alterar os padrões. Depois:

```powershell
.\scripts\db_up.ps1
.\scripts\db_migrate.ps1
.\scripts\db_load_pilot.ps1
.\scripts\db_counts.ps1
```

Migração e carga são idempotentes para o piloto.

## Explorador web

Para navegar a formação dos dados do DODF 112:

```powershell
.\scripts\web_up.ps1
```

O script atualiza o pacote de dados do painel e mostra o endereço local. A
interface permite buscar e filtrar matérias, pessoas, órgãos, cargos, ações,
processos e referências, além de abrir bloco, página, coordenadas, regra e texto
usados como evidência.

A calibração humana independente fica em `http://localhost:3000/anotar`. Essa
rota é deliberadamente separada do explorador: mostra as imagens das páginas 37
e 51 e referências estruturais de bloco, sem classificações automáticas. Para
recriar o pacote estrutural mínimo depois de alterar o documento-base:

```powershell
cd web
npm run data:calibration
```

O lote baixado pela interface deve ser validado antes de ser fechado:

```powershell
python -m min_df.annotation caminho\para\lote.json
```

O fluxo principal de controle de qualidade está em `/revisar`. A fila é
reproduzida a partir do explorador e da identidade material com:

```powershell
cd web
npm run data:review
```

## Política dos contratos

Os contratos ficam em `src/min_df/schemas` e usam JSON Schema 2020-12.

- Alterações retrocompatíveis mantêm a versão do contrato e só adicionam campos
  opcionais ou restrições que aceitem todos os artefatos válidos existentes.
- Alterações incompatíveis exigem novo identificador/versionamento de schema,
  migrador explícito e fixtures para as duas versões durante a transição.
- Produtores validam antes de gravar; consumidores validam antes de processar.
- Nunca se reescreve silenciosamente um artefato histórico para fazê-lo caber em
  um contrato novo.
