# Cozinha Mais — pacote completo de desenvolvimento

Esta pasta contém o projeto inteiro da branch `yuri` fornecida pelo usuário, com as alterações de frontend adicionadas. **Nenhum commit, push ou PR foi criado.**

## Executar localmente

Windows: execute `run.bat` (ou `run.bat --seed` apenas para dados demonstrativos em um banco novo). Requisitos: Python 3.12+, Node.js 22+ e npm. Aguarde as instalações e abra **http://localhost:8080**. O script abre uma janela para a API Flask (5000) e mantém o Vite na janela principal (8080). Para acesso na rede local, use `http://IP_DO_PC:8080` e libere a porta 8080 no firewall, se necessário. A API Flask fica em loopback; o proxy do Vite encaminha `/api`.

Linux/macOS: `./run.sh`. Não execute scripts de desenvolvimento diretamente na OCI de produção.

Docker/OCI: `docker-compose.yml`, `frontend/nginx.conf` e os Dockerfiles originais foram preservados. A conexão DBeaver ao PostgreSQL via `127.0.0.1:5432` só funciona no próprio host ou por túnel SSH. PostgreSQL exige o profile `postgres` e configuração do banco; a publicação da porta não significa que o serviço está rodando.

## Melhorias de frontend

- Nome Cozinha Mais em login, barra lateral, carregamento e título; monograma textual C+ provisório.
- Tela de usuários para OWNER (criar, editar, redefinir senha pelo proprietário, ativar/desativar; sem exclusão).
- Localizações: criar, editar e excluir, respeitando restrições do backend.
- Movimentações: consulta dos últimos 500 registros, com filtros de lote, produto, tipo, usuário e datas.
- Estoque: transferência entre lotes do mesmo produto, transformação entre produtos com rendimento e edição de datas/custo de lote.
- Ajustes de estoque já disponíveis no formulário de movimentação, com motivo obrigatório quando exigido pela API.
- Impressão simplificada da fila de produção.
- Correção no formulário de nova entrada: após criar lote, uma falha no movimento não cria outro lote em uma nova tentativa.
- Vite proxy para API, execução local integrada por `run.bat` e `run.sh`.

## Pendências que dependem de backend/DevOps

Geração automática de produto acabado e tratamento completo de perdas; senha própria/primeiro login; rate limit/auditoria; alerta de estoque mínimo; backup; testes de implantação; TLS e segredos de produção. **Não são anunciados como implementados.** Transformação pela API exige lote de destino preexistente. O histórico está limitado aos 500 registros mais recentes retornados pela API.

## Importante para a equipe

O nome do repositório e variáveis históricas de banco (`ft_machry`, `machry`) foram preservados para não quebrar infraestrutura. O nome exibido ao usuário é Cozinha Mais. O script local força SQLite e não altera o banco PostgreSQL do Docker.


## Evolução — Fase 8.4

O backend agora persiste planejamento de produção com quantidade, prioridade, data/horário, responsável e observação. Componentes da ficha são escalados automaticamente pelo rendimento. A interface React ainda usa o payload legado (somente ficha), que permanece compatível; a experiência visual de planejamento será expandida na fase específica de alinhamento do frontend.

## Evolução — Fase 8.5

A execução da produção agora registra quantidade efetivamente produzida, tempos reais e observações por fase sem alterar o planejamento original. As fases de cada solicitação armazenam um snapshot do nome da fase para preservar o histórico mesmo que o catálogo seja renomeado. A integração automática com o estoque foi implementada na Fase 8.6.


## Evolução — Fase 8.6

Ao concluir uma produção em andamento, o backend agora baixa automaticamente os componentes planejados do estoque usando FEFO. As movimentações são registradas como `CONSUMO_PRODUCAO`, ligadas à solicitação e ao componente, e usam o usuário autenticado como autor. Conclusão e estoque compartilham a mesma transação: falta de qualquer ingrediente causa rollback completo e mantém a produção em andamento. A geração do lote do produto acabado permanece para a próxima fase.

## Atualização — Fase 8.7

- conclusão da produção gera automaticamente o lote do produto acabado;
- entrada do produto acabado é registrada como movimentação `PRODUCAO`;
- validade é calculada usando `validade_padrao_dias` quando configurada;
- `localizacao_destino_id` pode ser informada ao concluir; temporariamente há fallback para a primeira localização compatível;
- desperdícios de componentes são registrados como `PERDA` e entram no realizado da produção;
- `perda_rendimento` informa a diferença positiva entre planejado e produzido;
- consumo, lote final, movimento de produção e status final são transacionais.

## Atualização Fase 8.8

O frontend de Produção agora cobre o fluxo planejado nas fases anteriores: planejamento completo, execução real por etapa, perdas, planejado × realizado e conclusão com destino do produto acabado. O backend ganhou apenas o contrato de leitura `/api/auth/responsaveis`; o restante reutiliza os endpoints de produção já estabilizados.

## Fase 8.9 — Hardening

Antes dos testes E2E, o sistema recebeu troca obrigatória da senha temporária, troca da própria senha pela interface, bloqueio temporário de login após falhas repetidas, auditoria persistida e validação de configuração de produção. Movimentações de estoque agora usam a identidade da sessão para autoria; `usuario_id` enviado pelo cliente é legado e ignorado.

Em produção, configure `APP_ENV=production`, PostgreSQL, `SESSION_COOKIE_SECURE=1`, uma `SECRET_KEY` aleatória com 32+ caracteres e senhas bootstrap não padronizadas. A aplicação se recusa a iniciar com configuração insegura. Consulte `docs/FASE8_09_HARDENING.md`.

## Hotfix — transformação inteligente

A transformação de estoque não exige mais um lote de destino criado manualmente. A interface permite escolher o produto resultante e a localização; o backend cria ou reaproveita um lote compatível, calcula validade/custo, registra rendimento e mantém compatibilidade com `lote_destino_id`. Veja `docs/HOTFIX_TRANSFORMACAO_INTELIGENTE.md`.

