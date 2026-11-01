"""Fase 9: fluxo E2E do Machry pela API HTTP.

Exercita o sistema como usuários reais, sem inserir diretamente dados de produção ou
movimentações no banco: OWNER prepara catálogo/estoque e planejamento; COZINHA faz
primeiro acesso, executa, registra perda e conclui; OWNER audita o resultado.
"""

from __future__ import annotations

from collections import defaultdict


def _json(response):
    assert response.is_json, response.get_data(as_text=True)
    return response.get_json()


def _post_ok(client, url, payload, expected=201):
    response = client.post(url, json=payload)
    assert response.status_code == expected, (url, response.status_code, response.get_data(as_text=True))
    return _json(response) if response.data else None


def _put_ok(client, url, payload, expected=200):
    response = client.put(url, json=payload)
    assert response.status_code == expected, (url, response.status_code, response.get_data(as_text=True))
    return _json(response) if response.data else None


def test_fluxo_completo_owner_cozinha_fefo_perdas_produto_final_auditoria(seeded_client):
    client = seeded_client

    # 1) OWNER cria uma conta de cozinha com senha temporária.
    cozinha = _post_ok(
        client,
        "/api/auth/usuarios",
        {
            "nome": "Cozinha E2E",
            "username": "cozinha.e2e",
            "password": "Temporaria@123",
            "papel": "USER",
        },
    )
    cozinha_id = cozinha["id"]
    assert cozinha["deve_trocar_senha"] == 1

    # 2) OWNER prepara estoque real para todos os componentes da ficha #1.
    # Leite recebe dois lotes para provar FEFO + uma sobra previsível.
    lotes = {}

    def criar_lote(produto_id, localizacao_id, validade, quantidade, custo=1.0, chave=None):
        lote = _post_ok(
            client,
            "/api/estoque/lotes",
            {
                "produto_id": produto_id,
                "localizacao_id": localizacao_id,
                "data_producao": "2026-10-31",
                "data_validade": validade,
                "custo_unitario": float(custo),
            },
        )
        _post_ok(
            client,
            "/api/estoque/movimentacoes",
            {"tipo": "ENTRADA", "lote_id": lote["id"], "quantidade": float(quantidade)},
        )
        lotes[chave or produto_id] = lote["id"]
        return lote["id"]

    # Massa, creme e chantili são resfriados; nozes são secas.
    criar_lote(8, 2, "2099-12-01", 500, chave="massa")
    leite_vence_primeiro = criar_lote(3, 2, "2098-01-01", 100, chave="leite_1")
    leite_vence_depois = criar_lote(3, 2, "2099-01-01", 250, chave="leite_2")
    criar_lote(7, 2, "2099-12-01", 600, chave="creme")
    criar_lote(9, 2, "2099-12-01", 100, chave="chantili")
    criar_lote(4, 1, "2099-12-01", 150, chave="nozes")

    # 3) OWNER cria o planejamento da produção e designa a cozinha.
    solicitacao = _post_ok(
        client,
        "/api/producao/solicitacoes",
        {
            "ficha_tecnica_id": 1,
            "quantidade_planejada": 1,
            "prioridade": "ALTA",
            "previsto_para": "2026-11-01T08:00:00",
            "responsavel_id": cozinha_id,
            "observacao": "Fluxo E2E da Fase 9",
        },
    )
    sp_id = solicitacao["id"]
    assert solicitacao["status"] == "ABERTA"
    assert solicitacao["responsavel_id"] == cozinha_id

    # 4) Troca de perfil: cozinha faz primeiro login.
    assert client.post("/api/auth/logout").status_code == 204
    login = client.post(
        "/api/auth/login",
        json={"username": "cozinha.e2e", "password": "Temporaria@123"},
    )
    assert login.status_code == 200
    assert _json(login)["deve_trocar_senha"] == 1

    # Primeiro acesso bloqueia o restante da API.
    bloqueado = client.get("/api/producao/solicitacoes")
    assert bloqueado.status_code == 403
    assert "troca de senha" in _json(bloqueado)["erro"]

    troca = client.post(
        "/api/auth/change-password",
        json={"current_password": "Temporaria@123", "new_password": "CozinhaNova@456"},
    )
    assert troca.status_code == 200
    assert _json(troca)["deve_trocar_senha"] == 0

    # 5) COZINHA inicia a produção.
    iniciada = _put_ok(
        client,
        f"/api/producao/solicitacoes/{sp_id}/status",
        {"status": "EM_PRODUCAO"},
    )
    assert iniciada["status"] == "EM_PRODUCAO"
    assert iniciada["iniciado_em"] is not None

    detalhe = _json(client.get(f"/api/producao/solicitacoes/{sp_id}"))
    componentes = {item["produto_id"]: item for item in detalhe["componentes"]}
    fases = detalhe["fases"]
    assert componentes[3]["quantidade_prevista"] == 300.0  # leite
    assert len(fases) == 3

    # 6) Execução real: produz 0.95 un, registra tempos e 10 ml de perda de leite.
    execucao = _put_ok(
        client,
        f"/api/producao/solicitacoes/{sp_id}/execucao",
        {
            "quantidade_produzida": 0.95,
            "observacao_execucao": "Produção E2E concluída com pequena perda.",
            "fases": [
                {
                    "sp_fase_id": fases[0]["sp_fase_id"],
                    "tempo_realizado_min": 12,
                    "observacao": "Mistura homogênea",
                    "iniciado_em": "2026-11-01T08:00:00",
                    "finalizado_em": "2026-11-01T08:12:00",
                },
                {
                    "sp_fase_id": fases[1]["sp_fase_id"],
                    "tempo_realizado_min": 32,
                    "iniciado_em": "2026-11-01T08:12:00",
                    "finalizado_em": "2026-11-01T08:44:00",
                },
            ],
            "perdas": [
                {
                    "sp_componente_id": componentes[3]["sp_componente_id"],
                    "quantidade": 10.0,
                    "motivo": "Derramamento durante a mistura",
                }
            ],
        },
    )
    assert execucao["solicitacao"]["quantidade_produzida"] == 0.95
    assert execucao["solicitacao"]["perda_rendimento"] == 0.05

    # 7) COZINHA conclui; backend consome por FEFO e gera lote do produto final.
    concluida = _put_ok(
        client,
        f"/api/producao/solicitacoes/{sp_id}/status",
        {"status": "CONCLUIDA", "localizacao_destino_id": 2},
    )
    assert concluida["status"] == "CONCLUIDA"

    final = _json(client.get(f"/api/producao/solicitacoes/{sp_id}"))
    assert final["solicitacao"]["quantidade_produzida"] == 0.95
    assert final["solicitacao"]["perda_rendimento"] == 0.05
    assert len(final["lotes_produzidos"]) == 1
    assert final["lotes_produzidos"][0]["quantidade"] == 0.95

    # Leite realizado inclui consumo de 300 + perda de 10.
    leite_realizado = next(c for c in final["componentes"] if c["produto_id"] == 3)
    assert leite_realizado["quantidade_prevista"] == 300.0
    assert leite_realizado["quantidade_realizada"] == 310.0

    # 8) Verifica FEFO e autoria pela sessão da cozinha.
    assert client.post("/api/auth/logout").status_code == 204
    owner_login = client.post(
        "/api/auth/login", json={"username": "dona", "password": "Teste@123"}
    )
    assert owner_login.status_code == 200

    movimentos = _json(client.get("/api/estoque/movimentacoes?limite=500"))
    da_producao = [m for m in movimentos if m.get("solicitacao_producao_id") == sp_id]
    assert da_producao
    assert {m["usuario_id"] for m in da_producao} == {cozinha_id}

    por_tipo = defaultdict(list)
    for movimento in da_producao:
        por_tipo[movimento["tipo"]].append(movimento)

    assert len(por_tipo["PERDA"]) == 1
    assert por_tipo["PERDA"][0]["quantidade"] == 10.0
    assert por_tipo["PERDA"][0]["lote_id"] == leite_vence_primeiro

    consumos_leite = [
        m for m in por_tipo["CONSUMO_PRODUCAO"]
        if m.get("sp_componente_id") == componentes[3]["sp_componente_id"]
    ]
    consumo_por_lote = {m["lote_id"]: m["quantidade"] for m in consumos_leite}
    assert consumo_por_lote == {
        leite_vence_primeiro: 90.0,
        leite_vence_depois: 210.0,
    }
    assert len(por_tipo["PRODUCAO"]) == 1
    assert por_tipo["PRODUCAO"][0]["quantidade"] == 0.95

    # O estoque final de leite é exatamente a sobra do segundo lote.
    inventario_leite = _json(client.get("/api/estoque/inventario?produto_id=3"))
    assert len(inventario_leite) == 1
    assert inventario_leite[0]["lote_id"] == leite_vence_depois
    assert inventario_leite[0]["quantidade"] == 40.0

    # Produto final entrou no estoque resfriado.
    inventario_bolo = _json(client.get("/api/estoque/inventario?produto_id=10"))
    assert len(inventario_bolo) == 1
    assert inventario_bolo[0]["quantidade"] == 0.95
    assert inventario_bolo[0]["localizacao"] == "Câmara Fria"

    # 9) Auditoria registra o ciclo de autenticação/segurança.
    auditoria_response = client.get("/api/auth/auditoria?limite=500")
    assert auditoria_response.status_code == 200
    auditoria = _json(auditoria_response)
    eventos_cozinha = {
        item["evento"] for item in auditoria if item.get("usuario_id") == cozinha_id
    }
    assert "LOGIN_SUCESSO" in eventos_cozinha
    assert "SENHA_ALTERADA" in eventos_cozinha
    assert "LOGOUT" in eventos_cozinha

    # Hardening transversal: request-id e headers de segurança continuam presentes.
    health = client.get("/health", headers={"X-Request-ID": "fase9-e2e"})
    assert health.status_code == 200
    assert health.headers["X-Request-ID"] == "fase9-e2e"
    assert health.headers["X-Content-Type-Options"] == "nosniff"
    assert health.headers["X-Frame-Options"] == "DENY"
