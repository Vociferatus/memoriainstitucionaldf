# Política de dados, artefatos e pacotes-fonte

Versão: 1.0
Data: 2026-08-18

## Objetivo

Preservar evidências e permitir reprodução sem transformar o repositório Git em
armazenamento indiscriminado de corpora crescentes.

## Classes de conteúdo

### Código e documentação

Devem ser versionados normalmente:

- código-fonte;
- migrações;
- schemas;
- configuração sem segredos;
- documentação e ADRs;
- testes e fixtures pequenas;
- manifestos de inventário que não exponham dados desnecessários.

### Evidência bruta

PDFs e respostas originais são imutáveis. Para cada objeto devem existir, no
mínimo:

- SHA-256;
- tamanho;
- media type;
- fonte e URL;
- instante de captura;
- metadados de transporte disponíveis;
- identificador do storage.

Após a linha de base, novos arquivos brutos não entram automaticamente no Git.
Devem ser preservados no storage documental e referenciados por manifesto.

### Artefatos derivados

JSON estrutural, Markdown, extrações, imagens e OCR devem registrar:

- hash da entrada;
- hash da saída;
- ferramenta e versão;
- schema version;
- parâmetros;
- instante da transformação.

Derivados devem ser reconstruíveis. Sua retenção pode ser útil para auditoria e
comparação, mas não os transforma em fonte de verdade superior aos bytes
originais.

### Pacotes recebidos

Um ZIP ou pacote externo é tratado como objeto de proveniência. Antes de ser
incorporado, deve ter:

- nome preservado ou mapeamento documentado;
- origem registrada;
- tamanho;
- data conhecida;
- SHA-256;
- inventário;
- relação com outros pacotes e artefatos.

Não se substitui um pacote existente por outro conteúdo com o mesmo nome.

### Segredos e dados locais

Nunca entram no Git:

- `.env` reais;
- senhas e tokens;
- volumes PostgreSQL;
- índices locais;
- caches;
- logs com dados sensíveis;
- arquivos temporários.

## Exceção da linha de base recuperada

O primeiro commit preserva integralmente o piloto ancestral, inclusive PDF,
JSON estrutural, extrações e pacotes de recuperação. A exceção é deliberada
porque:

1. o conjunto tem aproximadamente 18,7 MB;
2. documenta a recuperação histórica do projeto;
3. contém o único vertical slice original conhecido;
4. permite validar a cadeia de reprodução sem depender de storage externo;
5. seus hashes e proveniência foram auditados.

Os padrões de `.gitignore` protegem contra inclusão automática de novas
edições. Arquivos já rastreados permanecem versionados como referência.

## Evolução do armazenamento

### Uma edição e conjunto ouro

- baseline preservado no Git;
- filesystem local controlado;
- backup independente;
- manifestos obrigatórios.

### Dez edições e um mês

- storage documental separado;
- inventário no banco;
- backup externo;
- fixtures pequenas no Git;
- avaliação formal de Git LFS somente se houver necessidade concreta.

### Um ano ou mais

- object storage ou implementação equivalente;
- objetos endereçados por conteúdo;
- política de retenção e lifecycle;
- verificação periódica de integridade;
- restauração testada.

## Integridade

- SHA-256 é o identificador inicial de conteúdo.
- Hash igual permite deduplicar bytes, não eventos de captura.
- Uma captura nunca é descartada apenas porque aponta para blob já conhecido.
- Verificação periódica deve recalcular hashes a partir dos bytes armazenados.
- Backups só são considerados válidos após teste de restauração.

## Alterações desta política

Mudanças que afetem preservação, versionamento, retenção ou exclusão devem ser
registradas em ADR e não podem reduzir silenciosamente a capacidade de auditar
artefatos históricos.
