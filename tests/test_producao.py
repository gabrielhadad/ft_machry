"""Testes dos endpoints públicos de produção.

A Fase 8 usa estes testes como contrato de regressão: a criação de uma
solicitação deve acontecer pela própria API, sem montar a produção diretamente
no banco. Isso garante que routes -> service -> repository sejam exercitados.
"""


def _criar_solicitacao(client, ficha_id=1):
    resposta = client.post(
        "/api/producao/solicitacoes",
        json={"ficha_tecnica_id": ficha_id},
    )
    assert resposta.status_code == 201, resposta.get_json()
    return resposta.get_json()


def test_lista_vazia(client):
    r = client.get("/api/producao/solicitacoes")
    assert r.status_code == 200 and r.get_json() == []


def test_criar_solicitacao_por_endpoint(seeded_client):
    criada = _criar_solicitacao(seeded_client)
    assert criada["ficha_tecnica_id"] == 1
    assert criada["usuario_id"] == 1
    assert criada["status"] == "ABERTA"


def test_criar_solicitacao_com_ficha_inexistente(client):
    resposta = client.post(
        "/api/producao/solicitacoes",
        json={"ficha_tecnica_id": 9999},
    )
    assert resposta.status_code == 404


def test_detalhe_inexistente(client):
    assert client.get("/api/producao/solicitacoes/999").status_code == 404


def test_lista_e_detalhe_com_dados(seeded_client):
    c = seeded_client
    criada = _criar_solicitacao(c)
    solicitacao_id = criada["id"]

    # Exercita também a máquina de estados pública da produção.
    atualizada = c.put(
        f"/api/producao/solicitacoes/{solicitacao_id}/status",
        json={"status": "EM_PRODUCAO"},
    )
    assert atualizada.status_code == 200, atualizada.get_json()
    assert atualizada.get_json()["status"] == "EM_PRODUCAO"

    lista = c.get("/api/producao/solicitacoes")
    assert lista.status_code == 200
    assert [s["id"] for s in lista.get_json()] == [solicitacao_id]
    assert lista.get_json()[0]["status"] == "EM_PRODUCAO"

    detalhe = c.get(f"/api/producao/solicitacoes/{solicitacao_id}")
    assert detalhe.status_code == 200
    corpo = detalhe.get_json()
    assert corpo["solicitacao"]["id"] == solicitacao_id
    assert corpo["solicitacao"]["status"] == "EM_PRODUCAO"

    assert len(corpo["fases"]) >= 1
    assert corpo["fases"][0]["tempo_previsto_min"] > 0

    assert len(corpo["componentes"]) >= 1
    assert corpo["componentes"][0]["quantidade_prevista"] > 0
    assert corpo["componentes"][0]["quantidade_realizada"] == 0

    assert corpo["lotes_produzidos"] == []


def test_transicao_de_status_invalida(seeded_client):
    c = seeded_client
    criada = _criar_solicitacao(c)

    # Não é permitido concluir uma produção que ainda está ABERTA.
    resposta = c.put(
        f"/api/producao/solicitacoes/{criada['id']}/status",
        json={"status": "CONCLUIDA"},
    )
    assert resposta.status_code == 400


def test_criacao_legada_usa_rendimento_da_ficha(seeded_client):
    """O payload antigo deve continuar funcionando sem quantidade explícita."""
    criada = _criar_solicitacao(seeded_client)
    assert criada["quantidade_planejada"] == 1.0
    assert criada["prioridade"] == "NORMAL"
    assert criada["previsto_para"] is None
    assert criada["responsavel_id"] is None

    detalhe = seeded_client.get(
        f"/api/producao/solicitacoes/{criada['id']}"
    ).get_json()
    quantidades = {
        item["produto_id"]: item["quantidade_prevista"]
        for item in detalhe["componentes"]
    }
    assert quantidades == {8: 400.0, 3: 300.0, 7: 500.0, 9: 50.0, 4: 100.0}


