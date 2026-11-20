# Praças — arquitetura, API e operação

## Objetivo e escopo

`Praca` representa uma estação operacional de cozinha, como Grelha, Saladas ou
Sobremesas. Ela **não** é uma `Localizacao` de estoque: localização define onde
um lote fica armazenado; praça define onde a equipe atua e organiza preparos.

Esta documentação descreve o código entregue nas fases 1–4 e os testes/documentação
acrescentados na fase 5. **Não é um atestado de homologação ou de deploy em produção.**

## Modelo de dados

- `praca`: `id` (PK), `nome` (obrigatório e único sem distinguir caixa),
  `descricao` (opcional), `ativo` (`0`/`1`), `criado_em`.
- `praca_usuario`: `praca_id` e `usuario_id` (PK composta, FKs). O vínculo
  com `Usuario` é N:N: um cozinheiro pode integrar várias praças.
- `solicitacao_producao.praca_id`: FK opcional para `praca.id`. Cada solicitação
  pode estar ligada a **uma** praça; uma praça pode receber muitas solicitações.
  O campo aceita `NULL` para compatibilidade com dados antigos.

Não existe model `Cozinheiro`: a equipe é formada por usuários ativos vinculados
ao grupo de acesso `Cozinha`.

### Invariantes da gestão de praças

1. A criação exige nome com 2–120 caracteres e ao menos um cozinheiro ativo
   do grupo `Cozinha`.
2. Associações repetidas, nomes de praça duplicados e IDs inválidos são rejeitados.
   O nome é comparado sem diferenciar maiúsculas/minúsculas e também possui
   índice de unicidade no banco.
3. A equipe pode mudar durante a edição, mas não pode ficar vazia.
4. Usuários não podem ser desativados ou perder o grupo `Cozinha` quando isso
   deixaria uma praça **ativa** sem cozinheiro elegível.
5. Desativar uma praça é uma operação lógica (`ativo=0`), não um `DELETE`
   físico. A API mantém as associações e o histórico da produção.
6. Reativar exige que haja equipe elegível naquele momento.

### Regras de produção

- A criação pode omitir `praca_id` ou informar uma praça ativa com pelo menos um
  cozinheiro ativo do grupo `Cozinha`.
- Atribuição, troca ou remoção de praça só são permitidas nos estados `ABERTA`
  e `EM_SEPARACAO`. Nos estados `EM_PRODUCAO`, `CONCLUIDA` e `CANCELADA`, a
  realocação é bloqueada com HTTP 409.
- A desativação de uma praça **após** o planejamento preserva `praca_id`,
  permite consultar o vínculo histórico e não bloqueia a continuação de
  solicitações previamente atribuídas.
- O filtro de solicitações por praça é uma facilidade de consulta, **não**
  restringe a autorização do cozinheiro autenticado por praça. Essa restrição
  não foi incluída no requisito implementado.
- As regras de FEFO, consumo de ingredientes, geração de lote final e histórico
  de movimentações permanecem na camada de produção/estoque. A nova FK não
  substitui nem altera a localização de armazenamento do produto final.

## API REST

A API usa sessão autenticada e o mesmo padrão JSON e de paginação das demais
features. Listagens são envelopes `items`, `page`, `per_page`, `total`, `pages`.

| Método | Rota | Permissão | Função |
| --- | --- | --- | --- |
| GET | `/api/pracas` | `pracas:ler` | Lista praças ativas e inativas |
| GET | `/api/pracas/{id}` | `pracas:ler` | Consulta praça |
| GET | `/api/pracas/cozinheiros` | `pracas:ler` | Lista usuários elegíveis |
| POST | `/api/pracas` | `pracas:criar` | Cria praça |
| PUT | `/api/pracas/{id}` | `pracas:atualizar` | Atualiza praça, equipe ou situação |
| DELETE | `/api/pracas/{id}` | `pracas:excluir` | Desativa, sem apagar |
| POST | `/api/producao/solicitacoes` | `producao:criar` | Aceita `praca_id` opcional |
| GET | `/api/producao/solicitacoes` | `producao:ler` | Aceita `?praca_id=N` |
| GET | `/api/producao/solicitacoes/{id}` | `producao:ler` | Inclui resumo da praça |
| PUT | `/api/producao/solicitacoes/{id}/praca` | `producao:criar` | Realoca ou desatribui antes da execução |

**Exceção de permissão:** a rota de realocação é `PUT`, mas exige
`producao:criar` porque altera o planejamento; não basta
`producao:atualizar` (ação de andamento disponível à Cozinha).

### Exemplos de payload

Cadastro de praça:

```json
{
  "nome": "Grelha",
  "descricao": "Estação de grelhados",
  "cozinheiros": [3, 7]
}
```

