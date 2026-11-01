# Validação — Fase 8.6

- pytest: **58 passed**;
- regressão da Fase 8.5: 53 testes anteriores preservados;
- FEFO automático na conclusão: OK;
- lote vencido ignorado: OK;
- divisão de um componente entre múltiplos lotes: OK;
- vínculos `solicitacao_producao_id` e `sp_componente_id`: OK;
- autoria pela sessão autenticada: OK;
- rollback total com estoque insuficiente: OK;
- retry não gera consumo duplicado: OK;
- AST: **49 arquivos Python** válidos;
- OpenAPI YAML: sintaxe válida;
- Alembic `upgrade head`: OK;
- Alembic `current`: `c4e8f1a2b730 (head)`;
- Alembic `check`: **No new upgrade operations detected**;
- nenhuma migration nova foi necessária porque os vínculos de produção já existiam no schema.
