# 🍳 Machry — Cozinha Mais

> Sistema integrado de **produção, fichas técnicas, estoque, lotes, localizações, usuários e rastreabilidade** para operação de restaurante.
>
> Este README registra a grande integração realizada entre **31/10/2026 e 01/11/2026**, as decisões arquiteturais tomadas, as fases implementadas, os hotfixes encontrados durante uso real e a relação dessas entregas com as quests do Trello.

---

## 📌 Estado atual do projeto

| Área | Estado |
|---|---|
| Backend Flask modular | ✅ Implementado |
| Frontend React + TypeScript | ✅ Integrado |
| Catálogo de produtos | ✅ Implementado |
| Fichas técnicas | ✅ Implementado |
| Estoque por lotes | ✅ Implementado |
| FEFO | ✅ Implementado |
| Planejamento de produção | ✅ Implementado |
| Execução real da produção | ✅ Implementado |
| Produção ↔ Estoque | ✅ Implementado |
| Produto acabado | ✅ Implementado |
| Perdas de ingredientes | ✅ Implementado |
| Transferências por localização | ✅ Implementado |
| Transformações de estoque | ✅ Implementado / melhorado |
| Usuários e permissões | ✅ Implementado |
| Primeiro acesso / troca de senha | ✅ Implementado |
| Auditoria | ✅ Implementado |
| Migrations com Alembic | ✅ Implementado |
| E2E principal | ✅ Implementado |
| PostgreSQL em Docker | 🟡 Preparado; validação operacional final ainda necessária |
| HTTPS + domínio | ⏳ Pendente de ambiente de produção |
| Backup/restore de produção | ⏳ Pendente |
| Alertas operacionais | ⏳ Pendente |
| Inventário físico/contagem | ⏳ Pendente |

---

# 📚 Sumário

