# Machry — Fase 3: integração de praças com a produção

## Implementação

A coluna `solicitacao_producao.praca_id` e seu índice foram criados na Fase 1.
Nesta fase, a API de produção passou a usar o relacionamento existente, sem
introduzir nova migração ou modificar as regras de FEFO, baixas e lotes.

### API

| Método | Rota | Comportamento |
| --- | --- | --- |
| `POST` | `/api/producao/solicitacoes` | Aceita `praca_id` opcional (inteiro positivo ou `null`) |
| `GET` | `/api/producao/solicitacoes` | Lista todas; aceita `?praca_id=ID` para filtrar |
| `GET` | `/api/producao/solicitacoes/{id}` | Retorna vínculo dentro de `solicitacao` |
| `PUT` | `/api/producao/solicitacoes/{id}/praca` | Reatribui ou remove a praça antes da execução |
| `PUT` | `/api/producao/solicitacoes/{id}/status` | Mantém transições anteriores, com lock antes de gravar |

Os objetos de solicitação (criação, lista, detalhe e status) agora incluem:

```json
{
  "praca_id": 5,
  "praca": {"id": 5, "nome": "Grelha", "ativo": 1}
}
```

Para solicitações sem praça: `"praca_id": null`, `"praca": null`. Os demais
campos permanecem inalterados. O filtro retorna lista vazia se não existirem
produções vinculadas ao ID, mantendo o envelope de paginação existente.

### Atualizar a praça

Payload: `{"praca_id": 5}`. Pode usar `{"praca_id": null}` para desatribuir.
Essa atualização é permitida somente enquanto a solicitação estiver `ABERTA`
ou `EM_SEPARACAO`. Após `EM_PRODUCAO`, `CONCLUIDA` ou `CANCELADA`, o endpoint
responde HTTP 409 e preserva o histórico. Ausência do campo ou ID inválido
retorna HTTP 400; ID da solicitação inexistente retorna 404.

A nova atribuição exige praça existente, ativa e com ao menos um usuário ativo
participante do grupo `Cozinha`. Produções já atribuídas a praças posteriormente
desativadas preservam a referência e podem continuar seu fluxo de execução.

A rota de realocação exige `producao:criar` (permissão de planejamento), não
`producao:atualizar` (que o grupo Cozinha já possui para mudar status). Assim,
cozinheiros não ganham poder de realocação somente por poderem atualizar status.

### Compatibilidade e limites

- Atribuir praça **não exige** que o autor ou executor pertença à equipe da
  praça. A restrição de visualização/execução por equipe **não foi definida**;
  não foi adicionada implicitamente nesta etapa.
- Nenhuma praça é criada automaticamente nem definida como obrigatória. O
  frontend atual ainda pode criar produções sem `praca_id`.
- O relacionamento é **uma praça por solicitação**; distribuição das fases de
  uma mesma produção por diversas praças não está contemplada.
- O backend de produção usa transações e bloqueios de linhas para realocação e
  transições de status. SQLite não reproduz integralmente a concorrência do
  PostgreSQL, que ainda precisa ser testada em ambiente de integração.
- A Fase 4 permanece responsável pelas telas React. A Fase 5 engloba a revisão
  final de OpenAPI, testes de ponta a ponta e validação de deploy.

## Testes preparados

`tests/test_producao_pracas.py` cobre compatibilidade legada, criação, filtro,
consulta, realocação, status finais, permissões, desativação e conclusão com
movimentações de estoque.

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_producao_pracas.py tests/test_producao.py tests/test_pracas_api.py tests/test_pracas_modelagem.py
.\.venv\Scripts\python.exe -m pytest -q
```

**Validação neste ambiente:** sintaxe e schemas Pydantic estáticos verificados.
Os testes Pytest de integração **não puderam executar**, porque as dependências
Flask e Flask-SQLAlchemy não estão instaladas. PostgreSQL permanece não validado.

Não execute `flask init-db` em ambiente compartilhado sem backup e conferência da conexão.
