"""Integração transacional entre produção e estoque — Fase 8.6."""


def _criar_lote_com_saldo(client, produto_id, localizacao_id, quantidade, validade=None):
    payload = {"produto_id": produto_id, "localizacao_id": localizacao_id}
    if validade is not None:
        payload["data_validade"] = validade
    resposta = client.post("/api/estoque/lotes", json=payload)
    assert resposta.status_code == 201, resposta.get_json()
    lote_id = resposta.get_json()["id"]

    entrada = client.post(
        "/api/estoque/movimentacoes",
        json={
            "tipo": "ENTRADA",
            "lote_id": lote_id,
            "usuario_id": 1,
            "quantidade": quantidade,
        },
    )
    assert entrada.status_code == 201, entrada.get_json()
    return lote_id


def _abastecer_ficha_padrao(client, *, farinha_massa=400, leite=(100, 250)):
    """Cria estoque suficiente para os cinco componentes da ficha seed.

    O leite é dividido em dois lotes para provar a ordem FEFO.
    """
    lotes = {}
    lotes["massa"] = _criar_lote_com_saldo(
        client, 8, 2, farinha_massa, "2099-05-01"
    )
    lotes["leite_primeiro"] = _criar_lote_com_saldo(
        client, 3, 2, leite[0], "2098-01-01"
    )
    lotes["leite_segundo"] = _criar_lote_com_saldo(
        client, 3, 2, leite[1], "2099-01-01"
    )
    lotes["creme"] = _criar_lote_com_saldo(
        client, 7, 2, 500, "2099-05-01"
    )
    lotes["chantili"] = _criar_lote_com_saldo(
        client, 9, 2, 50, "2099-05-01"
    )
    lotes["nozes"] = _criar_lote_com_saldo(client, 4, 1, 100)
    return lotes


def _criar_e_iniciar(client):
    criada = client.post(
        "/api/producao/solicitacoes", json={"ficha_tecnica_id": 1}
    )
    assert criada.status_code == 201, criada.get_json()
    sp_id = criada.get_json()["id"]
    iniciada = client.put(
        f"/api/producao/solicitacoes/{sp_id}/status",
        json={"status": "EM_PRODUCAO"},
    )
    assert iniciada.status_code == 200, iniciada.get_json()
    return sp_id


def test_concluir_producao_consume_componentes_por_fefo(seeded_client):
    c = seeded_client
    lotes = _abastecer_ficha_padrao(c)
    sp_id = _criar_e_iniciar(c)

    resposta = c.put(
        f"/api/producao/solicitacoes/{sp_id}/status",
        json={"status": "CONCLUIDA"},
    )
    assert resposta.status_code == 200, resposta.get_json()
    assert resposta.get_json()["status"] == "CONCLUIDA"

    # O leite precisava de 300 ml: esgota o lote que vence antes e usa 200 do segundo.
    assert c.get(f"/api/estoque/lotes/{lotes['leite_primeiro']}").get_json()["quantidade"] == 0
    assert c.get(f"/api/estoque/lotes/{lotes['leite_segundo']}").get_json()["quantidade"] == 50

    detalhe = c.get(f"/api/producao/solicitacoes/{sp_id}").get_json()
    for componente in detalhe["componentes"]:
        assert componente["quantidade_realizada"] == componente["quantidade_prevista"]

    movimentos = c.get(
        "/api/estoque/movimentacoes?tipo=CONSUMO_PRODUCAO&limite=100"
    ).get_json()
    # Cinco componentes; leite ocupa dois lotes = seis movimentos.
    assert len(movimentos) == 6
    assert all(m["solicitacao_producao_id"] == sp_id for m in movimentos)
    assert all(m["sp_componente_id"] is not None for m in movimentos)
    assert all(m["usuario_id"] == 1 for m in movimentos)


