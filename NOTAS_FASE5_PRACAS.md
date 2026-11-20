# Machry — Fase 5: testes, documentação e validação

## Base e alterações

Base: projeto completo entregue na Fase 4. Não foram alterados models, rotas,
services, repositories, frontend, infraestrutura de deploy ou histórico Git.

Esta fase acrescenta e atualiza:

- `docs/openapi.yaml`: documenta CRUD `/api/pracas`, listagem de cozinheiros,
  filtro, campos e realocação da produção, schemas e permissões.
- `docs/PRACAS.md`: documentação técnica e operacional da feature, regras,
  exemplos, migração, autorização e checklist de homologação.
- `README.md`: descrição da feature e links para os documentos.
- `requirements-dev.txt`: adiciona `PyYAML>=6.0` para validar o contrato OpenAPI.
- `tests/test_pracas_documentacao.py`: três testes para rotas/métodos,
  campos/permissões e resolução de referências internas da documentação.
- `tests/test_producao_pracas.py`: acrescenta regressão de falha da conclusão
  por falta de estoque e verifica que repetir uma conclusão bem-sucedida não
  duplica movimentações.

## Resultado das verificações nesta entrega

| Verificação | Resultado | Observação |
| --- | --- | --- |
| Sintaxe Python (`compileall`) | APROVADO | Todo o código `app/`, `db/` e `tests/` |
| Carregamento YAML | APROVADO | OpenAPI analisado com PyYAML |
| Referências internas de OpenAPI | APROVADO | Todas as referências `#/...` resolvidas |
| Rotas/métodos documentados (inspeção YAML) | APROVADO | Endpoints da feature presentes no documento |
| Sintaxe TypeScript | APROVADO | 122 arquivos `.ts`/`.tsx`, analisados com TypeScript global |
| Pytest Flask | BLOQUEADO | `ModuleNotFoundError: No module named 'flask'` no carregamento dos fixtures |
| Instalação npm offline | BLOQUEADA | `ENOTCACHED`: dependências não estão em cache |
| `tsc --noEmit` / build Vite reais | NÃO EXECUTADOS | Dependências frontend indisponíveis |
| Testes UI em navegador | NÃO EXECUTADOS | Aplicação não iniciada |
| Migração e testes em PostgreSQL | NÃO EXECUTADOS | Sem banco/serviço PostgreSQL configurado |
| Segurança de concorrência PostgreSQL | NÃO VALIDADA | Necessita transações concorrentes em ambiente apropriado |
| Deploy/OCI | NÃO EXECUTADO | Fora do escopo e não autorizado |

A execução do Pytest foi tentada especificamente para
`tests/test_pracas_documentacao.py` e `tests/test_producao_pracas.py`, mas
não houve coleta dos testes devido à falta de Flask. Portanto **não há
resultado de suíte funcional aprovada** nesta sessão.

## Procedimento de homologação antes de aprovar o PR

1. Conferir a branch e o diff. Os pacotes entregues não incluem `.git` e não
   alteram automaticamente a branch `main` ou o histórico de commits.
2. Criar/ativar o virtualenv Python 3.12+ e instalar
   `pip install -r requirements-dev.txt`.
3. Executar os testes focados e a suíte inteira:

   ```powershell
   .\.venv\Scripts\python.exe -m pytest -q tests/test_pracas_modelagem.py tests/test_pracas_api.py tests/test_producao_pracas.py tests/test_pracas_documentacao.py
   .\.venv\Scripts\python.exe -m pytest -q
   ```

4. Instalar os pacotes a partir do lockfile frontend e validar compilação:

   ```powershell
   cd frontend
   pnpm install --frozen-lockfile
   pnpm exec tsc --noEmit
   pnpm run build
   ```

5. Em cópia de banco real, após backup validado, executar `flask --app app
   init-db` e conferir migração e indexação do campo `praca_id`. Repetir em
   PostgreSQL e validar os dados legados.
6. Fazer teste manual da UI e da API conforme `docs/PRACAS.md`, incluindo
   perfis Gestor/Cozinha, desativação, reativação, realocação e falha de estoque.
7. Revisar os testes de concorrência do banco alvo (atribuição/realocação,
   início simultâneo, usuários que perdem o grupo Cozinha) e permissões de
   grupos existentes. Testes unitários com SQLite não bastam para certificar
   comportamento de bloqueio de linha no PostgreSQL.
8. Registrar resultados (comandos, logs, ambiente, commit) no PR. Se qualquer
   teste falhar, corrigir antes do merge. O workflow do projeto prevê deploy
   automático após push em `main`; não fazer merge para produção sem a aprovação
   do pipeline e da equipe.

## Status

**Fase 5: documentação e testes implementados; validação integrada pendente.**
Não declarar esta feature pronta para produção enquanto os itens bloqueados
não forem executados e avaliados em ambiente com dependências e banco reais.
