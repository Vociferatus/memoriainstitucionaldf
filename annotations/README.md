# Anotações humanas

Este diretório recebe somente anotações humanas versionadas e seus metadados.
Saídas automáticas, bancos, caches e artefatos gerados não pertencem aqui.

Regras:

- um arquivo representa um lote imutável de um anotador e modo;
- primeira anotação, segunda revisão e adjudicação são arquivos diferentes;
- correções geram novo lote e referenciam o anterior em `parent_batch_ids`;
- anotações nunca sobrescrevem evidência nem saída automática;
- identificação pública do revisor não é obrigatória: use ID estável ou
  pseudônimo controlado;
- todo arquivo deve respeitar `human-annotation/1.0` e o guia vigente.

Templates válidos estão em `annotations/templates/`. Eles são esqueletos, não
constituem anotação nem conjunto ouro.
