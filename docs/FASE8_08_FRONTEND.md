# Fase 8.8 — Frontend e contratos de produção

Esta fase conecta o frontend React aos contratos introduzidos nas fases 8.4–8.7 sem remover os endpoints existentes.

## Planejamento

A tela de produção agora permite informar:

- ficha técnica;
- quantidade planejada;
- prioridade;
- data/hora prevista;
- responsável;
- observação de planejamento.

`GET /api/auth/responsaveis` expõe somente usuários ativos para OWNER e ADMIN, sem abrir o CRUD administrativo de usuários.

## Execução

O detalhe de uma solicitação usa `GET /api/producao/solicitacoes/{id}` e apresenta planejado × realizado para componentes e fases.

Durante `EM_PRODUCAO`, a cozinha pode registrar:

- quantidade produzida;
- observação da execução;
- tempo realizado por fase;
- início/fim por fase;
- observação por fase;
- novas perdas de ingredientes.

A gravação usa `PUT /api/producao/solicitacoes/{id}/execucao`.

## Conclusão

A conclusão usa `PUT /api/producao/solicitacoes/{id}/status` com `status=CONCLUIDA` e pode enviar `localizacao_destino_id`.

Usuários de cozinha podem consultar `GET /api/estoque/localizacoes` exclusivamente para escolher o destino do produto acabado. As demais permissões administrativas de estoque continuam bloqueadas.

## Compatibilidade

Os contratos anteriores continuam registrados. O frontend antigo de criação simples também permanece compatível com o backend porque os novos campos de planejamento são opcionais na API.
