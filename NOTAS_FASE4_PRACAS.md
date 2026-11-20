# Machry — Fase 4: interface de praças e integração com produção

## Base e escopo

Implementação sobre o projeto completo entregue na Fase 3, sem alterações de backend, banco de dados ou histórico Git. A Fase 4 contempla somente a integração da interface React/TypeScript.

## Interfaces implementadas

- Nova rota `/pracas`, exibida na navegação para quem possui `pracas:ler`.
- Listagem paginada de praças com busca por nome, descrição ou nome dos cozinheiros, equipe vinculada e situação ativa/inativa.
- Modal de criação e edição: nome obrigatório, descrição opcional, situação e associação de um ou mais cozinheiros por seleção múltipla. O formulário rejeita equipe vazia e evita reenviar associações históricas quando elas não mudaram.
- Desativação com confirmação e reativação (quando permitidas); os vínculos históricos são mantidos pela API.
- Consulta de cozinheiros ativos via `GET /api/pracas/cozinheiros`, sem exigir acesso administrativo ao endpoint de usuários.
- Planejamento de produção com seleção opcional de praça ativa. A criação continua válida sem atribuição de praça.
- Fila de produção exibindo a praça de cada solicitação, inclusive vínculos históricos com praças posteriormente desativadas.
- Filtro local da fila por praça, com opções de todas as praças e sem praça. O filtro usa a coleção completa que o frontend já carrega via paginação da API.
- Modal de alteração de praça antes de iniciar a produção, incluindo remoção de atribuição, usando `PUT /api/producao/solicitacoes/{id}/praca`.
- Feedback de erro e carregamento, controles condicionados às permissões existentes e ajustes responsivos no layout.

## Regras de autorização e compatibilidade

- A navegação de Praças exige `pracas:ler`; os botões administrativos respeitam `pracas:criar`, `pracas:atualizar` e `pracas:excluir`.
- O seletor de praça no planejador e o modal de realocação só aparecem quando o usuário pode planejar e consultar praças. A realocação segue a permissão `producao:criar` exigida pelo backend e está disponível somente nos estados `ABERTA`/`EM_SEPARACAO`.
- Usuários sem `pracas:ler` continuam usando a tela de produção sem forçar nova consulta à API de praças; podem visualizar o nome da praça já retornado na solicitação.
- Sem praça é escolha válida, preservando solicitações antigas e compatibilidade com o endpoint de criação.
- Não foi implementada filtragem de produções por cozinheiro autenticado ou por praça de atuação, pois essa restrição não foi definida. O filtro de interface **não é** controle de autorização.
- A interface não cria uma entidade distinta `Cozinheiro`: usa o vínculo de `Praca` com usuários da equipe Cozinha.

## Arquivos afetados

Todos em `frontend/src`, além destas notas:

- `app/router.tsx`
- `features/acessos/utils/rotulos.ts`
- `features/pracas/api/pracasApi.ts` (novo)
- `features/pracas/components/ModalDePraca.tsx` (novo)
- `features/pracas/components/TabelaDePracas.tsx` (novo)
- `features/pracas/index.ts` (novo)
- `features/producao/api/producaoApi.ts`
- `features/producao/components/FilaDeProducao.tsx`
- `features/producao/components/ModalDeAtribuicao.tsx` (novo)
- `features/producao/components/PlanejadorDeProducao.tsx`
- `features/producao/index.ts`
- `pages/Pracas/PracasPage.tsx` (novo)
- `pages/Producao/ProducaoPage.tsx`
- `stores/dados.ts`
- `styles/global.css`
- `styles/telas/pracas.css` (novo)
- `styles/telas/producao.css`
- `types/acesso.ts`
- `types/index.ts`
- `types/praca.ts` (novo)
- `types/producao.ts`

## Validação e pendências

Validações realizadas na preparação da entrega:

1. Todos os 122 arquivos `.ts`/`.tsx` do frontend passaram pela análise sintática do compilador TypeScript global.
2. Uma checagem de tipos com declarações temporárias simplificadas para React não identificou incompatibilidades de tipos. **Isso não substitui** a validação real com `@types/react`, React, Vite e dependências instaladas.
3. A instalação das dependências npm não pôde ser concluída nesta sessão: indisponibilidade de acesso a `registry.npmjs.org` (`EAI_AGAIN`). Portanto **`npm run build` e testes em navegador não foram executados**.
4. O backend e o banco PostgreSQL não foram executados nesta fase. A validação completa e a documentação final permanecem na Fase 5.

### Conferência na máquina de desenvolvimento (PowerShell)

```powershell
cd frontend
npm ci
npx tsc --noEmit
npm run build
```

Depois, executar a aplicação com a API da Fase 3 e validar manualmente: permissões do menu, CRUD, seleção múltipla, desativação/reativação, filtro, criação e realocação da produção, produção sem praça, erros 400/403/409 e atualização após salvar.
