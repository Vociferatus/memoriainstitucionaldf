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

1. Copiar `annotations/templates/blind-primary.template.json`.
2. Alterar o lote, o revisor, o instante e o escopo para `[37, 51]`.
3. Manter `automatic_artifacts: []` e não abrir o explorador automático.
4. Anotar as duas páginas usando apenas PDF, guia e referências de bloco para
   localização.
5. Fechar o lote e validar com:

   ```powershell
   min-df-validate-annotation caminho\para\lote.json
   ```

6. Após intervalo ou por segundo revisor, repetir com modo
   `independent_second`, sem consultar o primeiro lote.
7. Comparar os lotes somente quando ambos estiverem fechados.
8. Classificar todos os desacordos.
9. Criar novo lote de adjudicação; não editar os lotes originais.
10. Atualizar o guia para versão 1.1 se houver mudança de regra.

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
