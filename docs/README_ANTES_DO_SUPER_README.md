# Machry

Sistema de operação para restaurante, com API Flask, frontend React com Vite e TypeScript e persistência SQLAlchemy. O ambiente padrão usa SQLite em volume local. A mesma camada de persistência aceita PostgreSQL quando a infraestrutura for migrada.

## Funcionalidades atuais

- Catálogo de insumos, produtos intermediários e produtos finais.
- Fichas técnicas com rendimento, fases ordenadas e componentes.
- Validações de domínio recuperadas do projeto anterior.
- Lotes, localizações, movimentações e sugestão de saída por FEFO.
- Estoque geral de insumos, produtos intermediários e produtos finais, com entradas, saídas e ajustes pela interface.
- Planejamento de produção com quantidade, prioridade, horário previsto, responsável e observação.
- Escala automática dos componentes da ficha técnica conforme a quantidade planejada.
- Interface responsiva para produtos e fichas técnicas.
- Login por sessão com perfis de proprietária, gestor e cozinha.
- Swagger em `/docs`.

## Executar na VM com Docker e SQLite

Crie o arquivo de ambiente e inicialize o banco uma única vez:

```bash
cp .env.example .env
docker compose build
docker compose run --rm api flask --app app db upgrade
docker compose run --rm api flask --app app init-db --seed
docker compose up -d
```

Acessos padrão:

- Interface: `http://IP_DA_VM:8080`
- API: `http://IP_DA_VM:5000`
- Swagger: `http://IP_DA_VM:5000/docs`
- Saúde da API: `http://IP_DA_VM:5000/health`

O SQLite é salvo em `./data/app.db` na VM. Faça backup dessa pasta antes de atualizar ou mover o serviço.

Para acompanhar os containers:

```bash
docker compose ps
docker compose logs -f api frontend
```

## Desenvolvimento local

### API Flask

Requer Python 3.12+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
flask --app app db upgrade
flask --app app init-db --seed
flask --app app run
```

### Frontend React, Vite e TypeScript

Requer Node.js 22+ e pnpm.

```bash
cd frontend
pnpm install
pnpm dev
```

O servidor Vite abre em `http://localhost:5173` e encaminha `/api` para o Flask em `http://localhost:5000`.

### Acessos iniciais de desenvolvimento

Ao executar `flask --app app init-db`, o sistema cria ou atualiza as contas iniciais:

| Perfil | Usuário | Senha inicial |
|---|---|---|
| Proprietária | `dona` | `Dona@123` |
| Gestor | `gestor` | `Gestor@123` |
| Cozinha | `cozinha` | `Cozinha@123` |

Altere as credenciais e `SECRET_KEY` no arquivo `.env` antes de publicar. As senhas são armazenadas no banco somente como hash.

Para validar a compilação:

```bash
pnpm exec tsc --noEmit
pnpm build
```


## Migrations do banco

O schema agora é versionado com Flask-Migrate/Alembic. Para um banco novo, execute `flask --app app db upgrade` antes de `init-db`. Para alterar models, gere uma migration com `flask --app app db migrate -m "descricao"`, revise o arquivo e aplique com `db upgrade`.

Bancos que já existiam antes da Fase 8.2 devem seguir o procedimento de baseline/stamp descrito em [`docs/MIGRATIONS.md`](docs/MIGRATIONS.md); não execute a migration inicial sobre tabelas já existentes sem revisar o schema.

## PostgreSQL

O container PostgreSQL já está preparado como um profile opcional. Ajuste o `.env`:

```dotenv
DB_CONNECTION=postgresql
DB_HOST=postgres
DB_PORT=5432
DB_DATABASE=ft_machry
DB_USERNAME=machry
DB_PASSWORD=uma-senha-forte
```

Depois inicialize com:

```bash
docker compose --profile postgres up -d postgres
docker compose --profile postgres run --rm api flask --app app db upgrade
docker compose --profile postgres run --rm api flask --app app init-db --seed
docker compose --profile postgres up -d
```

Também é possível fornecer uma `DATABASE_URL` completa. Essa variável tem prioridade sobre os campos separados.

## CI/CD no GitHub

O workflow `.github/workflows/ci-cd.yml` executa automaticamente:

1. Testes da API em Python 3.12.
2. Verificação TypeScript e build Vite.
3. Build das imagens Docker.
4. Deploy por SSH quando um commit chega à `main`.

