# Hotfix — Transformação inteligente de estoque

## Objetivo

Remover a necessidade de criar manualmente um lote do produto resultante antes de registrar uma transformação.

## Fluxo novo

A interface envia:

```json
{
  "tipo": "TRANSFORMACAO",
  "lote_id": 12,
  "produto_destino_id": 6,
  "localizacao_destino_id": 4,
  "quantidade": 1000,
  "quantidade_destino": 900,
  "observacao": "Queijo ralado para mise en place"
}
```

O backend:

1. bloqueia o lote de origem para atualização;
2. valida saldo;
3. valida se o par origem -> destino existe em `produto_transformacao`;
4. valida que origem e destino usam a mesma unidade de medida;
5. valida a conservação do produto resultante contra a localização escolhida;
6. calcula data de produção como a data atual;
7. calcula validade a partir de `validade_padrao_dias` do produto resultante, sem ultrapassar a validade do lote de origem; lotes vencidos são rejeitados;
8. recalcula o custo unitário do produto resultante preservando o custo total consumido;
9. cria ou reaproveita um lote compatível no local de destino;
10. registra uma única `TRANSFORMACAO` e atualiza os dois saldos na mesma transação.

## Perda e rendimento

A transformação já subtrai toda a quantidade de origem. Por isso **não é criada uma segunda movimentação `PERDA`**, pois isso baixaria o estoque duas vezes.

A auditoria fica no próprio movimento:

- `quantidade`: entrada consumida;
- `quantidade_destino`: saída obtida;
- `perda_transformacao`: `max(quantidade - quantidade_destino, 0)`;
- `rendimento_percentual`: `quantidade_destino / quantidade * 100`;
- `observacao`: recebe também um resumo textual de rendimento/perda.

Exemplo: 1000 g -> 900 g resulta em 90% de rendimento e 100 g de perda de rendimento.

## Compatibilidade

O contrato antigo com `lote_destino_id` continua aceito para clientes legados.

## Endpoint auxiliar

`GET /api/estoque/transformacoes?produto_origem_id=5`

Retorna os produtos de destino cadastrados, permitindo que o frontend ofereça apenas transformações válidas.

## Gestão das transformações permitidas

A própria tela de Estoque agora permite cadastrar e remover pares de transformação.

API:

- `GET /api/estoque/transformacoes`
- `POST /api/estoque/transformacoes`
- `DELETE /api/estoque/transformacoes/{produto_origem_id}/{produto_destino_id}`

Exemplo de cadastro:

```json
{
  "produto_origem_id": 4,
  "produto_destino_id": 7
}
```

Por enquanto, os dois produtos precisam usar a mesma unidade de medida. Isso evita percentuais de rendimento incorretos até que exista um fator de conversão explícito no domínio.
