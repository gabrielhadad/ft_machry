# Fase 8.2 — Flask-Migrate / Alembic

## Mudanças

- Flask-Migrate e Alembic adicionados às dependências.
- `Migrate` integrado ao Application Factory.
- Criado repositório `migrations/`.
- Criada baseline `fee791234a46` com todas as tabelas, constraints, índices e as quatro views atuais.
- `run.bat` e `run.sh` executam `flask db upgrade` antes do bootstrap.
- Container da API aplica migrations antes de iniciar Gunicorn.
- `init-db` deixa de criar schema em runtime; `create_all()` fica restrito a `TESTING`.
- Seeds só são aplicados em catálogo vazio.
- Adicionado smoke test da migration em SQLite.

## Próxima fase

Fase 8.3 — consolidar domínio antes de evoluir o modelo de produção.