Cadastre estes secrets no environment `production` do GitHub:

- `VM_HOST`: endereço da VM.
- `VM_USER`: usuário SSH.
- `VM_SSH_KEY`: chave privada usada pelo GitHub Actions.
- `VM_SSH_PORT`: porta SSH; use `22` quando não houver alteração.
- `VM_APP_PATH`: caminho absoluto do clone na VM.

A VM precisa ter Git, Docker e o plugin Docker Compose. O repositório deve estar previamente clonado no caminho indicado, na branch `main`, e o usuário do deploy precisa ter permissão para executar Docker.

O deploy usa `git pull --ff-only`, reconstrói os containers e a API executa `flask db upgrade` antes de iniciar o Gunicorn. Alterações de schema passam a ser aplicadas por migrations versionadas.

## API de fichas técnicas

Rotas principais:

- `GET/POST /api/fichas-tecnicas`
- `GET/PUT/DELETE /api/fichas-tecnicas/{id}`
- `GET /api/fichas-tecnicas/fases`

Regras aplicadas:

- Insumos não podem possuir ficha técnica.
- Um produto possui no máximo uma ficha.
- O produto resultante não pode ser componente de si mesmo.
- Componentes e fases precisam existir e estar ativos quando aplicável.
- Ordem de fase e componente não podem se repetir.
- Componentes só podem apontar para fases da própria ficha.
- A atualização de cabeçalho, fases e componentes ocorre na mesma transação.
- Fichas com histórico de produção não podem ser excluídas.

## Testes

```bash
pytest -q
```

Cada teste cria um SQLite temporário. O arquivo `data/app.db` não é alterado.

## Fase 8.3 — domínio consolidado

A aplicação usa uma única representação para cada conceito central: `Produto`, `estoque.Lote`, `FichaTecnica` e `SolicitacaoProducao`. As entidades antigas do GAP (`Item`, `Processamento` e seus filhos) permanecem apenas como referência histórica e não fazem parte do runtime.

`Usuario` agora pertence ao módulo `auth`, enquanto estoque apenas referencia o responsável pelas movimentações. O catálogo também protege invariantes cruzadas: uma mudança de conservação não pode invalidar localizações de lotes existentes e validade obrigatória não pode ser ativada enquanto houver lote sem validade.

A nomenclatura histórica FIFO foi corrigida para FEFO pela migration `8a3c1d4e5f67`. Veja [`docs/FASE8_03.md`](docs/FASE8_03.md) para as decisões e validações desta etapa.


## Fase 8.4 — planejamento de produção

`SolicitacaoProducao` agora representa um planejamento operacional, sem criar uma segunda entidade de processamento. Além da ficha e do usuário solicitante, a solicitação registra quantidade planejada, prioridade, horário previsto, responsável, observação e horário real de início.

O contrato antigo continua compatível: se `quantidade_planejada` não for enviada, o backend usa o rendimento original da ficha. Ao informar uma quantidade diferente, os componentes são escalados pela razão `quantidade_planejada / rendimento_da_ficha`.

Exemplo: uma ficha com rendimento 10 e 5 kg de um componente, quando planejada para 20 unidades, gera 10 kg como `quantidade_prevista` do componente.

A migration `b7d9e2f4a610` adiciona os campos de planejamento e preenche solicitações antigas usando o rendimento da ficha correspondente. Veja [`docs/FASE8_04.md`](docs/FASE8_04.md).

## Fase 8.5 — execução real da produção

A produção agora separa explicitamente **planejado × realizado**. `SolicitacaoProducao` ganhou `quantidade_produzida` e `observacao_execucao`; `SpFase` ganhou snapshot histórico do nome da fase, observação e horários de início/fim. O endpoint `PUT /api/producao/solicitacoes/{id}/execucao` registra o realizado apenas enquanto a produção está `EM_PRODUCAO`.

A migration `c4e8f1a2b730` faz backfill do snapshot das fases existentes e atualiza `vw_sp_componente` para usar o snapshot. Veja [`docs/FASE8_05.md`](docs/FASE8_05.md).


## Fase 8.6 — integração Produção ↔ Estoque

