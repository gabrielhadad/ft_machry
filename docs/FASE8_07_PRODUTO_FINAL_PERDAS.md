# Fase 8.7 — Produto final e perdas

Esta fase fecha o ciclo transacional da produção com o estoque.

## Conclusão da produção

Ao mudar uma solicitação de `EM_PRODUCAO` para `CONCLUIDA`, a mesma transação:

1. valida e baixa todos os componentes por FEFO;
2. usa `quantidade_produzida` como rendimento real (ou o planejado quando um cliente legado não informou o realizado);
3. cria um lote do produto da ficha técnica;
4. calcula `data_producao` e, quando configurada, `data_validade` a partir de `validade_padrao_dias`;
5. registra `MovimentacaoEstoque(tipo="PRODUCAO")` vinculada à solicitação;
6. marca a solicitação como `CONCLUIDA`.

Se qualquer etapa falhar, o rollback também desfaz as baixas de ingredientes e a eventual criação do lote final.

`localizacao_destino_id` pode ser enviada no `PUT /api/producao/solicitacoes/{id}/status` apenas ao concluir. Enquanto o frontend ainda não expõe esse campo, a API escolhe a primeira localização compatível com a conservação do produto.

## Perda de rendimento

`perda_rendimento` é calculada como:

```text
max(quantidade_planejada - quantidade_produzida, 0)
```

Ela representa produto que **não chegou a existir** e, por isso, não gera movimento de estoque.

## Perda de ingrediente

Desperdícios físicos de componentes são eventos de estoque reais. A execução aceita:

```json
{
  "perdas": [
    {
      "sp_componente_id": 12,
      "quantidade": 20,
      "motivo": "Derramamento durante a mistura"
    }
  ]
}
```

O backend seleciona os lotes por FEFO e registra `MovimentacaoEstoque(tipo="PERDA")`, ligada à solicitação e ao componente. A view `vw_sp_componente` soma `CONSUMO_PRODUCAO + PERDA`, fazendo o realizado refletir toda quantidade efetivamente retirada do estoque para aquela produção.

## Migration

Revision atual:

```text
d6a1b2c3d4e5
```

Ela adiciona `PERDA` à constraint de tipos de movimentação e atualiza `vw_sp_componente`.
