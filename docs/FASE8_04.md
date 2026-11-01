# Fase 8.4 — Planejamento de produção

Esta etapa transforma `SolicitacaoProducao` de uma simples entrada na fila em um planejamento operacional, sem criar uma entidade paralela ao domínio de produção.

## Campos adicionados

`SolicitacaoProducao` passa a registrar:

- `quantidade_planejada`: quantidade do produto final/intermediário na unidade do produto produzido;
- `prioridade`: `BAIXA`, `NORMAL`, `ALTA` ou `URGENTE`;
- `previsto_para`: data/hora ISO 8601 planejada;
- `responsavel_id`: usuário ativo designado para executar a produção;
- `observacao`: orientação operacional do planejamento;
- `iniciado_em`: instante em que a solicitação entra em `EM_PRODUCAO`.

`usuario_id` continua sendo o usuário que criou a solicitação. Dessa forma, solicitante e responsável não são confundidos.

## Compatibilidade do contrato

O payload histórico permanece válido:

```json
{
  "ficha_tecnica_id": 1
}
```

Quando `quantidade_planejada` é omitida, o backend utiliza `FichaTecnica.rendimento`. Portanto os componentes copiados para `SpComponente` permanecem exatamente com as quantidades da ficha original.

O novo payload também aceita:

```json
{
  "ficha_tecnica_id": 1,
  "quantidade_planejada": 20,
  "prioridade": "ALTA",
  "previsto_para": "2026-11-03T08:30:00",
  "responsavel_id": 3,
  "observacao": "Priorizar para a abertura."
}
```

## Escala pelo rendimento

A ficha representa ingredientes para um determinado rendimento. A quantidade de cada componente da solicitação é calculada por:

```text
fator = quantidade_planejada / rendimento_da_ficha
quantidade_prevista = quantidade_da_ficha * fator
```

Exemplo:

```text
Ficha rende 10 unidades
Farinha = 5 kg

Planejamento = 20 unidades
Fator = 20 / 10 = 2
Farinha planejada = 10 kg
```

A escala é calculada no backend e persistida em `SpComponente`, congelando o planejamento daquela produção.

## Responsável

`responsavel_id` é opcional, mas, quando informado, precisa identificar um usuário ativo. Um identificador inexistente ou inativo é rejeitado.

## Início da produção

Na primeira transição para `EM_PRODUCAO`, `iniciado_em` é preenchido automaticamente. A máquina de estados existente permanece preservada.

## Migration

A revision `b7d9e2f4a610` adiciona os campos de planejamento, constraints e o índice `idx_solicitacao_planejamento`.

Para solicitações existentes, a migration preenche `quantidade_planejada` com o rendimento da ficha técnica correspondente. Assim, bancos já utilizados não recebem uma quantidade arbitrária.

A migration foi validada em:

```text
upgrade 8a3c1d4e5f67 -> b7d9e2f4a610
downgrade b7d9e2f4a610 -> 8a3c1d4e5f67
upgrade novamente -> b7d9e2f4a610
alembic check -> nenhuma operação pendente
```

## Frontend

Os tipos TypeScript já conhecem os novos campos, mas a tela de produção continua enviando somente `ficha_tecnica_id` nesta fase. Isso é intencional: a experiência de planejamento será alterada na fase de alinhamento de frontend, depois que execução real e integração com estoque estabilizarem os contratos.

## Validação

- payload legado preservado;
- escala de componentes testada;
- quantidade zero rejeitada;
- prioridade desconhecida rejeitada;
- data inválida rejeitada;
- responsável inexistente rejeitado;
- `iniciado_em` testado;
- migration de banco existente testa backfill pelo rendimento;
- 45 testes passando.

## Próxima etapa

Fase 8.5 — execução real da produção:

- quantidade produzida real;
- tempo realizado por fase;
- observação por fase;
- snapshot histórico suficiente para preservar o planejado;
- contratos de execução separados do planejamento.
