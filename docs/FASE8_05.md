# Fase 8.5 — Execução real da produção

Esta fase adiciona o registro do **realizado** sem sobrescrever o planejamento criado na Fase 8.4.

## Objetivos

- registrar `quantidade_produzida` separadamente de `quantidade_planejada`;
- registrar observações de execução;
- registrar tempo real por fase;
- registrar início/fim e observação por fase;
- preservar snapshot histórico do nome da fase;
- manter compatibilidade com os endpoints já usados pelo frontend.

## Modelo

### `solicitacao_producao`

Novos campos:

- `quantidade_produzida` — nullable enquanto não houver apuração;
- `observacao_execucao` — separada da observação de planejamento.

`quantidade_planejada` continua imutável pela API de execução.

### `sp_fase`

Novos campos:

- `fase_nome_snapshot`;
- `observacao`;
- `iniciado_em`;
- `finalizado_em`.

`tempo_realizado_min`, que já existia, passa a ser exposto e atualizado pela API de execução.

O campo `fase_id` continua existindo para rastreabilidade, porém as telas e detalhes históricos usam `fase_nome_snapshot`. Assim, renomear `fase_producao.nome` não altera produções já planejadas.

## Endpoint novo

```http
PUT /api/producao/solicitacoes/{id}/execucao
```

Exemplo:

```json
{
  "quantidade_produzida": 19.5,
  "observacao_execucao": "Rendimento abaixo do planejado.",
  "fases": [
    {
      "sp_fase_id": 12,
      "tempo_realizado_min": 34,
      "observacao": "Necessitou mais tempo de cocção.",
      "iniciado_em": "2026-11-01T08:00:00",
      "finalizado_em": "2026-11-01T08:34:00"
    }
  ]
}
```

A execução só pode ser modificada enquanto a solicitação estiver `EM_PRODUCAO`.

A atualização é parcial: fases não enviadas permanecem como estavam.

## Regras

- pelo menos um dado de execução precisa ser informado;
- a mesma `sp_fase_id` não pode ser repetida no payload;
- a fase informada precisa pertencer à solicitação;
- `tempo_realizado_min` não pode ser negativo;
- `quantidade_produzida` não pode ser negativa;
- `finalizado_em` não pode ser anterior a `iniciado_em` quando ambos forem enviados.

## Migration

Revision:

```text
c4e8f1a2b730
```

A migration faz backfill de `fase_nome_snapshot` para produções antigas usando o nome atual de `fase_producao` no momento do upgrade.

A view `vw_sp_componente` foi atualizada para usar o snapshot da fase em vez do nome vivo do catálogo.

## O que ainda NÃO acontece

Esta fase não baixa estoque automaticamente e não cria lote de produto final. Esses pontos pertencem às próximas fases:

- Fase 8.6 — Produção ↔ Estoque;
- Fase 8.7 — Produto final + perdas.
