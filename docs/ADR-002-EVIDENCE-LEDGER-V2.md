# ADR-002 — Ledger de evidências v2

Status: aceito em 2026-08-18.

## Contexto

O schema inicial confundia bytes e eventos de captura, impedia duas capturas dos
mesmos bytes e registrava somente a transformação de extração. As menções também
repetiam captura, página, identificador e geometria do bloco, permitindo estados
contraditórios.

## Decisão

- `blobs` identifica bytes por SHA-256 e pode ser reutilizado por várias capturas.
- `captures` registra cada observação documental e aponta para um blob.
- `artifacts` registra toda saída persistida por hash, tipo, mídia, schema e URI.
- `transformation_runs` registra ferramenta, versão, parâmetros e conclusão.
- `transformation_io` forma o grafo explícito de entradas e saídas.
- `evidence_mentions` guarda somente o `block_id` como localização documental.
- Um trigger impede ligar menção e transformação a capturas diferentes.
- `source_policies` registra autoridade e política versionada da fonte.
- Caminhos novos usam `repo:///...` ou `urn:sha256:...`, nunca caminhos absolutos.

As tabelas da migração 001 permanecem durante a compatibilidade. O carregador
preenche os dois modelos na mesma transação; qualquer falha desfaz ambos.

## Invariantes

1. SHA-256 identifica conteúdo, não evento de captura.
2. Duas capturas podem apontar para um blob sem se tornarem o mesmo evento.
3. Toda transformação tem ao menos uma entrada e uma saída após carga concluída.
4. Toda menção canônica alcança transformação, artefatos, captura, documento e blob.
5. Deduplicação nunca remove capturas distintas.

## Rollback

O rollback operacional consiste em voltar o aplicativo ao commit anterior e usar
as tabelas da migração 001, que não são alteradas ou apagadas pela 002. As tabelas
v2 podem permanecer inertes. Sua remoção física só deve ocorrer após backup e por
migração destrutiva separada; não faz parte deste rollback.
