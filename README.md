# ft_machry

API Flask + SQLite para estoque e produção de cozinha (produtos, lotes, fichas técnicas, solicitações de produção).

## Rodar localmente

Requer Python 3.12+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate | Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

flask --app app init-db --seed   # cria data/app.db a partir de db/schema.sql (+ db/seeds.sql)
flask --app app run              # http://localhost:5000
```

`init-db` sem `--seed` cria o banco vazio. O caminho do banco vem de `DATABASE_PATH` (padrão `data/app.db`).

## Rodar com Docker

```bash
docker compose build
docker compose run --rm api flask --app app init-db --seed
docker compose up
```

O banco fica em `./data`, montado no container.

## Documentação da API (Swagger)

Com o app rodando:

- Swagger UI: http://localhost:5000/docs
- Spec OpenAPI: http://localhost:5000/openapi.yaml (arquivo em `app/openapi.yaml`)

O Swagger UI é carregado via CDN, então o navegador precisa de internet.

Hoje a spec cobre a API de produtos (`/api/produtos`).

## Testes

```bash
pip install pytest
pytest
```

Cada teste usa um banco SQLite temporário; `data/app.db` não é tocado.
