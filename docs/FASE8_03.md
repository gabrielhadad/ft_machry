# Fase 8.3 — Consolidação de domínio

Esta etapa consolida os limites definidos nas Fases 5–7 sem introduzir ainda o novo planejamento de produção.

## Fonte única por domínio

- `Produto` é a entidade oficial de catálogo. Não existem tabelas ou rotas legadas `Item`.
- `estoque.Lote` é o único lote do sistema; o saldo continua sendo alterado somente por `MovimentacaoEstoque`.
- `FichaTecnica`, `FichaTecnicaFase` e `FichaTecnicaComponente` são a única representação de ficha.
- `SolicitacaoProducao` permanece como raiz do agregado de produção; `Processamento` não é reintroduzido.

A suíte possui testes arquiteturais que falham caso tabelas ou rotas legadas do GAP reapareçam.

## Usuário fora do estoque

`Usuario` foi movido de `app.features.estoque.models` para `app.features.auth.models`.

A tabela SQL continua se chamando `usuario`; portanto esta mudança reorganiza o domínio Python sem alterar os dados persistidos.

O estoque apenas referencia o usuário responsável por uma movimentação.

## Consistência Produto × Estoque

O catálogo não pode mais ser alterado de maneira que torne lotes existentes inválidos:

- não é permitido alterar a conservação do produto se algum lote estiver em uma localização incompatível;
- não é permitido ativar `validade_obrigatoria` enquanto existirem lotes desse produto sem data de validade;
- continua proibido transformar em `INSUMO` um produto que possui ficha técnica.

Essas validações ficam no `ProdutoService`; o banco continua responsável por constraints estruturais.

## Regras de ficha preservadas

Foram congeladas por testes as regras já adotadas na fusão com o GAP:

- INSUMO não possui ficha;
- uma ficha por produto;
- produto não pode ser componente de si próprio;
- componentes precisam existir e estar ativos;
- fases precisam existir;
- ordens de fase não se repetem;
- componentes não se repetem;
- componente só referencia uma ordem de fase existente na própria ficha.

## FIFO → FEFO

O sistema já selecionava lotes pela data de validade; portanto a nomenclatura `FIFO` era histórica e incorreta.

A migration `8a3c1d4e5f67`:

- substitui `vw_fifo` por `vw_fefo`;
- substitui `idx_lote_fifo` por `idx_lote_fefo`;
- mantém downgrade reversível para a baseline `fee791234a46`.

A seleção operacional continua usando FEFO e deixa lotes sem validade por último. Lotes vencidos não são sugeridos.

## Validação

- 37 testes passando;
- `alembic upgrade head` validado em banco vazio;
- `alembic check` sem operações pendentes;
- downgrade para `fee791234a46` e novo upgrade para `8a3c1d4e5f67` validados;
- views finais: `vw_fefo`, `vw_inventario`, `vw_sp_componente`, `vw_sp_producao`.

## Próxima etapa

Fase 8.4 — Planejamento de produção:

- quantidade planejada;
- prioridade;
- data/horário previsto;
- responsável;
- observação;
- escala dos componentes da ficha pelo rendimento.
