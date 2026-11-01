# Baseline da Fase 8 — Integração GAP + Cozinha Mais

Este documento congela o ponto de partida usado na Fase 8 do projeto Machry.

## Base escolhida

A estrutura-base é a versão `feature/cozinha-mais` do FTMARCHY. O GAP Flask não
será mantido como uma segunda API: suas regras de domínio serão incorporadas
progressivamente aos módulos atuais.

## Arquitetura preservada

```text
frontend React + TypeScript
        ↓
      /api
        ↓
Flask (monólito modular)
├── auth
├── produtos
├── fichas_tecnicas
├── estoque
└── producao
        ↓
   SQLAlchemy
        ↓
PostgreSQL / SQLite de desenvolvimento
```

## Contratos congelados temporariamente

Durante a integração, os seguintes endpoints usados pelo frontend não devem ser
renomeados/removidos sem migração coordenada do SPA:

- `/api/auth/*`
- `/api/produtos`
- `/api/fichas-tecnicas`
- `/api/fichas-tecnicas/fases`
- `/api/estoque/inventario`
- `/api/estoque/lotes`
- `/api/estoque/localizacoes`
- `/api/estoque/movimentacoes`
- `/api/producao/solicitacoes`

`tests/test_baseline_contracts.py` protege os principais endpoints de coleção
contra regressões acidentais.

## Decisões de integração

- `Item` do GAP será substituído por `Produto`.
- O `Lote` do GAP não será incorporado; o saldo pertence ao módulo de estoque.
- Regras úteis de `FichaTecnica` do GAP serão incorporadas à ficha atual.
- `Processamento` não será criado em paralelo; seus conceitos de execução real
  serão incorporados em `SolicitacaoProducao`, `SpFase`, `SpComponente` e
  `MovimentacaoEstoque`.
- O frontend continua usando os contratos `/api/*` atuais durante a migração.

## Baseline de testes

Antes das alterações desta fase, a suíte existente passou com **23 testes**.
Após adicionar os testes de contrato e trocar o teste de produção que manipulava
o banco diretamente pela API pública, a suíte passa a ser a referência para as
próximas subfases.

## Próxima subfase

Adicionar Flask-Migrate/Alembic e criar uma estratégia de baseline de migrations
antes de alterar os modelos de produção.