1. [Visão geral](#-visão-geral)
2. [Tecnologias](#-tecnologias)
3. [Arquitetura atual](#-arquitetura-atual)
4. [Decisões arquiteturais da integração](#-decisões-arquiteturais-da-integração)
5. [Linha do tempo das fases implementadas](#-linha-do-tempo-das-fases-implementadas)
   - [Fase 8.1 — Estabilização da base](#fase-81--estabilização-da-base)
   - [Fase 8.2 — Migrations](#fase-82--migrations)
   - [Fase 8.3 — Consolidação do domínio](#fase-83--consolidação-do-domínio)
   - [Fase 8.4 — Planejamento de produção](#fase-84--planejamento-de-produção)
   - [Fase 8.5 — Execução real](#fase-85--execução-real)
   - [Fase 8.6 — Produção ↔ Estoque](#fase-86--produção--estoque)
   - [Fase 8.7 — Produto final e perdas](#fase-87--produto-final-e-perdas)
   - [Fase 8.8 — Frontend e contratos](#fase-88--frontend-e-contratos)
   - [Fase 8.9 — Hardening](#fase-89--hardening)
   - [Fase 9 — Integração completa](#fase-9--integração-completa)
6. [Hotfixes após uso real](#-hotfixes-após-uso-real)
7. [Fluxos de negócio atuais](#-fluxos-de-negócio-atuais)
8. [Mapeamento das quests do Trello](#-mapeamento-das-quests-do-trello)
9. [Como executar — Windows + SQLite](#-como-executar--windows--sqlite)
10. [Como executar os testes](#-como-executar-os-testes)
11. [Como executar com Docker + PostgreSQL](#-como-executar-com-docker--postgresql)
12. [Migrations](#-migrations)
13. [Usuários, seed e primeiro acesso](#-usuários-seed-e-primeiro-acesso)
14. [Como resetar o banco](#-como-resetar-o-banco)
15. [URLs e endpoints úteis](#-urls-e-endpoints-úteis)
16. [Troubleshooting](#-troubleshooting)
17. [Testes e evolução da cobertura](#-testes-e-evolução-da-cobertura)
18. [O que ainda falta](#-o-que-ainda-falta)

---

# 🧭 Visão geral

O **Machry / Cozinha Mais** é um sistema operacional para restaurante focado em dois domínios que precisam conversar constantemente:

```text
PRODUÇÃO  ←────────→  ESTOQUE
```

A aplicação controla:

- insumos;
- produtos intermediários;
- produtos finais;
- fichas técnicas;
- fases de preparo;
- planejamento diário de produção;
- execução real do que foi produzido;
- lotes e validades;
- locais de armazenamento;
- entradas, saídas, ajustes, transferências e transformações;
- consumo automático de ingredientes;
- perdas;
- geração automática do lote do produto acabado;
- usuários, perfis, sessão e auditoria.

Durante a integração, o objetivo deixou de ser manter projetos paralelos e passou a ser construir **um único sistema coerente**, reaproveitando o que havia de melhor nas implementações existentes.

> Este README começa na etapa em que as informações e projetos já haviam sido reunidos. As fases puramente relacionadas a coletar/fornecer dados, arquivos, conversas e históricos para análise foram propositalmente omitidas.

---

# 🛠️ Tecnologias

## Backend

- Python 3.12+
- Flask 3
- Flask-SQLAlchemy
- Flask-Migrate
- Alembic
- Pydantic / Pydantic Settings
- Werkzeug Security
- Gunicorn
- psycopg2-binary

## Frontend

- React 19
- TypeScript
- Vite

## Banco

- SQLite para desenvolvimento local e testes isolados;
- PostgreSQL preparado para ambiente integrado/produção.

## Infraestrutura

- Docker
- Docker Compose
- GitHub Actions
- OpenAPI / Swagger

## Testes

- pytest
- Flask test client
- migrations smoke/round-trip tests
- cenário E2E de domínio

---

# 🏗️ Arquitetura atual

A arquitetura final é um **monólito modular Flask** com frontend React separado.

```text
┌──────────────────────────────────────────────┐
│             React + TypeScript               │
│                frontend/                     │
└──────────────────────┬───────────────────────┘
                       │ HTTP / JSON
                       ▼
┌──────────────────────────────────────────────┐
│                  Flask API                   │
│                    /api                      │
│                                              │
│  auth      produtos      fichas_tecnicas    │
│    │           │                │            │
│    └───────────┼────────────────┤            │
│                │                │            │
│             producao ─────── estoque         │
└──────────────────────┬───────────────────────┘
                       │
                    SQLAlchemy
                       │
               ┌───────┴────────┐
               │                │
             SQLite         PostgreSQL
          desenvolvimento    produção
```

Estrutura principal:

```text
app/
├── features/
│   ├── auth/
│   │   ├── models.py
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   └── security.py
│   ├── produtos/
│   │   ├── models.py
│   │   ├── repository.py
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   └── services.py
│   ├── fichas_tecnicas/
│   ├── estoque/
│   └── producao/
└── utils/
    ├── config.py
    ├── errors.py
    └── parsing.py

frontend/
migrations/
tests/
docs/
db/
```

Cada feature segue, quando necessário:

```text
Route
  ↓
Service
  ↓
Repository
  ↓
SQLAlchemy
  ↓
Banco
```

## Por que não separar Produção e Estoque em duas APIs?

Essa foi uma das decisões mais importantes da integração.

Concluir uma produção pode precisar executar, de forma indivisível:

```text
validar produção
→ verificar estoque
→ selecionar lotes FEFO
→ consumir ingredientes
→ registrar perdas
→ criar lote final
→ registrar entrada do produto produzido
→ concluir produção
```

Se Produção e Estoque fossem serviços independentes, essa operação exigiria consistência distribuída, tratamento de falhas de rede, compensações e uma complexidade desnecessária para o tamanho atual do sistema.

No monólito modular podemos usar uma única transação de banco:

```text
BEGIN
...
COMMIT
```

ou, em qualquer erro:

```text
ROLLBACK
```

Assim evitamos situações como:

```text
ingrediente baixado ✅
produto final não criado ❌
produção ficou incompleta ❌
```

---

# 🧠 Decisões arquiteturais da integração

## 1. Cozinha Mais como base estrutural; GAP como fonte de regras

A estrutura modular mais recente do Cozinha Mais foi adotada como base do runtime.

O GAP não virou uma segunda API. Em vez disso, regras úteis foram incorporadas ao domínio consolidado.

Resultado:

```text
Cozinha Mais = estrutura
GAP          = regras e conceitos reaproveitados
```

## 2. `Produto` é o catálogo oficial

A entidade antiga `Item` não foi mantida paralelamente.

```text
Item ❌
Produto ✅
```

Isso evita dois cadastros diferentes descrevendo a mesma coisa.

## 3. Existe apenas um `Lote`

O lote oficial pertence ao módulo de estoque.

Seu saldo deve ser alterado por regras de estoque e movimentações, e não por um CRUD paralelo.

```text
Produto
  ↓
Lote
  ↓
MovimentacaoEstoque
```

## 4. Movimentação é a trilha de auditoria do estoque

Entradas e saídas relevantes devem deixar rastros.

Tipos atualmente usados incluem:

```text
ENTRADA
SAIDA
AJUSTE_ENTRADA
AJUSTE_SAIDA
TRANSFERENCIA
TRANSFORMACAO
CONSUMO_PRODUCAO
PRODUCAO
PERDA
```

## 5. `Processamento` não foi recriado como domínio paralelo

Os conceitos úteis do processamento antigo foram absorvidos por:

```text
SolicitacaoProducao
SpFase
SpComponente
MovimentacaoEstoque
```

Isso evita:

```text
SolicitacaoProducao
      +
Processamento
```

representando o mesmo evento em estruturas diferentes.

## 6. Pydantic foi mantido como framework de schemas

Não misturamos Marshmallow e Pydantic no mesmo runtime.

A base já utilizava Pydantic e mantê-lo reduz duplicidade conceitual.

## 7. O Repository Pattern foi mantido

No GAP isolado um repository extra poderia ser só cerimônia. Na base integrada ele já existia e possui papel real de persistência, consultas e bloqueios.

Por isso foi mantido.

## 8. Migrations vieram antes das grandes mudanças de schema

Antes de adicionar campos de planejamento, execução e segurança, introduzimos Alembic.

A regra passou a ser:

```text
models = estado desejado
migrations = caminho seguro até esse estado
```

## 9. FEFO, não FIFO

O sistema usa validade como prioridade.

Logo o termo correto é:

**FEFO — First Expired, First Out**

```text
vence primeiro → sai primeiro
sem validade   → fica por último
vencido        → não é selecionado automaticamente
```

A nomenclatura histórica `FIFO` foi removida de view e índice.

## 10. Planejado e realizado são informações diferentes

Nunca sobrescrevemos o planejamento com a execução.

Exemplo:

```text
Planejado: 20 unidades
Produzido:  18 unidades
```

Os dois valores devem continuar existindo.

O mesmo vale para tempos:

```text
Tempo previsto: 30 min
Tempo realizado: 42 min
```

Isso permite comparar expectativa e realidade.

## 11. Snapshot histórico das fases

Se uma fase chamada `Cocção` for renomeada amanhã, uma produção feita ontem não pode mudar retroativamente.

Por isso `SpFase` guarda um snapshot do nome da fase no momento do planejamento.

## 12. Estoque é a fonte de verdade do consumo real

A quantidade efetivamente utilizada de um componente deriva das movimentações relacionadas à produção.

```text
quantidade_realizada
=
CONSUMO_PRODUCAO
+
PERDA
```

## 13. Perda física e perda de rendimento são conceitos diferentes

### Perda de ingrediente

Exemplo:

```text
20 g derramados
```

É estoque real que desapareceu.

Logo gera:

```text
MovimentacaoEstoque(PERDA)
```

### Perda de rendimento

Exemplo:

```text
planejado: 1,00 kg
produzido: 0,95 kg
```

Os `0,05 kg` nunca chegaram a existir como produto acabado.

Logo são calculados como:

```text
max(planejado - produzido, 0)
```

sem criar uma saída fictícia do produto final.

## 14. O cliente não escolhe quem fez uma movimentação

O frontend não é uma fonte confiável para autoria.

Portanto:

```text
usuario_id enviado pelo cliente → ignorado para autoria
```

O backend usa:

```text
g.usuario.id
```

## 15. Compatibilidade foi preservada sempre que possível

Ao evoluir contratos, evitamos quebrar clientes antigos.

Exemplos:

- produção ainda aceita somente `ficha_tecnica_id`;
- transferência antiga ainda pode usar `lote_destino_id`;
- transformação antiga ainda pode usar `lote_destino_id`;
- novos campos são adicionados progressivamente.

---

# 🚀 Linha do tempo das fases implementadas

## Fase 8.1 — Estabilização da base

Antes de alterar o domínio, congelamos o comportamento existente.

### O que foi feito

- base estrutural definida;
- endpoints utilizados pelo frontend protegidos por testes;
- teste de produção deixou de inserir registros diretamente no banco e passou a usar a API pública;
- arquitetura feature-oriented preservada;
- contratos `/api/*` tratados como dependência real do frontend.

### Decisão

Não fazia sentido iniciar a integração modificando tudo ao mesmo tempo.

Primeiro criamos uma baseline que pudesse dizer:

> “Isto funcionava antes da mudança.”

### Evolução dos testes

```text
23 testes existentes
→ 29 testes após estabilização
```

---

## Fase 8.2 — Migrations

O schema passou a ser controlado por:

```text
Flask-Migrate + Alembic
```

### O que mudou

- `Migrate` integrado ao Application Factory;
- pasta `migrations/` criada;
- baseline do schema criada;
- tabelas, constraints, índices e views passaram a ser versionados;
- `run.bat` e `run.sh` aplicam `db upgrade` antes do bootstrap;
- Docker aplica migrations antes do Gunicorn;
- `init-db` deixou de ser responsável por criar schema em produção;
- `db.create_all()` ficou restrito ao ambiente de testes.

### Por quê?

Sem migrations, cada mudança de model corria risco de exigir:

```text
apagar banco
→ criar tudo de novo
```

Isso é aceitável em protótipo, mas não em sistema com dados reais.

---

## Fase 8.3 — Consolidação do domínio

Foi eliminada a ambiguidade entre conceitos duplicados.

### Fonte única por conceito

```text
Produto              ✅
estoque.Lote         ✅
FichaTecnica         ✅
SolicitacaoProducao  ✅

Item                 ❌
Processamento        ❌ como entidade paralela
```

### `Usuario` saiu do estoque

Usuário é autenticação/identidade, não estoque.

Ele foi movido conceitualmente para:

```text
app.features.auth
```

O estoque apenas referencia o responsável.

### Consistência Produto × Estoque

Passamos a impedir alterações no catálogo que deixariam lotes existentes inválidos.

Exemplos:

- mudar conservação para um tipo incompatível com o local atual do lote;
- exigir validade quando já existem lotes sem validade.

### FIFO → FEFO

Renomeamos a estrutura para refletir a regra realmente utilizada.

---

## Fase 8.4 — Planejamento de produção

`SolicitacaoProducao` deixou de ser apenas uma fila simples.

Ela passou a registrar:

```text
quantidade_planejada
prioridade
previsto_para
responsavel_id
observacao
iniciado_em
```

### Solicitante ≠ responsável

Mantivemos duas responsabilidades separadas:

```text
usuario_id     = quem criou o planejamento
responsavel_id = quem deve executar
```

### Escala automática da ficha

A fórmula é:

```text
fator = quantidade_planejada / rendimento_da_ficha
quantidade_prevista = quantidade_da_ficha × fator
```

Exemplo:

```text
Ficha rende 10
Farinha: 5 kg

Produção solicitada: 20

fator = 20 / 10 = 2
farinha = 5 × 2 = 10 kg
```

Assim a cozinha recebe uma ficha proporcional à produção realmente desejada.

---

## Fase 8.5 — Execução real

Foi introduzida a comparação **planejado × realizado**.

### Produção

```text
quantidade_planejada
quantidade_produzida
```

### Fases

Cada fase pode registrar:

```text
tempo_previsto_min
tempo_realizado_min
iniciado_em
finalizado_em
observacao
fase_nome_snapshot
```

### Endpoint de execução

```http
PUT /api/producao/solicitacoes/{id}/execucao
```

A execução somente pode ser alterada enquanto a produção está `EM_PRODUCAO`.

---

## Fase 8.6 — Produção ↔ Estoque

Aqui ocorreu uma das principais integrações de negócio.

Ao concluir uma produção, o sistema passou a consumir ingredientes automaticamente.

### Fluxo

```text
EM_PRODUCAO
    ↓
CONCLUIR
    ↓
validar componentes
    ↓
validar estoque
    ↓
selecionar FEFO
    ↓
CONSUMO_PRODUCAO
    ↓
CONCLUIDA
```

### Atomicidade

A operação é transacional.

Se faltar um único ingrediente:

```text
ROLLBACK
```

Nada fica parcialmente consumido.

### Idempotência

Uma produção concluída não pode consumir novamente os mesmos ingredientes em um retry.

### Estoque insuficiente

Retorna conflito de negócio, não erro interno:

```http
409 Conflict
```

---

## Fase 8.7 — Produto final e perdas

A conclusão passou a fechar o ciclo completo.

```text
ingredientes
→ consumo FEFO
→ produção
→ lote do produto acabado
→ movimentação PRODUCAO
```

### Produto final

A API cria automaticamente um lote para a quantidade realmente produzida.

Também calcula validade quando o produto possui `validade_padrao_dias`.

### Localização final

Pode ser informada pelo cliente.

Se não for informada, o backend possui fallback para uma localização compatível.

### Perdas de ingredientes

Perdas físicas são registradas como:

```text
PERDA
```

com:

- produção;
- componente;
- quantidade;
- motivo;
- usuário autenticado.

### Perda de rendimento

É mostrada como diferença entre planejado e produzido, sem criar estoque inexistente.

---

## Fase 8.8 — Frontend e contratos

O React passou a utilizar os recursos criados nas fases anteriores.

### Planejamento pela interface

É possível informar:

- ficha;
- quantidade;
- prioridade;
- data/hora;
- responsável;
- observação.

### Execução pela interface

A cozinha consegue registrar:

- quantidade produzida;
- tempo real das fases;
- início e fim;
- observações;
- perdas.

### Visualização

A tela exibe:

```text
planejado × realizado
```

para:

- produção;
- componentes;
- fases.

Também existe impressão da fila de produção.

### Endpoint de responsáveis

Foi criado um endpoint somente de leitura para planejamento:

```http
GET /api/auth/responsaveis
```

ADMIN e OWNER podem listar usuários ativos sem ganhar acesso indevido ao CRUD administrativo.

---

## Fase 8.9 — Hardening

Antes do E2E, fechamos riscos básicos de segurança.

### Primeiro acesso

Usuários criados ou resetados podem ser obrigados a trocar a senha.

Enquanto isso, o restante da API permanece bloqueado.

### Política de senha

A nova senha exige combinação de:

- maiúscula;
- minúscula;
- número;
- caractere especial.

### Brute force

Depois de falhas consecutivas de login:

```text
conta bloqueada temporariamente
```

Parâmetros:

```env
LOGIN_MAX_FAILURES
LOGIN_LOCK_MINUTES
```

### Auditoria

Eventos importantes passam a ser registrados.

Exemplos:

```text
LOGIN_SUCESSO
LOGIN_FALHA
LOGOUT
SENHA_ALTERADA
administração de usuário
```

### Headers

Foram adicionados headers de segurança e rastreabilidade, incluindo `X-Request-ID`.

### Proteção de produção

Quando `APP_ENV=production`, a aplicação rejeita configurações perigosas como:

- SQLite;
- `SECRET_KEY` fraca/default;
- cookie sem `Secure`;
- senhas bootstrap inseguras.

---

## Fase 9 — Integração completa

Foi criado um cenário E2E que atravessa a API como um usuário real.

### Cenário

```text
OWNER faz login
→ cria usuário da cozinha
→ abastece estoque
→ cria produção
→ COZINHA faz primeiro login
→ troca senha
→ inicia produção
→ registra execução
→ registra perda
→ conclui
→ FEFO consome ingredientes
→ produto final entra no estoque
→ OWNER verifica inventário
→ OWNER verifica movimentos
→ OWNER verifica auditoria
```

### FEFO validado no cenário

Exemplo utilizado:

```text
Lote A: 100 ml, vence primeiro
Lote B: 250 ml, vence depois

Perda antes da conclusão: 10 ml do lote A
Necessidade da produção: 300 ml

FEFO:
Lote A → 90 ml
Lote B → 210 ml

Saldo final lote B → 40 ml
```

### Produto acabado

```text
Planejado: 1,00
Produzido: 0,95
Perda de rendimento: 0,05
```

O sistema cria lote final de `0,95` e registra `PRODUCAO`.

---

# 🐛 Hotfixes após uso real

Os testes automatizados foram importantes, mas o uso manual revelou situações que mereciam tratamento mais elegante.

## Hotfix 1 — Exclusão de localização retornando HTTP 500

### Problema encontrado

Ao excluir `Cozinha`, o banco podia receber uma tentativa de exclusão enquanto outra localização ainda dependia dela:

```text
Cozinha
└── Geladeira da Cozinha
```

A foreign key explodia no banco e aparecia para o usuário como:

```http
500 Internal Server Error
```

### Correção

O backend agora valida antes do DELETE.

Se a localização:

- possui sub-localizações; ou
- possui lotes vinculados;

retorna:

```http
409 Conflict
```

com erro de negócio compreensível.

### Decisão

Constraint de banco é a última linha de defesa. A aplicação deve detectar uma operação conhecida e devolver uma resposta de domínio, e não expor um erro interno.

---

## Hotfix 2 — Testes dependiam da senha do `.env`

### Problema encontrado

Depois de trocar a senha bootstrap da cozinha no `.env`, dois testes ainda possuíam:

```text
Cozinha@123
```

hardcoded.

Resultado local:

```text
73 passed
2 failed
```

Os dois failures eram `401` no login da cozinha.

### Correção

Os testes passaram a usar a configuração do próprio ambiente de testes:

```python
application.config["COOK_INITIAL_PASSWORD"]
```

Além disso, `tests/conftest.py` ganhou credenciais próprias.

### Decisão

Testes automatizados não devem depender do `.env` pessoal do desenvolvedor.

```text
.env real        ≠ configuração dos testes
```

---

## Hotfix 3 — Transferência exigia lote destino manual

### UX antiga

Para transferir um produto de um local para outro era necessário criar previamente um lote vazio no destino.

```text
Lote origem
→ lote destino já existente
```

Isso fazia o usuário pensar em estrutura de banco quando ele só queria mover mercadoria.

### UX nova

```text
Lote de origem
→ Localização de destino
→ Quantidade
→ Transferir
```

O backend:

1. valida saldo;
2. valida conservação;
3. impede usar a mesma localização;
4. procura lote compatível no destino;
5. reutiliza ou cria um lote;
6. preserva produção, validade e custo;
7. registra `TRANSFERENCIA`;
8. altera os saldos na mesma transação.

### Compatibilidade

`lote_destino_id` continua aceito para clientes antigos.

---

## Hotfix 4 — Transformação inteligente

### UX antiga

A transformação também exigia lote de destino manual.

### UX nova

```text
Lote de origem
→ Produto resultante
→ Localização destino
→ Quantidade usada
→ Quantidade resultante
→ Transformar
```

### Regras

O backend:

1. valida saldo;
2. rejeita lote vencido;
3. valida se a transformação origem → destino foi cadastrada;
4. exige mesma unidade enquanto não houver fator de conversão;
5. valida conservação do produto resultante;
6. calcula validade;
7. não permite que a validade calculada ultrapasse automaticamente a validade da matéria-prima;
8. recalcula custo unitário com base no rendimento;
9. cria ou reutiliza lote final;
10. registra uma única `TRANSFORMACAO`.

### Rendimento

Exemplo:

```text
1000 g → 900 g
```

```text
rendimento = 90%
perda de transformação = 100 g
```

### Por que não criar `PERDA` também?

Porque a movimentação `TRANSFORMACAO` já retira os `1000 g` da origem.

Criar uma `PERDA` adicional de `100 g` baixaria estoque duas vezes.

Logo a perda fica auditável no próprio evento de transformação.

### Regras configuráveis

A interface também passou a permitir cadastrar quais transformações são válidas:

```text
Queijo em bloco → Queijo ralado
Nozes → Creme de nozes
```

Endpoints:

```http
GET    /api/estoque/transformacoes
POST   /api/estoque/transformacoes
DELETE /api/estoque/transformacoes/{produto_origem_id}/{produto_destino_id}
```

---

# 🔄 Fluxos de negócio atuais

## Produção completa

```text
Ficha Técnica
      ↓
Planejamento
      ↓
quantidade + prioridade + horário + responsável
      ↓
SpFase + SpComponente congelam o planejamento
      ↓
EM_PRODUCAO
      ↓
execução real / tempos / observações / perdas
      ↓
CONCLUIR
      ↓
validação de estoque
      ↓
FEFO
      ↓
CONSUMO_PRODUCAO
      ↓
lote do produto final
      ↓
PRODUCAO
      ↓
CONCLUIDA
```

## O que é um lote?

Um lote representa uma quantidade rastreável de um produto.

Exemplo:

```text
Produto: Leite
Lote: #25
Quantidade: 15 L
Produção: 01/11/2026
Validade: 08/11/2026
Localização: Geladeira da Cozinha
Custo unitário: R$ ...
```

O mesmo produto pode possuir vários lotes com:

- validades diferentes;
- custos diferentes;
- datas de produção diferentes;
- locais diferentes;
- saldos diferentes.

É por isso que FEFO opera sobre lotes e não apenas sobre o produto agregado.

## Transferência

Transferência move o **mesmo produto** entre locais.

```text
Lote de Leite — Geladeira
        ↓
      5 L
        ↓
Câmara Fria
```

A identidade rastreável do lote é preservada na criação/reutilização do lote destino.

## Transformação

Transformação converte um produto em outro.

```text
Queijo em bloco
      ↓
Queijo ralado
```

Ela registra quantidade de entrada e quantidade resultante, permitindo calcular rendimento.

## Ajustes

Quando o saldo físico e o sistema precisam ser conciliados, devem ser usados movimentos de ajuste em vez de editar silenciosamente o saldo.

```text
AJUSTE_ENTRADA
AJUSTE_SAIDA
```

---

# 📋 Mapeamento das quests do Trello

> Referência: export do board **Projeto Machry — Gestão Ágil** utilizado durante a integração. O status abaixo representa a avaliação técnica do código atual. Este README não altera automaticamente o board.

## ✅ Cards que podem ser consideradas concluídas tecnicamente

| Quest | Status no export | Situação atual | Evidência principal |
|---|---|---|---|
| **T-DEV-04 — Configurar migrações do banco** | A FAZER | ✅ Concluída | Flask-Migrate + Alembic, baseline, upgrades/downgrades |
| **T-DEV-09 — Implementar entidades e relacionamentos** | A FAZER | ✅ Concluída | Domínio consolidado e migrations versionadas |
| **T-DEV-03 — Automatizar baixa de estoque** | A FAZER | ✅ Concluída | `CONSUMO_PRODUCAO` automático por FEFO |
| **T-DEV-11 — Processamento e atualização do estoque** | EM ANDAMENTO | ✅ Concluída | Movimentações atualizam saldos transacionalmente |
| **T-DEV-12 — Calcular consumo de ingredientes por pedido** | EM ANDAMENTO | ✅ Concluída | Escala de ficha + `SpComponente` + consumo na produção |
| **T-DEV-14 — Gerenciamento de lotes e validades** | EM ANDAMENTO | ✅ Concluída | Lotes, validade, FEFO, bloqueio de vencidos e rastreabilidade |
| **T-DEV-08 — Visualização da ficha de produção** | A FAZER | ✅ Tecnicamente atendida | Detalhe de produção, ingredientes, fases, observações e impressão |
| **T-DEV-05 — Implementar entradas e saídas** | BACKLOG | ✅ Funcionalidade existente | ENTRADA, SAIDA, ajustes e histórico |
| **US-DEV-01 — Gerenciar usuários pelo frontend** | EM ANDAMENTO | ✅ Concluída | Tela OWNER para criar/editar/desativar/resetar |
| **US-DEV-02 — Planejar produção diária** | EM ANDAMENTO | ✅ Concluída | Quantidade, prioridade, horário, responsável e observação |
| **US-DEV-03 — Integrar produção e estoque** | EM ANDAMENTO | ✅ Concluída | Estoque suficiente, FEFO, consumo, perda, produto final e idempotência |
| **US-DEV-04 — Histórico de movimentações** | EM ANDAMENTO | ✅ Concluída | Tela com filtros por produto, lote, tipo, usuário e data |
| **US-DEV-06 — Troca e redefinição de senhas** | EM ANDAMENTO | ✅ Concluída | Autoalteração, reset OWNER e primeiro acesso obrigatório |
| **US-DEV-07 — Proteger acesso ao sistema** | EM ANDAMENTO | ✅ Concluída | lock de login, política de senha, auditoria e sessão |
| **US-DEV-09 — Etapas de produção pelos cozinheiros** | EM ANDAMENTO | ✅ Concluída | fases, escala, início/fim, tempos, responsável e execução |
| **US-AN-01 — Gerenciar permissões dos usuários** | BACKLOG | ✅ Atendida pelo sistema | OWNER / ADMIN / USER com regras de rota |
| **US-AN-02 — Consultar estoque e produção** | BACKLOG | ✅ Atendida pelo sistema | telas de estoque, movimentos, produção e detalhes |
| **TEST-AN-01 — Cenários de teste e validação de negócio** | BACKLOG | ✅ Atendida tecnicamente | E2E de produção, transferências e regras de estoque |

## 🟡 Cards majoritariamente atendidas, mas que eu NÃO moveria para concluído ainda

### US-DEV-05 — Gerenciar localizações de estoque

Já existe:

- cadastro;
- edição;
- hierarquia;
- exclusão segura;
- proteção contra exclusão em uso;
- transferência entre localizações.

Porém a descrição do Trello pede **desativar localizações**, enquanto o modelo atual não possui um `ativo`/soft-delete específico para localização.

**Pendente:** implementar desativação lógica caso esse critério continue obrigatório.

### TEST-DEV-02 — Ampliar testes de integração e funcionalidades

Já cobrimos fortemente:

- perfis;
- autenticação;
- estoque;
- produção;
- FEFO;
- perdas;
- E2E HTTP;
- migrations.

Ainda seria desejável executar uma automação de navegador real e o cenário completo contra PostgreSQL.

### TESTE-DEV-01 — Integração frontend, API e banco

Frontend e API estão integrados, e o TypeScript foi validado.

Ainda falta a aceitação final com:

```text
browser real + API + PostgreSQL real
```

### T-DEV-15 — Segurança do ambiente de produção

Já concluído no código:

- `SECRET_KEY` validada;
- cookies seguros configuráveis;
- HSTS em produção;
- secrets não devem ficar no código;
- hardening da aplicação.

Ainda faltam critérios de infraestrutura:

- HTTPS real;
- domínio;
- backup automático;
- procedimento operacional de rotação de secrets.

### T-DEV-16 — Validar PostgreSQL

O código e Docker estão preparados.

Ainda faltam os testes pedidos pela card:

- migração real SQLite → PostgreSQL;
- backup/restore real;
- concorrência real;
- reinicialização da VM e persistência.

## ⏳ Cards que continuam pendentes

| Quest | Motivo |
|---|---|
| **T-DEV-02 — Alerta de estoque baixo** | estoque mínimo/alerta ainda não implementado |
| **T-DEV-07 — Inventário e contagem** | existe inventário de saldo, mas não fluxo de contagem física + conciliação |
| **US-DEV-08 — Alertas operacionais** | alertas de mínimo, validade e insuficiência planejada ainda não compõem uma central de alertas |
| **DEP-DEV-01 / DEP-DEV-02** | deploy real/VM ainda precisa ser realizado e validado |
| **T-DEV-16** | PostgreSQL real ainda precisa da validação operacional descrita acima |

---

# ▶️ Como executar — Windows + SQLite

Este é o caminho recomendado para desenvolvimento local.

## 1. Pré-requisitos

Instale:

- **Python 3.12 ou superior**;
- **Node.js 22 ou superior**;
- npm;
- opcionalmente Docker Desktop para PostgreSQL.

### Conferir Python

No PowerShell:

```powershell
py --list
```

Exemplo:

```text
-V:3.13
```

Não é obrigatório usar exatamente Python 3.12. O projeto exige **3.12+**.

Confirme:

```powershell
python --version
```

ou:

```powershell
py -3.13 --version
```

### Conferir Node

```powershell
node --version
npm --version
```

---

## 2. Extraia o projeto

Entre na pasta que contém:

```text
app/
frontend/
migrations/
tests/
run.bat
requirements.txt
```

Exemplo:

```powershell
cd C:\Users\SEU_USUARIO\Desktop\GAP
```

---

## 3. Crie o `.env`

O `.env` **não deve ser versionado nem incluído em ZIP público**.

Você pode começar copiando:

```powershell
Copy-Item .env.example .env
```

Para desenvolvimento local com SQLite, use algo semelhante:

```dotenv
APP_ENV=development

DB_CONNECTION=sqlite
DATABASE_PATH=data/app.db
DATABASE_URL=

DB_HOST=postgres
DB_PORT=5432
DB_DATABASE=ft_machry
DB_USERNAME=machry
DB_PASSWORD=troque-esta-senha

FLASK_DEBUG=0
FRONTEND_PORT=8080

SECRET_KEY=COLOQUE-UMA-CHAVE-LONGA-E-ALEATORIA-AQUI
SESSION_COOKIE_NAME=cozinha_mais_session
SESSION_COOKIE_HTTPONLY=1
SESSION_COOKIE_SAMESITE=Lax
SESSION_COOKIE_SECURE=0
SESSION_LIFETIME_MINUTES=480

LOGIN_MAX_FAILURES=5
LOGIN_LOCK_MINUTES=15

OWNER_USERNAME=dona
OWNER_INITIAL_PASSWORD=TroqueOwner@123

MANAGER_USERNAME=gestor
MANAGER_INITIAL_PASSWORD=TroqueGestor@123

COOK_USERNAME=cozinha
COOK_INITIAL_PASSWORD=TroqueCozinha@123
```

> Use senhas suas. Os valores acima são apenas exemplos de formato.

---

## 4. Primeira execução

No PowerShell, arquivos da pasta atual precisam de `./` ou `.\`.

Portanto:

```powershell
.\run.bat --seed
```

Não use apenas:

```text
run.bat --seed
```

pois o PowerShell não executa arquivos do diretório atual implicitamente.

### O que o script faz

```text
1. cria .venv se necessário
2. instala requirements.txt
3. força SQLite para execução local
4. aplica migrations
5. executa init-db
6. carrega seeds quando --seed é informado e o catálogo está vazio
7. instala frontend se necessário
8. inicia Flask
9. inicia Vite
```

### Primeira execução

Use:

```powershell
.\run.bat --seed
```

### Execuções seguintes

```powershell
.\run.bat
```

---

## 5. Acesse a aplicação

### Backend

Health:

```text
http://localhost:5000/health
```

Swagger:

```text
http://localhost:5000/docs
```

OpenAPI:

```text
http://localhost:5000/openapi.yaml
```

### Por que `http://localhost:5000/` retorna 404?

Porque a API não possui uma rota `/`.

Isso é esperado.

```text
/health → existe
/docs   → existe
/api/*  → existe
/       → não existe → 404
```

### Frontend

O fluxo atual foi desenhado para:

```text
http://localhost:8080
```

#### ⚠️ Nota sobre Vite

O repositório atual ainda contém:

```text
frontend/vite.config.js
frontend/vite.config.ts
```

O `.ts` configura porta `8080`; o `.js` legado configura `5173`.

Se o terminal do Vite informar `5173`, use:

```text
http://localhost:5173
```

A configuração que representa o fluxo atual é `vite.config.ts`. Em uma limpeza futura do repositório, o arquivo legado deve ser removido para eliminar essa ambiguidade.

---

# 🧪 Como executar os testes

## 1. Instale dependências de desenvolvimento

Se o `.venv` ainda não existe:

```powershell
py -3.13 -m venv .venv
```

Troque `3.13` pela versão 3.12+ que aparecer em:

```powershell
py --list
```

Depois:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

## 2. Rode tudo

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Os testes usam bancos SQLite temporários e **não devem alterar `data/app.db`**.

## 3. Somente E2E

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_e2e_fluxo_completo.py
```

Resultado esperado desse arquivo:

```text
1 passed
```

Isso é correto: ele contém um cenário E2E grande.

## 4. Somente migrations

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_migrations.py
```

## 5. Somente estoque

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_estoque.py
```

## 6. Frontend

```powershell
cd frontend
npm install
npx tsc --noEmit
npm run build
```

---

# 🐳 Como executar com Docker + PostgreSQL

Esta é a validação recomendada antes do deploy.

## 1. Configure `.env`

```dotenv
APP_ENV=development

DB_CONNECTION=postgresql
DB_HOST=postgres
DB_PORT=5432
DB_DATABASE=ft_machry
DB_USERNAME=machry
DB_PASSWORD=UMA-SENHA-FORTE

POSTGRES_PORT=5432
API_PORT=5000
FRONTEND_PORT=8080

SECRET_KEY=UMA-CHAVE-LONGA-E-ALEATORIA
SESSION_COOKIE_SECURE=0

OWNER_USERNAME=dona
OWNER_INITIAL_PASSWORD=TroqueOwner@123
MANAGER_USERNAME=gestor
MANAGER_INITIAL_PASSWORD=TroqueGestor@123
COOK_USERNAME=cozinha
COOK_INITIAL_PASSWORD=TroqueCozinha@123
```

## 2. Suba somente o PostgreSQL primeiro

```powershell
docker compose --profile postgres up -d postgres
```

Confira:

```powershell
docker compose --profile postgres ps
```

Espere o PostgreSQL aparecer como saudável.

## 3. Aplique migrations

```powershell
docker compose --profile postgres run --rm api flask --app app db upgrade
```

## 4. Inicialize banco + seeds

```powershell
docker compose --profile postgres run --rm api flask --app app init-db --seed
```

## 5. Suba a aplicação

```powershell
docker compose --profile postgres up -d
```

## 6. Confira

```powershell
docker compose --profile postgres ps
```

Logs:

```powershell
docker compose --profile postgres logs -f api frontend postgres
```

Acessos:

```text
Frontend: http://localhost:8080
API:      http://localhost:5000
Swagger:  http://localhost:5000/docs
Postgres: localhost:5432
```

---

# 🗃️ Migrations

## Banco novo

```powershell
.\.venv\Scripts\python.exe -m flask --app app db upgrade
.\.venv\Scripts\python.exe -m flask --app app init-db --seed
```

## Ver revision atual

```powershell
.\.venv\Scripts\python.exe -m flask --app app db current
```

## Histórico

```powershell
.\.venv\Scripts\python.exe -m flask --app app db history
```

## Criar migration depois de alterar models

```powershell
.\.venv\Scripts\python.exe -m flask --app app db migrate -m "descricao da alteracao"
```

Depois revise manualmente o arquivo gerado.

Então:

```powershell
.\.venv\Scripts\python.exe -m flask --app app db upgrade
```

> Nunca confie cegamente no autogenerate para views, dados especiais ou alterações destrutivas.

---

# 👤 Usuários, seed e primeiro acesso

O bootstrap provisiona três perfis:

| Perfil | Variável de username | Variável da senha |
|---|---|---|
| OWNER / Proprietária | `OWNER_USERNAME` | `OWNER_INITIAL_PASSWORD` |
| ADMIN / Gestor | `MANAGER_USERNAME` | `MANAGER_INITIAL_PASSWORD` |
| USER / Cozinha | `COOK_USERNAME` | `COOK_INITIAL_PASSWORD` |

Em runtime normal, contas bootstrap novas entram com troca de senha obrigatória.

## Muito importante: alterar `.env` não redefine senha existente

Se o usuário já existe no banco com `senha_hash`, rodar novamente:

```powershell
.\run.bat --seed
```

não substitui automaticamente a senha existente.

Portanto:

```text
alterar COOK_INITIAL_PASSWORD no .env
≠
alterar senha de um usuário já salvo
```

Para aplicar novas credenciais bootstrap em um banco descartável, resete o banco.

Em um banco com dados importantes, use o fluxo de redefinição pelo OWNER.

---

# ♻️ Como resetar o banco

## SQLite

⚠️ Isso apaga todos os dados locais.

Pare a aplicação e execute:

```powershell
Remove-Item .\data\app.db -ErrorAction SilentlyContinue
```

Depois:

```powershell
.\run.bat --seed
```

## Sessão antiga após reset

A sessão Flask fica no cookie do navegador.

É possível acontecer:

```text
banco antigo → usuário id 1
cookie antigo → usuario_id 1
banco novo → proprietária id 1
```

Então, após apagar o banco, o navegador pode parecer entrar automaticamente como Proprietária.

Isso não significa que o banco “lembrou” da sessão.

Limpe os dados de `localhost` no navegador ou abra uma janela anônima.

No Chrome:

```text
F12
→ Application
→ Storage
→ Clear site data
```

## PostgreSQL Docker

⚠️ Isso remove o volume inteiro do banco PostgreSQL do projeto.

```powershell
docker compose --profile postgres down -v
```

Depois repita o fluxo de inicialização.

---

# 🌐 URLs e endpoints úteis

## Infra

```text
GET /health
GET /docs
GET /openapi.yaml
```

## Auth

```text
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
POST /api/auth/change-password
GET  /api/auth/responsaveis
GET  /api/auth/auditoria
```

## Produtos

```text
GET/POST /api/produtos
GET/PUT/DELETE /api/produtos/{id}
```

## Fichas

```text
GET/POST /api/fichas-tecnicas
GET/PUT/DELETE /api/fichas-tecnicas/{id}
GET /api/fichas-tecnicas/fases
```

## Estoque

```text
GET /api/estoque/inventario
GET/POST /api/estoque/lotes
GET/POST /api/estoque/localizacoes
GET/POST /api/estoque/movimentacoes
GET/POST /api/estoque/transformacoes
```

## Produção

```text
GET/POST /api/producao/solicitacoes
GET      /api/producao/solicitacoes/{id}
PUT      /api/producao/solicitacoes/{id}/status
PUT      /api/producao/solicitacoes/{id}/execucao
```

---

# 🩺 Troubleshooting

## `run.bat` não é reconhecido

No PowerShell use:

```powershell
.\run.bat --seed
```

O prefixo `.\` significa “arquivo localizado no diretório atual”.

---

## `No suitable Python runtime found`

Veja versões instaladas:

```powershell
py --list
```

Depois crie o venv com uma versão existente, desde que seja 3.12+:

```powershell
py -3.13 -m venv .venv
```

---

## `localhost:5000` retorna 404

Normal.

Teste:

```text
http://localhost:5000/health
```

Se retornar `OK`, a API está funcionando.

---

## Frontend não abre em 8080

Veja a URL exibida pelo terminal do Vite.

Devido ao arquivo de configuração legado, ela pode aparecer como:

```text
http://localhost:5173
```

---

## Senha bootstrap não funciona

Confira se `.env` existe:

```powershell
Get-ChildItem -Force .env
```

Confira variáveis:

```powershell
Get-Content .env | Select-String "OWNER_|MANAGER_|COOK_"
```

Lembre-se:

> Se o usuário já foi criado, mudar `.env` não substitui o hash existente.

---

## Sistema entra automaticamente como Proprietária depois de resetar o banco

Limpe cookies/site data de `localhost`.

O cookie de sessão sobrevive à exclusão do SQLite.

---

## Exclusão de localização retorna conflito

Isso é esperado quando a localização:

- contém sub-localizações; ou
- possui lotes.

Resolva as dependências antes da exclusão.

---

## “Local de destino” da transferência

Agora a transferência não exige lote destino.

Escolha diretamente uma localização compatível.

O backend cria/reutiliza o lote automaticamente.

---

## Transformação não mostra produtos

Uma transformação precisa estar cadastrada.

Na própria tela de estoque abra:

```text
Configurar transformações permitidas
```

Cadastre:

```text
Produto origem → Produto resultante
```

Atualmente as unidades precisam ser iguais.

---

# 📈 Testes e evolução da cobertura

A suíte foi crescendo junto com o sistema.

```text
23  → baseline original
29  → contratos estabilizados
30  → smoke de migrations
37  → domínio consolidado
45  → planejamento
53  → execução real
58  → produção ↔ estoque
63  → produto final + perdas
68  → frontend/contratos
73  → hardening
74  → cenário E2E + migrations da Fase 9
75  → hotfix de localização / regressão esperada
77  → transferência automática por localização
82  → testes atualmente definidos após transformação inteligente
```

### Observação importante sobre o estado mais recente

Na etapa de transferência, os testes foram validados por módulos com **77/77 passando**.

A transformação inteligente adicionou novos testes e deixou **82 testes definidos**. No ambiente usado para gerar esse último hotfix não havia todas as dependências Flask disponíveis para executar a suíte completa novamente.

Portanto, no clone/local atual, a confirmação final deve ser:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

O objetivo esperado é:

```text
82 passed
```

Se houver falha, não esconda o resultado: registre o log e trate como regressão antes do deploy.

---

# 🚧 O que ainda falta

Mesmo depois desta integração grande, o projeto ainda possui trabalho importante antes de ser chamado de produção final.

## 1. PostgreSQL real

Executar e documentar:

- migração SQLite → PostgreSQL;
- backup;
- restore;
- concorrência;
- persistência após restart.

## 2. Deploy

- VM;
- domínio;
- HTTPS/TLS;
- secrets reais;
- CI/CD final;
- rollback de deploy.

## 3. Backup automatizado

Criar política real de:

```text
backup
→ retenção
→ restore testado
```

## 4. Alertas operacionais

- estoque mínimo;
- validade próxima;
- lote vencido;
- ingrediente insuficiente para planejamento.

## 5. Inventário físico

Criar sessão de contagem:

```text
saldo sistema
vs
quantidade encontrada
→ diferença
→ ajuste auditável
```

## 6. Soft-delete/desativação de localização

Hoje a localização possui exclusão protegida.

Se o requisito do Trello for mantido literalmente, deve existir um campo de ativação/desativação para preservar localizações históricas sem removê-las.

## 7. Limpeza da configuração Vite

Remover o `vite.config.js` legado e manter uma única configuração oficial para evitar divergência `5173 × 8080`.

## 8. Teste de aceitação em navegador

Além dos testes HTTP, realizar o fluxo completo por UI com PostgreSQL:

```text
login
→ produtos
→ ficha
→ estoque
→ planejamento
→ cozinha
→ execução
→ conclusão
→ movimentos
→ lote final
```

---

# 🧾 Resumo final da integração

Em aproximadamente um ciclo intensivo de integração, o projeto saiu de um conjunto de funcionalidades sobrepostas para um domínio único e transacional.

Antes, o principal risco era existir mais de uma resposta para perguntas básicas como:

```text
Qual é o produto oficial?
Quem controla o lote?
Processamento e produção são a mesma coisa?
Quem diminui o estoque?
Como uma produção vira produto acabado?
```

Agora as respostas estão claras:

```text
Produto → catálogo
Ficha Técnica → receita/planejamento técnico
Solicitação de Produção → planejamento + execução
SpComponente → necessidade congelada da produção
SpFase → fase planejada + realizada
Lote → unidade rastreável do estoque
MovimentacaoEstoque → histórico das mudanças de saldo
EstoqueService → autoridade sobre saldo/FEFO
```

A conclusão de produção virou uma operação coerente:

```text
Planejar
→ executar
→ registrar diferenças
→ consumir ingredientes
→ registrar perdas
→ gerar produto acabado
→ atualizar estoque
→ preservar auditoria
```

E os bugs encontrados no uso manual — exclusão de localização, senha de teste hardcoded, transferência dependente de lote vazio e transformação pouco intuitiva — foram tratados como parte natural da estabilização do produto, não como exceções escondidas.

---

## 🏁 Regra de ouro para continuar o projeto

Antes de adicionar uma nova feature, pergunte:

1. **Qual domínio é dono dessa regra?**
2. **A operação precisa ser transacional?**
3. **Ela altera estoque? Se sim, deixa uma movimentação?**
4. **Estou preservando histórico ou sobrescrevendo o passado?**
5. **O frontend está pedindo uma ação de negócio ou detalhes internos do banco?**
6. **Existe teste para o cenário feliz e para a falha mais perigosa?**

Se essas respostas estiverem claras, o Machry continua crescendo sem voltar a virar dois sistemas brigando pelo mesmo estoque. 🔥