def test_planejamento_escala_componentes_pelo_rendimento(seeded_client):
    resposta = seeded_client.post(
        "/api/producao/solicitacoes",
        json={
            "ficha_tecnica_id": 1,
            "quantidade_planejada": 2,
            "prioridade": "ALTA",
            "previsto_para": "2026-11-03T08:30:00",
            "responsavel_id": 3,
            "observacao": "  Priorizar para a abertura.  ",
        },
    )
    assert resposta.status_code == 201, resposta.get_json()
    criada = resposta.get_json()
    assert criada["quantidade_planejada"] == 2.0
    assert criada["prioridade"] == "ALTA"
    assert criada["previsto_para"] == "2026-11-03T08:30:00"
    assert criada["responsavel_id"] == 3
    assert criada["observacao"] == "Priorizar para a abertura."

    detalhe = seeded_client.get(
        f"/api/producao/solicitacoes/{criada['id']}"
    ).get_json()
    quantidades = {
        item["produto_id"]: item["quantidade_prevista"]
        for item in detalhe["componentes"]
    }
    assert quantidades == {8: 800.0, 3: 600.0, 7: 1000.0, 9: 100.0, 4: 200.0}


def test_planejamento_rejeita_quantidade_invalida(seeded_client):
    resposta = seeded_client.post(
        "/api/producao/solicitacoes",
        json={"ficha_tecnica_id": 1, "quantidade_planejada": 0},
    )
    assert resposta.status_code == 400


def test_planejamento_rejeita_prioridade_invalida(seeded_client):
    resposta = seeded_client.post(
        "/api/producao/solicitacoes",
        json={"ficha_tecnica_id": 1, "prioridade": "SUPER_IMPORTANTE"},
    )
    assert resposta.status_code == 400


def test_planejamento_rejeita_data_invalida(seeded_client):
    resposta = seeded_client.post(
        "/api/producao/solicitacoes",
        json={"ficha_tecnica_id": 1, "previsto_para": "amanhã cedo"},
    )
    assert resposta.status_code == 400


def test_planejamento_rejeita_responsavel_inexistente(seeded_client):
    resposta = seeded_client.post(
        "/api/producao/solicitacoes",
        json={"ficha_tecnica_id": 1, "responsavel_id": 9999},
    )
    assert resposta.status_code == 404


def test_iniciar_producao_registra_inicio(seeded_client):
    criada = _criar_solicitacao(seeded_client)
    assert criada["iniciado_em"] is None

    resposta = seeded_client.put(
        f"/api/producao/solicitacoes/{criada['id']}/status",
        json={"status": "EM_PRODUCAO"},
    )
    assert resposta.status_code == 200, resposta.get_json()
    assert resposta.get_json()["iniciado_em"] is not None


def test_execucao_registra_quantidade_tempo_observacoes_e_datas(seeded_client):
    criada = _criar_solicitacao(seeded_client)
    solicitacao_id = criada["id"]

    inicio = seeded_client.put(
        f"/api/producao/solicitacoes/{solicitacao_id}/status",
        json={"status": "EM_PRODUCAO"},
    )
    assert inicio.status_code == 200

    detalhe_inicial = seeded_client.get(
        f"/api/producao/solicitacoes/{solicitacao_id}"
    ).get_json()
    fase = detalhe_inicial["fases"][0]

    resposta = seeded_client.put(
        f"/api/producao/solicitacoes/{solicitacao_id}/execucao",
        json={
            "quantidade_produzida": 0.95,
            "observacao_execucao": "  Rendimento ligeiramente abaixo do previsto.  ",
            "fases": [
                {
                    "sp_fase_id": fase["sp_fase_id"],
                    "tempo_realizado_min": 12,
                    "observacao": "  Mistura homogênea.  ",
                    "iniciado_em": "2026-11-01T08:00:00",
                    "finalizado_em": "2026-11-01T08:12:00",
                }
            ],
        },
    )
    assert resposta.status_code == 200, resposta.get_json()
    corpo = resposta.get_json()
    assert corpo["solicitacao"]["quantidade_planejada"] == 1.0
    assert corpo["solicitacao"]["quantidade_produzida"] == 0.95
    assert corpo["solicitacao"]["observacao_execucao"] == "Rendimento ligeiramente abaixo do previsto."

    fase_atualizada = next(
        item for item in corpo["fases"] if item["sp_fase_id"] == fase["sp_fase_id"]
    )
    assert fase_atualizada["tempo_previsto_min"] == fase["tempo_previsto_min"]
    assert fase_atualizada["tempo_realizado_min"] == 12
    assert fase_atualizada["observacao"] == "Mistura homogênea."
    assert fase_atualizada["iniciado_em"] == "2026-11-01T08:00:00"
    assert fase_atualizada["finalizado_em"] == "2026-11-01T08:12:00"


