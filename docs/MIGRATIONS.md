# Migrations do banco

A partir da Fase 8.2, o schema do Machry/Cozinha Mais é versionado por **Flask-Migrate + Alembic**.

## Banco novo

Instale as dependências e aplique todas as migrations:

```bash
pip install -r requirements.txt
flask --app app db upgrade
flask --app app init-db --seed
```

`db upgrade` cria/atualiza o schema. `init-db` não é mais responsável por criar tabelas em runtime; ele provisiona os usuários iniciais e, opcionalmente, os dados de demonstração.

## Alterar models

Depois de modificar models SQLAlchemy:

```bash
flask --app app db migrate -m "descricao da alteracao"
```

Revise obrigatoriamente o arquivo gerado em `migrations/versions/` e então execute:

```bash
flask --app app db upgrade
```

O autogenerate do Alembic não entende automaticamente todos os objetos de banco. Views, dados especiais e alterações destrutivas precisam ser revisados/escritos explicitamente na migration.

## Banco existente da Fase 8.1 ou anterior

A migration `fee791234a46` representa o schema-base já existente na Fase 8.1. Portanto **não execute `upgrade` diretamente em um banco que já possui essas tabelas**, pois a migration tentaria criá-las novamente.

Primeiro faça backup e confirme que o banco realmente corresponde ao schema da Fase 8.1. Depois marque a baseline como já aplicada:

```bash
flask --app app db stamp fee791234a46
flask --app app db current
```

A partir daí, futuras migrations podem ser aplicadas normalmente:

```bash
flask --app app db upgrade
```

Se o banco for mais antigo ou tiver divergências manuais, não use `stamp` às cegas: ele registra uma revisão sem alterar o schema.

## Comandos úteis

```bash
flask --app app db current
flask --app app db history
flask --app app db heads
flask --app app db migrate -m "descricao"
flask --app app db upgrade
flask --app app db downgrade
```

## Regra do projeto

- Models SQLAlchemy descrevem o estado desejado da aplicação.
- Migrations descrevem **como chegar** a esse estado sem apagar os dados.
- Alterações de schema em runtime não devem usar `db.create_all()`, `ALTER TABLE` manual ou `drop_all()`.
- `db.create_all()` permanece apenas no bootstrap isolado da suíte de testes unitários.