Atualização parcial de praça:

```json
{
  "nome": "Grelha e finalização",
  "cozinheiros": [3, 8],
  "ativo": 1
}
```

Criação de uma solicitação vinculada:

```json
{
  "ficha_tecnica_id": 1,
  "quantidade_planejada": 20,
  "localizacao_destino_id": 2,
  "praca_id": 1
}
```

Uma solicitação retorna `praca_id` e `praca` com `id`, `nome`, `ativo`;
ambos são `null` se não houver praça. O nome histórico continua disponível
mesmo quando a praça se tornar inativa.

Remoção do vínculo antes de começar a produção:

```http
PUT /api/producao/solicitacoes/15/praca
Content-Type: application/json

{"praca_id": null}
```

Para trocar, envie `{"praca_id": 2}`. O campo `praca_id` é **obrigatório**
nesse `PUT`, mesmo quando seu valor é `null`.

Códigos HTTP mais relevantes: `201` na criação, `200` em leituras/edições,
`204` na desativação, `400` em validações, `401` sem sessão, `403` sem
permissão, `404` em recurso ausente e `409` em conflitos (incluindo realocação
após início). A descrição detalhada dos contratos está em `docs/openapi.yaml`
e pode ser consultada em `/docs` com a aplicação iniciada.

## Interface React

- `/pracas` lista, pesquisa, cadastra, edita e ativa/desativa praças;
  os botões seguem as permissões disponíveis na sessão.
- A escolha de cozinheiros é múltipla. A lista vem de
  `GET /api/pracas/cozinheiros`, evitando exigir `usuarios:ler`.
- Em `/producao`, o planejador oferece praça opcional, a fila exibe a praça
  vinculada, há filtro local e a realocação é oferecida somente antes da execução.
- Praças inativas continuam aparecendo em históricos. Sem permissão para ler
  praças, a tela de produção funciona com a lista existente sem carregar
  `/api/pracas`.

## Inicialização, migração e permissões

**Não apague o banco.** O comando `flask --app app init-db` usa o mecanismo
existente de criação e migração incremental. Para banco antigo, a evolução da
Fase 1 adiciona `solicitacao_producao.praca_id` opcional, o índice da FK e
as novas tabelas. Para um banco novo, `db.create_all()` as cria.

Antes de executar em ambiente que contenha dados importantes: confira
`DATABASE_URL` e variáveis `DB_*`, faça um backup recuperável e teste a
atualização em uma cópia. Não execute `--seed` indiscriminadamente em banco
existente. Em PostgreSQL, também valide as permissões do usuário de banco
para criar índices e adicionar colunas.

Em bancos novos, os grupos padrão ficam configurados para: Administrador
(todas as operações), Gestor (gerenciamento de praças) e Cozinha (leitura).
**Em bancos já existentes, `init-db` registra as novas permissões no catálogo,
mas não sobrescreve os vínculos de grupos personalizados/antigos.** Um
administrador deve revisar e conceder explicitamente `pracas:ler`,
`pracas:criar`, `pracas:atualizar`, `pracas:excluir` conforme a política local.

## Validação antes do Pull Request

Com as dependências Python instaladas e com o banco **temporário de testes**:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_pracas_modelagem.py tests/test_pracas_api.py tests/test_producao_pracas.py tests/test_pracas_documentacao.py
.\.venv\Scripts\python.exe -m pytest -q
```

Para checar TypeScript e build real com os pacotes do lockfile:

```powershell
cd frontend
pnpm install --frozen-lockfile
pnpm exec tsc --noEmit
pnpm run build
```

Validação manual recomendada em ambiente descartável:

1. Criar praça com dois cozinheiros; editar e remover um vínculo.
2. Tentar criar praça sem cozinheiro, com usuário inativo e com nome duplicado.
3. Testar grupos Gestor/Cozinha e um usuário sem `pracas:ler`.
4. Criar produção com e sem praça; filtrar e conferir o detalhe.
5. Realocar em `ABERTA` e `EM_SEPARACAO`; conferir HTTP 409 após iniciar.
6. Desativar uma praça com produção vinculada; verificar histórico e conclusão.
7. Simular falta de estoque e verificar ausência de baixas parciais; depois
   prover insumos e concluir; repetir conclusão e checar ausência de duplicação.
8. Testar a migração em cópias de bancos SQLite e PostgreSQL com dados legados.
9. Validar responsividade, teclado e mensagens de erro na UI.

**Condição de aprovação:** suíte Pytest, `tsc`, build Vite, cenários manuais e
migração PostgreSQL devem ter resultados registrados; a aprovação para produção
não decorre apenas da presença de código ou endpoints.