def test_falta_de_estoque_faz_rollback_total(seeded_client):
    c = seeded_client
    # Primeiro componente (massa) tem saldo; leite ficará insuficiente depois dele.
    lotes = _abastecer_ficha_padrao(c, leite=(100, 100))
    sp_id = _criar_e_iniciar(c)

    resposta = c.put(
        f"/api/producao/solicitacoes/{sp_id}/status",
        json={"status": "CONCLUIDA"},
    )
    assert resposta.status_code == 409, resposta.get_json()
    assert "estoque insuficiente" in resposta.get_json()["erro"]

    # Nem a baixa do componente anterior pode sobreviver ao erro posterior.
    assert c.get(f"/api/estoque/lotes/{lotes['massa']}").get_json()["quantidade"] == 400
    assert c.get(f"/api/estoque/lotes/{lotes['leite_primeiro']}").get_json()["quantidade"] == 100
    assert c.get(f"/api/estoque/lotes/{lotes['leite_segundo']}").get_json()["quantidade"] == 100

    movimentos = c.get(
        "/api/estoque/movimentacoes?tipo=CONSUMO_PRODUCAO&limite=100"
    ).get_json()
    assert movimentos == []
    solicitacao = c.get(f"/api/producao/solicitacoes/{sp_id}").get_json()["solicitacao"]
    assert solicitacao["status"] == "EM_PRODUCAO"
    assert solicitacao["concluido_em"] is None


def test_retry_de_conclusao_nao_consume_duas_vezes(seeded_client):
    c = seeded_client
    lotes = _abastecer_ficha_padrao(c)
    sp_id = _criar_e_iniciar(c)

    primeira = c.put(
        f"/api/producao/solicitacoes/{sp_id}/status",
        json={"status": "CONCLUIDA"},
    )
    assert primeira.status_code == 200
    saldo_apos_primeira = c.get(
        f"/api/estoque/lotes/{lotes['leite_segundo']}"
    ).get_json()["quantidade"]
    qtd_movimentos = len(
        c.get("/api/estoque/movimentacoes?tipo=CONSUMO_PRODUCAO&limite=100").get_json()
    )

    segunda = c.put(
        f"/api/producao/solicitacoes/{sp_id}/status",
        json={"status": "CONCLUIDA"},
    )
    assert segunda.status_code == 400
    assert c.get(
        f"/api/estoque/lotes/{lotes['leite_segundo']}"
    ).get_json()["quantidade"] == saldo_apos_primeira
    assert len(
        c.get("/api/estoque/movimentacoes?tipo=CONSUMO_PRODUCAO&limite=100").get_json()
    ) == qtd_movimentos


def test_lote_vencido_nao_e_usado_no_consumo_automatico(seeded_client):
    c = seeded_client
    vencido = _criar_lote_com_saldo(c, 3, 2, 999, "2020-01-01")
    lotes = _abastecer_ficha_padrao(c)
    sp_id = _criar_e_iniciar(c)

    resposta = c.put(
        f"/api/producao/solicitacoes/{sp_id}/status",
        json={"status": "CONCLUIDA"},
    )
    assert resposta.status_code == 200, resposta.get_json()
    assert c.get(f"/api/estoque/lotes/{vencido}").get_json()["quantidade"] == 999
    assert c.get(f"/api/estoque/lotes/{lotes['leite_primeiro']}").get_json()["quantidade"] == 0


def test_cozinha_e_a_autora_da_baixa_quando_conclui(seeded_client):
    c = seeded_client
    _abastecer_ficha_padrao(c)
    sp_id = _criar_e_iniciar(c)

    c.post("/api/auth/logout")
    login = c.post(
        "/api/auth/login",
        json={
            "username": c.application.config["COOK_USERNAME"],
            "password": c.application.config["COOK_INITIAL_PASSWORD"],
        },
    )
    assert login.status_code == 200

    resposta = c.put(
        f"/api/producao/solicitacoes/{sp_id}/status",
        json={"status": "CONCLUIDA"},
    )
    assert resposta.status_code == 200, resposta.get_json()
    movimentos = c.get("/api/producao/solicitacoes/%d" % sp_id).get_json()["componentes"]
    assert all(item["quantidade_realizada"] == item["quantidade_prevista"] for item in movimentos)

    # USER não pode consultar /estoque; validamos autoria diretamente no banco.
    from app.features.estoque.models import MovimentacaoEstoque
    from db.database_config import db

    with c.application.app_context():
        consumos = db.session.execute(
            db.select(MovimentacaoEstoque).where(
                MovimentacaoEstoque.solicitacao_producao_id == sp_id,
                MovimentacaoEstoque.tipo == "CONSUMO_PRODUCAO",
            )
        ).scalars().all()
        assert consumos
        assert {m.usuario_id for m in consumos} == {3}
