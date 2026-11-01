"""Contratos HTTP que o frontend Cozinha Mais já consome.

Enquanto a integração GAP -> Cozinha Mais estiver em andamento, estes caminhos
não devem ser renomeados/removidos sem uma migração coordenada do frontend.
"""

CRITICAL_ROUTES = {
    ("GET", "/api/auth/me"),
    ("POST", "/api/auth/login"),
    ("POST", "/api/auth/logout"),
    ("POST", "/api/auth/change-password"),
    ("GET", "/api/auth/responsaveis"),
    ("GET", "/api/auth/auditoria"),
    ("GET", "/api/produtos"),
    ("POST", "/api/produtos"),
    ("GET", "/api/fichas-tecnicas"),
    ("POST", "/api/fichas-tecnicas"),
    ("GET", "/api/fichas-tecnicas/fases"),
    ("GET", "/api/estoque/inventario"),
    ("GET", "/api/estoque/lotes"),
    ("POST", "/api/estoque/lotes"),
    ("GET", "/api/estoque/localizacoes"),
    ("GET", "/api/estoque/movimentacoes"),
    ("GET", "/api/estoque/transformacoes"),
    ("POST", "/api/estoque/transformacoes"),
    ("DELETE", "/api/estoque/transformacoes/<int:produto_origem_id>/<int:produto_destino_id>"),
    ("POST", "/api/estoque/movimentacoes"),
    ("GET", "/api/producao/solicitacoes"),
    ("POST", "/api/producao/solicitacoes"),
    ("GET", "/api/producao/solicitacoes/<int:sp_id>"),
    ("PUT", "/api/producao/solicitacoes/<int:sp_id>/status"),
    ("PUT", "/api/producao/solicitacoes/<int:sp_id>/execucao"),
}


def _normalize_rule(rule: str) -> str:
    # Regras parametrizadas continuam sendo verificadas em seus testes de CRUD;
    # aqui congelamos apenas os endpoints de coleção usados para bootstrap do SPA.
    return rule


def test_rotas_criticas_do_frontend_continuam_registradas(app):
    registradas: set[tuple[str, str]] = set()
    for rule in app.url_map.iter_rules():
        caminho = _normalize_rule(str(rule))
        for metodo in rule.methods:
            if metodo not in {"HEAD", "OPTIONS"}:
                registradas.add((metodo, caminho))

    ausentes = CRITICAL_ROUTES - registradas
    assert not ausentes, f"Contratos removidos/renomeados sem migração do frontend: {sorted(ausentes)}"


def test_health_check_publico(app):
    client = app.test_client()
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.get_json() == {"status": "ok"}


def test_api_privada_exige_autenticacao(app):
    client = app.test_client()
    resposta = client.get("/api/produtos")
    assert resposta.status_code == 401
