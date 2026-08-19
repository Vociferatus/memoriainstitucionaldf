# Calibração da anotação — DODF 112

Versão: 1.0
Data: 2026-08-18
Estado: seleção congelada; anotações ainda não iniciadas.

## Objetivo

Aplicar duas vezes o guia de anotação em um escopo pequeno antes de selecionar as
12 páginas estratificadas. A calibração verifica se as definições são operáveis;
ela não mede a qualidade final do sistema.

## Páginas congeladas

### Página 37 — ações de pessoal e estrutura normativa

Características automáticas usadas somente para selecionar a página:

- 7 blocos estruturais;
- 2 matérias atravessando ou iniciando na página;
- 25 verbos de ação localizados;
- 22 menções de pessoa;
- processo SEI, matrícula, cargo e unidade educacional;
- início de portaria normativa após sequência de ações de pessoal.

Risco que ajuda a calibrar: distinguir pessoa, cargo, unidade, ação e matéria sem
usar proximidade como identidade.

### Página 51 — contratos, republicação e contexto editorial

Características automáticas usadas somente para selecionar a página:

- 15 blocos estruturais;
- 4 matérias presentes e 3 iniciadas na página;
- administração regional, secretaria, subsecretaria, coordenação e diretoria;
- contrato, termo aditivo, ata de registro de preços, processos e normas;
- data de assinatura e data de publicação no mesmo contexto;
- republicação por incorreção do original.

Risco que ajuda a calibrar: separar matéria, breadcrumb editorial, organização,
instrumento, temporalidade e vínculo de republicação.

## Protocolo de execução

1. Abrir `/anotar` na interface web e informar um identificador de revisor. Como
   alternativa sem interface, copiar
   `annotations/templates/blind-primary.template.json`.
2. Selecionar `blind_primary` na primeira aplicação. A interface fixa o escopo
   em `[37, 51]`, o baseline e `automatic_artifacts: []`.
3. Não abrir o explorador automático nem consultar lotes anteriores durante a
   aplicação independente.
4. Anotar as duas páginas usando a imagem integral como fonte primária e as
   referências de bloco somente para localização.
5. Exportar o lote JSON. O navegador preserva apenas um rascunho local; o arquivo
   exportado é o artefato que deve ser fechado e versionado.
6. Validar com:

   ```powershell
   min-df-validate-annotation caminho\para\lote.json
   ```

7. Após intervalo ou por segundo revisor, repetir com modo
   `independent_second`, sem consultar o primeiro lote.
8. Comparar os lotes somente quando ambos estiverem fechados.
9. Classificar todos os desacordos.
10. Criar novo lote de adjudicação; não editar os lotes originais.
11. Atualizar o guia para versão 1.1 se houver mudança de regra.

## Interface de calibração

A rota `/anotar` contém somente as imagens das páginas congeladas e um pacote
estrutural mínimo com página, bloco, ordem, coordenadas e texto original. O
pacote não contém matérias, entidades, ações, referências semânticas nem
classificações de layout. A interface:

- aceita apenas observações `PRESENT` ou `AMBIGUOUS` sem alvo automático;
- exige ao menos uma evidência e justificativa para ambiguidade;
- permite múltiplos blocos para limites de matéria;
- salva rascunho somente no dispositivo do revisor;
- exporta um lote compatível com `human-annotation/1.0`.

## Saída esperada

- dois lotes independentes válidos;
- relatório de desacordos por tarefa;
- lote de adjudicação quando necessário;
- decisão `APROVADO`, `APROVADO COM RESSALVAS` ou `REPROVADO` para o Portão 1;
- guia 1.0 preservado mesmo se uma versão posterior for criada.

## Restrições

- essas páginas não podem ser substituídas após examinar os resultados;
- estatísticas automáticas acima justificam a seleção, mas não são rótulos ouro;
- o Codex pode ajudar com contrato, validação e comparação, mas não deve ser
  tratado como segundo revisor humano independente;
- nenhum dado pessoal adicional deve ser transcrito além do estritamente
  necessário para a anotação controlada.