def test_execucao_so_pode_ser_registrada_em_producao(seeded_client):
    criada = _criar_solicitacao(seeded_client)
    resposta = seeded_client.put(
        f"/api/producao/solicitacoes/{criada['id']}/execucao",
        json={"quantidade_produzida": 1},
    )
    assert resposta.status_code == 400


def test_execucao_rejeita_fase_de_outra_solicitacao(seeded_client):
    primeira = _criar_solicitacao(seeded_client)
    segunda = _criar_solicitacao(seeded_client)

    for solicitacao in (primeira, segunda):
        resposta = seeded_client.put(
            f"/api/producao/solicitacoes/{solicitacao['id']}/status",
            json={"status": "EM_PRODUCAO"},
        )
        assert resposta.status_code == 200

    fase_segunda = seeded_client.get(
        f"/api/producao/solicitacoes/{segunda['id']}"
    ).get_json()["fases"][0]

    resposta = seeded_client.put(
        f"/api/producao/solicitacoes/{primeira['id']}/execucao",
        json={
            "fases": [
                {
                    "sp_fase_id": fase_segunda["sp_fase_id"],
                    "tempo_realizado_min": 10,
                }
            ]
        },
    )
    assert resposta.status_code == 400


def test_execucao_rejeita_fase_duplicada(seeded_client):
    criada = _criar_solicitacao(seeded_client)
    seeded_client.put(
        f"/api/producao/solicitacoes/{criada['id']}/status",
        json={"status": "EM_PRODUCAO"},
    )
    fase = seeded_client.get(
        f"/api/producao/solicitacoes/{criada['id']}"
    ).get_json()["fases"][0]

    resposta = seeded_client.put(
        f"/api/producao/solicitacoes/{criada['id']}/execucao",
        json={
            "fases": [
                {"sp_fase_id": fase["sp_fase_id"], "tempo_realizado_min": 10},
                {"sp_fase_id": fase["sp_fase_id"], "tempo_realizado_min": 11},
            ]
        },
    )
    assert resposta.status_code == 400


def test_execucao_rejeita_intervalo_de_fase_invertido(seeded_client):
    criada = _criar_solicitacao(seeded_client)
    seeded_client.put(
        f"/api/producao/solicitacoes/{criada['id']}/status",
        json={"status": "EM_PRODUCAO"},
    )
    fase = seeded_client.get(
        f"/api/producao/solicitacoes/{criada['id']}"
    ).get_json()["fases"][0]

    resposta = seeded_client.put(
        f"/api/producao/solicitacoes/{criada['id']}/execucao",
        json={
            "fases": [
                {
                    "sp_fase_id": fase["sp_fase_id"],
                    "iniciado_em": "2026-11-01T09:00:00",
                    "finalizado_em": "2026-11-01T08:00:00",
                }
            ]
        },
    )
    assert resposta.status_code == 400


def test_snapshot_da_fase_nao_muda_quando_catalogo_e_renomeado(seeded_client):
    from app.features.fichas_tecnicas.models import FaseProducao
    from db.database_config import db

    criada = _criar_solicitacao(seeded_client)
    antes = seeded_client.get(
        f"/api/producao/solicitacoes/{criada['id']}"
    ).get_json()
    nome_snapshot = antes["fases"][0]["fase"]

    with seeded_client.application.app_context():
        fase_catalogo = db.session.get(FaseProducao, antes["fases"][0]["fase_id"])
        fase_catalogo.nome = "Nome alterado depois da produção"
        db.session.commit()

    depois = seeded_client.get(
        f"/api/producao/solicitacoes/{criada['id']}"
    ).get_json()
    assert depois["fases"][0]["fase"] == nome_snapshot


def test_cozinha_pode_registrar_execucao(seeded_client):
    criada = _criar_solicitacao(seeded_client)
    seeded_client.put(
        f"/api/producao/solicitacoes/{criada['id']}/status",
        json={"status": "EM_PRODUCAO"},
    )
    seeded_client.post("/api/auth/logout")
    login = seeded_client.post(
        "/api/auth/login",
        json={
            "username": seeded_client.application.config["COOK_USERNAME"],
            "password": seeded_client.application.config["COOK_INITIAL_PASSWORD"],
        },
    )
    assert login.status_code == 200

    resposta = seeded_client.put(
        f"/api/producao/solicitacoes/{criada['id']}/execucao",
        json={"quantidade_produzida": 1},
    )
    assert resposta.status_code == 200, resposta.get_json()
