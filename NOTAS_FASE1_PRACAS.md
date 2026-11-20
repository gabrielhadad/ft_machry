# Machry — Fase 1: modelagem de Praças

## Escopo implementado

- `Praca` (`praca`): nome único, descrição opcional, ativo (0/1) e data de criação.
- `PracaUsuario` (`praca_usuario`): vínculo N:N entre usuários e praças, com chave primária composta.
- `Usuario.pracas` e `Praca.cozinheiros`: relacionamentos bidirecionais.
- `SolicitacaoProducao.praca_id` e `Praca.solicitacoes`: vínculo 1:N opcional, preservando solicitações antigas.
- `db/database_config.py`: migração incremental e idempotente da coluna `praca_id`, incluindo índice.
- `tests/test_pracas_modelagem.py`: testes focados em DDL, relacionamentos, integridade e migração legada.

## Decisões e limites

- A regra de que uma praça deve ter **pelo menos um** cozinheiro é uma validação de negócio; será aplicada na Fase 2. Por enquanto, a estrutura do banco permite criar uma praça vazia.
- As permissões e a restrição de participação a usuários do grupo Cozinha serão implementadas na Fase 2.
- Nenhum endpoint ou payload de produção existente foi alterado nesta fase; suporte na API ficará para a Fase 3.
- O esquema do banco usa o mecanismo `init-db` já existente, sem introduzir Alembic.
- As migrações que alteram bancos existentes devem ser executadas primeiro em ambiente de testes, com backup.

## Aplicação em um repositório existente

Copie somente os arquivos alterados para a raiz do seu projeto, sem substituir a pasta `.git`.
Faça `git status` antes e depois da cópia e inspecione `git diff`.

No PowerShell, depois de configurar o ambiente virtual e as dependências:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_pracas_modelagem.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m flask --app app init-db
```

**Atenção:** `init-db` altera o esquema da base configurada. Confirme a variável `DATABASE_URL`/`DATABASE_PATH` e faça backup antes de executá-lo em banco compartilhado.

## Validações realizadas no ambiente de elaboração

- Sintaxe Python: validada com `compileall` e AST.
- DDL SQL equivalente em SQLite: validado com chaves estrangeiras, índice e inclusão de coluna sem perder linhas anteriores.
- Pytest: **não executado** neste ambiente por ausência de Flask e Flask-SQLAlchemy (instalação de dependências indisponível pela rede).
- PostgreSQL: **não validado** neste ambiente.
