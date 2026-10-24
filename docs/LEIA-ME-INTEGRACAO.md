# Módulo de estoque para nelsondarosa/ft_machry

Este ZIP é um **patch de integração**, não um projeto Flask independente. Base: branch `product-api` / PR #1 de 16/10/2026. Não altera `db/schema.sql`, o CRUD de produtos nem a produção.

## Aplicação no GitHub

1. Aguarde a aprovação/merge do PR #1 (`product-api`) para `main`, **ou** trabalhe a partir da branch `product-api`.
2. Crie sua própria branch, por exemplo `feature/estoque-gabriel`.
3. Copie a pasta `app` e a pasta `tests` deste ZIP para a raiz do projeto existente, mantendo os caminhos. Substitua somente `app/features/estoque/routes.py` (os demais arquivos do projeto permanecem).
4. Instale dependências com `pip install -r requirements.txt` e `pip install pytest`.
5. Em um banco **novo e de testes**, rode `flask --app app init-db --seed` (não rode init-db em banco já inicializado; o comando não é uma migração).
6. Rode `pytest -q tests/test_estoque.py` e `flask --app app run`.
7. Faça commit e abra um pull request da sua branch, sem sobrescrever a branch `main`.

## Endpoints implementados

- `GET /api/estoque/inventario` — inventário, filtros `produto_id` e `lote_id`.
- `GET /api/estoque/movimentacoes` — histórico (tipo, usuário, lote, limite).
- `POST /api/estoque/movimentacoes` — entrada, saída, ajustes, transferência, transformação.
- `GET/POST /api/estoque/localizacoes` — listar/cadastrar locais.
- `PUT/DELETE /api/estoque/localizacoes/{id}` — atualizar/remover (remoção falha caso possua dependências).
- `GET/POST /api/estoque/lotes` — listar/criar lotes.
- `GET/PUT /api/estoque/lotes/{id}` — detalhar/editar dados do lote, nunca o saldo diretamente.
- `GET /api/estoque/sugestao-saida/{produto_id}?quantidade=10` — sugestão FEFO (validade mais próxima); não registra saída automaticamente.

## Exemplos

Criar lote: `POST /api/estoque/lotes`
```json
{"produto_id":5,"localizacao_id":2,"data_validade":"2027-04-30","custo_unitario":0.05}
```
Registrar entrada: `POST /api/estoque/movimentacoes`
```json
{"tipo":"ENTRADA","lote_id":1,"usuario_id":1,"quantidade":100}
```
Saída: `POST /api/estoque/movimentacoes`
```json
{"tipo":"SAIDA","lote_id":1,"usuario_id":1,"quantidade":10,"motivo":"uso na cozinha"}
```
Transformar queijo em queijo ralado (produtos **distintos**, regra já prevista em `produto_transformacao`):
```json
{"tipo":"TRANSFORMACAO","lote_id":1,"lote_destino_id":2,"usuario_id":1,"quantidade":100,"quantidade_destino":95}
```
Os IDs são exemplos: substitua pelos IDs reais. O lote de destino precisa ter produto correspondente e a transformação estar previamente autorizada em `produto_transformacao`.

## Regras e cuidados

- O banco aplica a alteração de saldo por meio de trigger, em transação única; o endpoint apenas insere eventos em `movimentacao_estoque`.
- Saldo insuficiente, lote/usuário inexistente e transformação não cadastrada são rejeitados.
- `PRODUCAO` e `CONSUMO_PRODUCAO` ficam reservados à integração com o módulo de produção.
- Lotes usam conservação compatível com a localização e datas válidas. A sugestão FEFO ignora lotes vencidos; movimentações manuais ainda podem movimentar lotes vencidos e precisam de política operacional própria.
- O banco modela estoque imutável por eventos; **não se deve editar ou apagar movimentações**. Correções são feitas por ajuste de entrada/saída.
- Nesta versão, `usuario_id` é informado no corpo, sem login/autorização. É apropriado para trabalho acadêmico, não para produção sem autenticação.
- `app/openapi.yaml` do PR #1 documenta apenas produtos. Este patch inclui `docs/estoque-openapi.yaml` como especificação complementar, para não gerar conflito com o arquivo dos colegas. Para unificar na interface `/docs`, integrar depois as rotas do documento complementar.
