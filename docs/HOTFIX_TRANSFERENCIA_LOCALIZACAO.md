# Hotfix — transferência por localização

A tela de estoque não exige mais que o usuário crie manualmente um lote vazio antes de transferir mercadoria.

## Fluxo novo

`lote de origem -> localização de destino -> quantidade`

A API aceita `localizacao_destino_id` para `TRANSFERENCIA`. Dentro da mesma transação ela:

1. valida saldo e conservação do produto;
2. rejeita a própria localização de origem;
3. procura no destino um lote com a mesma rastreabilidade (produto, produção, validade e custo);
4. reaproveita esse lote quando existir ou cria um novo lote com saldo zero;
5. registra `TRANSFERENCIA`, desconta a origem e soma o destino.

O campo legado `lote_destino_id` continua aceito em transferências para manter compatibilidade. Transformações continuam exigindo um lote de destino explícito.

Nenhuma migration é necessária: a alteração é de contrato HTTP, regra de negócio e frontend; o schema do banco permanece igual.
