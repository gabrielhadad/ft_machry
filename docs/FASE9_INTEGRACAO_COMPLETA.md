# Fase 9 — Teste de Integração Completa

Esta fase valida o fluxo integrado do Machry depois da consolidação realizada na Fase 8.

## Cenário E2E automatizado

O teste `tests/test_e2e_fluxo_completo.py` usa a API HTTP via Flask test client e executa o seguinte fluxo sem inserir diretamente registros de produção ou movimentações de estoque no banco:

1. OWNER autentica e cria uma nova conta de cozinha com senha temporária.
2. OWNER cria lotes e entradas de estoque para todos os componentes da ficha técnica do Bolo de Nozes.
3. São criados dois lotes de leite com validades diferentes para validar FEFO.
4. OWNER cria uma solicitação de produção, define quantidade, prioridade, horário e responsável.
5. COZINHA faz login com senha temporária e é impedida de usar o restante da API antes de trocar a senha.
6. COZINHA troca a senha e inicia a produção.
7. COZINHA registra quantidade produzida, tempos reais e uma perda de ingrediente.
8. COZINHA conclui a produção escolhendo a localização de destino.
9. O backend baixa componentes por FEFO e cria o lote do produto acabado na mesma conclusão.
10. OWNER volta a autenticar e confere inventário, histórico de movimentações e auditoria.

## Valores verificados no cenário

Para o leite:

- estoque inicial: 100 ml no lote que vence primeiro + 250 ml no lote seguinte;
- perda registrada: 10 ml no primeiro lote;
- consumo planejado da produção: 300 ml;
- consumo FEFO na conclusão: 90 ml do primeiro lote + 210 ml do segundo;
- saldo final: 40 ml no segundo lote.

Para o produto acabado:

- quantidade planejada: 1 unidade;
- quantidade produzida: 0,95 unidade;
- perda de rendimento: 0,05 unidade;
- um lote final de 0,95 unidade é criado no estoque;
- a movimentação `PRODUCAO` fica vinculada à solicitação.

## Segurança e auditoria verificadas

O cenário também confirma:

- primeiro acesso obriga troca de senha;
- `usuario_id` das movimentações automáticas é o usuário autenticado da cozinha;
- `LOGIN_SUCESSO`, `SENHA_ALTERADA` e `LOGOUT` aparecem na auditoria;
- `X-Request-ID`, `X-Content-Type-Options` e `X-Frame-Options` continuam presentes.

## Resultado neste ambiente

- suíte funcional, incluindo E2E: **71 passed**;
- testes de migrations: **3 passed**;
- total validado: **74 testes**;
- TypeScript: validação estática com `tsc` concluída;
- Python: AST válido;
- OpenAPI: YAML válido.

## Limitação do ambiente de validação

Não existe Docker nem servidor PostgreSQL disponível no ambiente em que esta fase foi executada. Portanto, o cenário E2E automatizado foi executado com SQLite, seguindo o mesmo fluxo HTTP e as mesmas regras de negócio.

O código específico de PostgreSQL, migrations e locks continua coberto pela arquitetura e pelos testes existentes, mas a execução real do E2E contra PostgreSQL deve ser repetida em uma máquina com Docker/PostgreSQL antes do deploy.

## Validação local recomendada com PostgreSQL

Copie `.env.example` para `.env`, defina senhas próprias e execute:

```bash
docker compose --profile postgres up --build
```

Depois confirme:

```bash
curl http://localhost:5000/health
```

Para a suíte automatizada de desenvolvimento:

```bash
python -m pytest -q
```

O teste E2E principal pode ser executado isoladamente com:

```bash
python -m pytest -q tests/test_e2e_fluxo_completo.py
```

> Observação: a suíte atual de pytest cria banco SQLite temporário para isolamento. A validação manual via Docker é a etapa necessária para provar o runtime PostgreSQL real.