A transição `EM_PRODUCAO → CONCLUIDA` agora é uma operação transacional de domínio. Antes de concluir, o backend lê os `SpComponente` planejados, bloqueia os lotes utilizáveis, ignora lotes vencidos e monta a baixa automática em ordem **FEFO (First Expired, First Out)**. Cada parcela consumida gera uma `MovimentacaoEstoque` do tipo `CONSUMO_PRODUCAO`, vinculada à `SolicitacaoProducao` e ao `SpComponente` correspondente.

O usuário responsável pela baixa é obtido da sessão autenticada (`g.usuario.id`), não de um identificador fornecido pelo cliente. Se qualquer componente não tiver saldo suficiente, a conclusão retorna `409`, nenhum lote é alterado, nenhum movimento parcial permanece e a solicitação continua `EM_PRODUCAO`. Tentativas repetidas de concluir uma produção já concluída não geram novo consumo.

Esta fase não altera o schema: os campos `solicitacao_producao_id`, `sp_componente_id` e o tipo `CONSUMO_PRODUCAO` já existiam. O head do Alembic permanece `c4e8f1a2b730`. Veja [`docs/FASE8_06.md`](docs/FASE8_06.md).

## Fase 8.7 — produto acabado e perdas

A conclusão de uma produção agora fecha o ciclo de estoque: consumo FEFO dos componentes, criação do lote produzido e movimentação `PRODUCAO` ocorrem na mesma transação. O status aceita `localizacao_destino_id` opcional; se omitido, a API seleciona uma localização compatível.

Perdas de ingrediente podem ser registradas no payload de execução e viram movimentações `PERDA` auditáveis. A resposta da solicitação também expõe `perda_rendimento`, calculada pela diferença positiva entre quantidade planejada e produzida. Consulte `docs/FASE8_07_PRODUTO_FINAL_PERDAS.md`.

## Fase 8.8 — Frontend de produção integrado

A tela React de produção foi conectada aos contratos de planejamento e execução do backend. Agora é possível planejar quantidade/prioridade/horário/responsável, acompanhar planejado × realizado, registrar tempos e perdas, informar quantidade produzida e escolher o local de destino antes da conclusão.

Também foi adicionado `GET /api/auth/responsaveis` para OWNER/ADMIN e liberada somente a leitura de localizações para o perfil de cozinha, necessária para o destino do produto acabado. Detalhes em `docs/FASE8_08_FRONTEND.md`.

## Fase 8.9 — hardening

A aplicação agora possui primeiro acesso com troca obrigatória de senha, política mínima de senha forte, bloqueio temporário após falhas repetidas de login, trilha de auditoria e validação de configuração de produção. Movimentações manuais de estoque usam sempre a identidade da sessão autenticada, mesmo que clientes antigos ainda enviem `usuario_id`.

Em `APP_ENV=production`, o startup rejeita SQLite, `SECRET_KEY` insegura, cookie sem `Secure` e senhas bootstrap conhecidas. Consulte [`docs/FASE8_09_HARDENING.md`](docs/FASE8_09_HARDENING.md). A migration correspondente é `e7f8a9b0c1d2`.

## Fase 9 — integração completa

A integração de ponta a ponta está coberta por `tests/test_e2e_fluxo_completo.py`. O cenário atravessa autenticação e primeiro acesso, planejamento, execução, perdas, consumo FEFO, conclusão, geração do lote final, inventário e auditoria.

Resultado da Fase 9 no ambiente de validação: **71 testes funcionais + 3 testes de migrations = 74 testes passando**. Consulte `docs/FASE9_INTEGRACAO_COMPLETA.md` para o cenário completo e as limitações de PostgreSQL deste ambiente.

## Hotfix — transferência por localização

A transferência de estoque agora recebe diretamente uma **localização de destino** no frontend. O backend cria ou reutiliza automaticamente um lote compatível, preservando produto, data de produção, validade e custo do lote de origem. O contrato antigo com `lote_destino_id` continua aceito para compatibilidade.

Consulte `docs/HOTFIX_TRANSFERENCIA_LOCALIZACAO.md` para os detalhes.

## Hotfix — transformação inteligente

A transformação de estoque não exige mais um lote de destino criado manualmente. A interface permite escolher o produto resultante e a localização; o backend cria ou reaproveita um lote compatível, calcula validade/custo, registra rendimento e mantém compatibilidade com `lote_destino_id`. Veja `docs/HOTFIX_TRANSFORMACAO_INTELIGENTE.md`.

