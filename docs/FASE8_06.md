# Fase 8.6 — Produção ↔ Estoque

## Objetivo

Integrar a conclusão de produção ao estoque sem criar um segundo controle de saldo. O estoque continua sendo a fonte única da quantidade realmente consumida.

## Fluxo implementado

1. A solicitação precisa estar `EM_PRODUCAO`.
2. O backend bloqueia a solicitação durante a conclusão.
3. Os `SpComponente` definem as quantidades que precisam ser consumidas.
4. Para cada produto, o estoque busca apenas lotes com saldo e não vencidos.
5. Os lotes são ordenados por FEFO: validade mais próxima primeiro; sem validade fica por último.
6. O sistema monta o plano completo antes de alterar qualquer saldo.
7. Cada alocação gera `MovimentacaoEstoque(tipo=CONSUMO_PRODUCAO)`.
8. A movimentação recebe `solicitacao_producao_id`, `sp_componente_id` e o usuário autenticado.
9. Somente depois das baixas a solicitação é marcada `CONCLUIDA`.
10. Um único commit confirma toda a operação. Qualquer erro executa rollback.

## Idempotência e concorrência

A solicitação é lida com `FOR UPDATE` nos bancos que suportam o recurso. Isso serializa tentativas concorrentes de conclusão. O serviço de estoque também rejeita uma segunda baixa se já existir `CONSUMO_PRODUCAO` para a solicitação.

## Estoque insuficiente

`EstoqueInsuficiente` deriva de `Conflito`, retornando HTTP `409`. O erro informa o produto, quantidade necessária e quantidade disponível. Como a baixa está na mesma transação da conclusão, não existem movimentos ou saldos parciais após a falha.

## Decisões

- O algoritmo FEFO continua pertencendo ao módulo `estoque`.
- `ProducaoService` apenas orquestra a operação.
- Quantidade realizada de cada componente continua derivada da soma das movimentações de estoque (`vw_sp_componente`).
- Nesta fase, a baixa automática usa a quantidade planejada do `SpComponente`. Ajustes/perdas serão tratados na etapa seguinte.
- Não houve mudança de schema; a migration atual continua `c4e8f1a2b730`.
