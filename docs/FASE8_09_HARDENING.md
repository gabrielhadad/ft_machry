# Fase 8.9 — Hardening

Esta fase fecha os principais riscos de segurança e operação antes dos testes E2E.

## Autenticação

- Usuários criados ou com senha redefinida recebem `deve_trocar_senha = 1`.
- Enquanto a troca não ocorrer, somente `/api/auth/me`, `/api/auth/logout` e `/api/auth/change-password` ficam acessíveis.
- A nova senha exige maiúscula, minúscula, número e caractere especial.
- Após `LOGIN_MAX_FAILURES` falhas, a conta fica bloqueada por `LOGIN_LOCK_MINUTES`.
- Login bem-sucedido limpa contadores de falha e registra `ultimo_login_em`.

## Auditoria

A tabela `auditoria` registra eventos de login, logout, troca de senha e administração de usuários. OWNER pode consultar `GET /api/auth/auditoria`. Senhas nunca são registradas.

## Sessão e HTTP

- Cookie HttpOnly, SameSite Lax e nome dedicado `cozinha_mais_session`.
- `SESSION_COOKIE_SECURE=1` é obrigatório quando `APP_ENV=production`.
- Respostas recebem `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` e `X-Request-ID`.
- Produção adiciona HSTS.
- Logs estruturados incluem request id, método, rota, status, duração e id do usuário autenticado.

## Configuração de produção

Ao iniciar com `APP_ENV=production`, a aplicação recusa:

- SECRET_KEY curta/default;
- cookie sem Secure;
- SQLite;
- senhas bootstrap conhecidas/default.

## Estoque

`usuario_id` enviado pelo cliente em movimentações é apenas compatibilidade legada e não define autoria. O backend sempre usa `g.usuario.id`.

## Migration

Revision: `e7f8a9b0c1d2`. Adiciona campos de segurança em `usuario` e a tabela `auditoria`.
