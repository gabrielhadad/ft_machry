# Machry — Fase 2: Backend de gerenciamento de praças

## Escopo implementado

Nova feature `app/features/pracas/` com camadas de routes, schemas, service e repository,
seguindo os padrões existentes do projeto.

| Método | Endpoint | Permissão | Função |
| --- | --- | --- | --- |
| GET | `/api/pracas` | `pracas:ler` | Listagem paginada (ativas e inativas) |
| GET | `/api/pracas/cozinheiros` | `pracas:ler` | Usuários ativos do grupo Cozinha, paginados |
| GET | `/api/pracas/{id}` | `pracas:ler` | Consulta individual |
| POST | `/api/pracas` | `pracas:criar` | Cadastro com pelo menos um cozinheiro |
| PUT | `/api/pracas/{id}` | `pracas:atualizar` | Atualização parcial e reativação |
| DELETE | `/api/pracas/{id}` | `pracas:excluir` | Desativação lógica; HTTP 204 |

As listagens usam o envelope existente (`items`, `page`, `per_page`, `total`, `pages`).

### Exemplo de cadastro

```json
{
  "nome": "Grelha",
  "descricao": "Estação de grelhados",
  "cozinheiros": [3, 7]
}
```

A resposta contém `id`, `nome`, `descricao`, `ativo`, `criado_em` e `cozinheiros`
(com `id`, `nome`, `username`). A criação sempre começa com `ativo=1`.

### Regras de negócio

- Nome obrigatório, com 2–120 caracteres após remover espaços nas pontas; nomes iguais ignorando
  maiúsculas/minúsculas retornam HTTP 409. Índice único funcional no banco reforça a regra.
- Criar/alterar a equipe exige ao menos um usuário existente, ativo e participante de `Cozinha`.
  IDs duplicados, inválidos e lista vazia retornam HTTP 400.
- Atualizar nome, descrição, situação e cozinheiros pelo PUT. Os campos omitidos não são alterados;
  `descricao: null` limpa a descrição. `nome`, `cozinheiros` e `ativo` não aceitam null explícito.
- Reativar uma praça verifica novamente a elegibilidade de sua equipe.
- Desativar a praça mantém registros e vínculos, inclusive os vínculos de produção da Fase 1.
- Atualizar/desativar usuários pela API de usuários impede deixar praça *ativa* sem cozinheiros
  elegíveis, retornando HTTP 409. **A alteração direta do banco e edições administrativas de
  grupos de acesso fora desse fluxo não são cobertas por essa proteção.**
- Operações de gravação são transacionais. Testes reais de concorrência em PostgreSQL pertencem
  à validação integrada da Fase 5.

### Permissões

Novo recurso `pracas` com ações `ler`, `criar`, `atualizar`, `excluir`.

- Banco **novo**: Administrador possui todas; Gestor possui todas; Cozinha possui somente `ler`.
- Banco **existente**: `init-db` sincroniza o catálogo e as permissões do grupo protegido
  Administrador. **Não altera automaticamente os grupos Gestor e Cozinha existentes**, pois
  o projeto preserva personalizações desses grupos. O Administrador deve atribuir as novas
  permissões manualmente, quando necessário, via `/api/grupos-acesso/{id}`.

### Atualização do esquema

`db/database_config.py` passa a garantir o índice único `uq_praca_nome_normalizado`
(para nomes sem diferença apenas de maiúsculas/minúsculas). Em dados preexistentes com
nomes equivalentes, a criação desse índice falhará até que a duplicidade seja resolvida.
Faça backup antes de executar a migração em qualquer banco compartilhado.

### Testes

`tests/test_pracas_api.py` contém testes para CRUD, associação, validação, rollback,
autorização, paginação, desativação com histórico e proteção da equipe.
`tests/test_acessos.py` atualiza a expectativa de permissões padrão do grupo Cozinha.

```powershell
# No diretório raiz do projeto, após instalar as dependências e configurar o banco de teste:
.\.venv\Scripts\python.exe -m pytest -q tests/test_pracas_api.py tests/test_pracas_modelagem.py
.\.venv\Scripts\python.exe -m pytest -q

# Só em uma base configurada e com backup:
.\.venv\Scripts\python.exe -m flask --app app init-db
```

### Limites da Fase 2

- Não altera os payloads de produção; criação/consulta/filtro de produção por praça é Fase 3.
- Não altera frontend; telas e seleção de praça na interface são Fase 4.
- Documento OpenAPI completo e verificação de regressão end-to-end são Fase 5.

## Validação no ambiente de preparação

- Sintaxe Python: verificada (`compileall`).
- SQL do índice único: verificação SQLite isolada (sem Flask).
- Pytest HTTP e PostgreSQL: **pendentes**, porque as dependências Flask/Flask-SQLAlchemy não
  estão instaladas neste ambiente e não foi possível obtê-las pela rede.
