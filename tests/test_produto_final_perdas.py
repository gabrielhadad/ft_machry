"""Produto acabado e perdas auditáveis — Fase 8.7."""
from datetime import date, timedelta


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


def _abastecer(client):
    _criar_lote_com_saldo(client, 8, 2, 400, "2099-05-01")
    _criar_lote_com_saldo(client, 3, 2, 100, "2098-01-01")
    _criar_lote_com_saldo(client, 3, 2, 270, "2099-01-01")
    _criar_lote_com_saldo(client, 7, 2, 500, "2099-05-01")
    _criar_lote_com_saldo(client, 9, 2, 50, "2099-05-01")
    _criar_lote_com_saldo(client, 4, 1, 100)


def _criar_e_iniciar(client):
    criada = client.post("/api/producao/solicitacoes", json={"ficha_tecnica_id": 1})
    assert criada.status_code == 201, criada.get_json()
    sp_id = criada.get_json()["id"]
    inicio = client.put(
        f"/api/producao/solicitacoes/{sp_id}/status",
        json={"status": "EM_PRODUCAO"},
    )
    assert inicio.status_code == 200, inicio.get_json()
    return sp_id


def test_conclusao_cria_lote_e_movimento_de_produto_final(seeded_client):
    c = seeded_client
    _abastecer(c)
    sp_id = _criar_e_iniciar(c)

    execucao = c.put(
        f"/api/producao/solicitacoes/{sp_id}/execucao",
        json={"quantidade_produzida": 0.95},
    )
    assert execucao.status_code == 200, execucao.get_json()

    concluida = c.put(
        f"/api/producao/solicitacoes/{sp_id}/status",
        json={"status": "CONCLUIDA", "localizacao_destino_id": 2},
    )
    assert concluida.status_code == 200, concluida.get_json()
    assert concluida.get_json()["quantidade_produzida"] == 0.95
    assert concluida.get_json()["perda_rendimento"] == 0.05

    detalhe = c.get(f"/api/producao/solicitacoes/{sp_id}").get_json()
    assert len(detalhe["lotes_produzidos"]) == 1
    produzido = detalhe["lotes_produzidos"][0]
    assert produzido["quantidade"] == 0.95

    lote = c.get(f"/api/estoque/lotes/{produzido['lote_id']}").get_json()
    assert lote["produto_id"] == 10
    assert lote["localizacao_id"] == 2
    assert lote["quantidade"] == 0.95
    assert lote["data_producao"] == date.today().isoformat()
    assert lote["data_validade"] == (date.today() + timedelta(days=4)).isoformat()

    movimentos = c.get("/api/estoque/movimentacoes?tipo=PRODUCAO").get_json()
    assert len(movimentos) == 1
    assert movimentos[0]["solicitacao_producao_id"] == sp_id
    assert movimentos[0]["lote_id"] == produzido["lote_id"]


def test_conclusao_legada_assume_planejado_e_localizacao_compativel(seeded_client):
    c = seeded_client
    _abastecer(c)
    sp_id = _criar_e_iniciar(c)

    resposta = c.put(
        f"/api/producao/solicitacoes/{sp_id}/status",
        json={"status": "CONCLUIDA"},
    )
    assert resposta.status_code == 200, resposta.get_json()
    corpo = resposta.get_json()
    assert corpo["quantidade_produzida"] == 1.0
    assert corpo["perda_rendimento"] == 0.0

    detalhe = c.get(f"/api/producao/solicitacoes/{sp_id}").get_json()
    lote_id = detalhe["lotes_produzidos"][0]["lote_id"]
    lote = c.get(f"/api/estoque/lotes/{lote_id}").get_json()
    # Primeiro local RESFRIADO do catálogo seed.
    assert lote["localizacao_id"] == 2


def test_destino_incompativel_faz_rollback_de_consumo_e_produto_final(seeded_client):
    c = seeded_client
    _abastecer(c)
    sp_id = _criar_e_iniciar(c)

    resposta = c.put(
        f"/api/producao/solicitacoes/{sp_id}/status",
        # Bolo é RESFRIADO; Estoque Seco é SECO.
        json={"status": "CONCLUIDA", "localizacao_destino_id": 1},
    )
    assert resposta.status_code == 400, resposta.get_json()

    detalhe = c.get(f"/api/producao/solicitacoes/{sp_id}").get_json()
    assert detalhe["solicitacao"]["status"] == "EM_PRODUCAO"
    assert detalhe["lotes_produzidos"] == []
    assert c.get("/api/estoque/movimentacoes?tipo=CONSUMO_PRODUCAO").get_json() == []
    assert c.get("/api/estoque/movimentacoes?tipo=PRODUCAO").get_json() == []


def test_quantidade_zero_registra_perda_total_sem_criar_lote_final(seeded_client):
    c = seeded_client
    _abastecer(c)
    sp_id = _criar_e_iniciar(c)
    execucao = c.put(
        f"/api/producao/solicitacoes/{sp_id}/execucao",
        json={"quantidade_produzida": 0},
    )
    assert execucao.status_code == 200, execucao.get_json()

    resposta = c.put(
        f"/api/producao/solicitacoes/{sp_id}/status",
        json={"status": "CONCLUIDA"},
    )
    assert resposta.status_code == 200, resposta.get_json()
    assert resposta.get_json()["perda_rendimento"] == 1.0
    detalhe = c.get(f"/api/producao/solicitacoes/{sp_id}").get_json()
    assert detalhe["lotes_produzidos"] == []


def test_perda_de_insumo_e_movimentacao_auditavel_e_compoe_realizado(seeded_client):
    c = seeded_client
    _abastecer(c)
    sp_id = _criar_e_iniciar(c)
    detalhe = c.get(f"/api/producao/solicitacoes/{sp_id}").get_json()
    leite = next(item for item in detalhe["componentes"] if item["produto_id"] == 3)

    perda = c.put(
        f"/api/producao/solicitacoes/{sp_id}/execucao",
        json={
            "perdas": [
                {
                    "sp_componente_id": leite["sp_componente_id"],
                    "quantidade": 20,
                    "motivo": "Derramamento durante a mistura",
                }
            ]
        },
    )
    assert perda.status_code == 200, perda.get_json()
    leite_apos_perda = next(
        item for item in perda.get_json()["componentes"] if item["produto_id"] == 3
    )
    assert leite_apos_perda["quantidade_realizada"] == 20

    movimentos_perda = c.get("/api/estoque/movimentacoes?tipo=PERDA").get_json()
    assert len(movimentos_perda) == 1
    assert movimentos_perda[0]["quantidade"] == 20
    assert movimentos_perda[0]["motivo"] == "Derramamento durante a mistura"
    assert movimentos_perda[0]["sp_componente_id"] == leite["sp_componente_id"]
    assert movimentos_perda[0]["solicitacao_producao_id"] == sp_id

    concluida = c.put(
        f"/api/producao/solicitacoes/{sp_id}/status",
        json={"status": "CONCLUIDA"},
    )
    assert concluida.status_code == 200, concluida.get_json()
    detalhe_final = c.get(f"/api/producao/solicitacoes/{sp_id}").get_json()
    leite_final = next(
        item for item in detalhe_final["componentes"] if item["produto_id"] == 3
    )
    assert leite_final["quantidade_prevista"] == 300
    assert leite_final["quantidade_realizada"] == 320
