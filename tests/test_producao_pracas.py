"""Integração de praças ao planejamento e acompanhamento da produção (Fase 3)."""

from sqlalchemy import text

from app.features.usuarios.models import Usuario
from db.database_config import db


def _cozinheiro_id(app) -> int:
    with app.app_context():
        usuario = db.session.execute(
            db.select(Usuario).where(Usuario.username == "cozinha")
        ).scalar_one()
        return usuario.id


def _criar_praca(app, client, nome="Grelha") -> int:
    resposta = client.post("/api/pracas", json={
        "nome": nome, "cozinheiros": [_cozinheiro_id(app)]
    })
    assert resposta.status_code == 201, resposta.get_json()
    return resposta.get_json()["id"]


def _criar_solicitacao(client, praca_id=None):
    payload = {"ficha_tecnica_id": 1}
    if praca_id is not None:
        payload["praca_id"] = praca_id
    resposta = client.post("/api/producao/solicitacoes", json=payload)
    assert resposta.status_code == 201, resposta.get_json()
    return resposta.get_json()


def _alterar_praca(client, sp_id, praca_id):
    return client.put(
        f"/api/producao/solicitacoes/{sp_id}/praca",
        json={"praca_id": praca_id},
    )


def _alterar_status(client, sp_id, status):
    return client.put(
        f"/api/producao/solicitacoes/{sp_id}/status", json={"status": status}
    )


def test_cliente_antigo_pode_criar_producao_sem_praca(seeded_client):
    solicitacao = _criar_solicitacao(seeded_client)
    assert solicitacao["praca_id"] is None
    assert solicitacao["praca"] is None
    assert solicitacao["status"] == "ABERTA"

    lista = seeded_client.get("/api/producao/solicitacoes").get_json()
    assert lista["total"] == 1
    assert lista["items"][0]["praca_id"] is None
    detalhe = seeded_client.get(
        f"/api/producao/solicitacoes/{solicitacao['id']}"
    ).get_json()
    assert detalhe["solicitacao"]["praca"] is None
    assert detalhe["fases"]
    assert detalhe["componentes"]


def test_criacao_listagem_detalhe_e_filtro_por_praca(app, seeded_client):
    client = seeded_client
    grelha = _criar_praca(app, client)
    saladas = _criar_praca(app, client, "Saladas")
    vinculada = _criar_solicitacao(client, grelha)
    outra = _criar_solicitacao(client, saladas)
    _criar_solicitacao(client)

    assert vinculada["praca_id"] == grelha
    assert vinculada["praca"] == {
        "id": grelha, "nome": "Grelha", "ativo": 1
    }
    assert client.get(
        f"/api/producao/solicitacoes/{vinculada['id']}"
    ).get_json()["solicitacao"]["praca"] == vinculada["praca"]

    pagina = client.get(
        f"/api/producao/solicitacoes?praca_id={grelha}&page=1&per_page=1"
    ).get_json()
    assert pagina["total"] == 1
    assert pagina["pages"] == 1
    assert [item["id"] for item in pagina["items"]] == [vinculada["id"]]
    assert client.get(
        f"/api/producao/solicitacoes?praca_id={saladas}"
    ).get_json()["items"][0]["id"] == outra["id"]
    assert client.get("/api/producao/solicitacoes").get_json()["total"] == 3
    assert client.get(
        "/api/producao/solicitacoes?praca_id=999999"
    ).get_json()["total"] == 0


def test_praca_inexistente_inativa_e_payload_invalido_na_criacao(app, seeded_client):
    client = seeded_client
    praca_id = _criar_praca(app, client)
    assert client.delete(f"/api/pracas/{praca_id}").status_code == 204
    for praca in (99999, praca_id, -1, 0, "abc"):
        resposta = client.post("/api/producao/solicitacoes", json={
            "ficha_tecnica_id": 1, "praca_id": praca
        })
        assert resposta.status_code == 400, resposta.get_json()
    assert client.get("/api/producao/solicitacoes").get_json()["total"] == 0

    # O cliente anterior, que não envia a praça, continua funcionando.
    assert client.post(
        "/api/producao/solicitacoes", json={"ficha_tecnica_id": 1}
    ).status_code == 201


def test_troca_e_desatribuicao_somente_antes_da_execucao(app, seeded_client):
    client = seeded_client
    grelha = _criar_praca(app, client)
    saladas = _criar_praca(app, client, "Saladas")
    sp_id = _criar_solicitacao(client, grelha)["id"]

    assert _alterar_praca(client, sp_id, saladas).get_json()["praca_id"] == saladas
    assert _alterar_praca(client, sp_id, None).get_json()["praca_id"] is None
    assert _alterar_status(client, sp_id, "EM_SEPARACAO").status_code == 200
    assert _alterar_praca(client, sp_id, grelha).get_json()["praca_id"] == grelha
    assert _alterar_status(client, sp_id, "EM_PRODUCAO").status_code == 200
    bloqueada = _alterar_praca(client, sp_id, saladas)
    assert bloqueada.status_code == 409, bloqueada.get_json()
    assert client.get(
        f"/api/producao/solicitacoes/{sp_id}"
    ).get_json()["solicitacao"]["praca_id"] == grelha


def test_troca_rejeita_status_final_e_praca_inativa(app, seeded_client):
    client = seeded_client
    primeira = _criar_praca(app, client)
    segunda = _criar_praca(app, client, "Saladas")
    sp_id = _criar_solicitacao(client, primeira)["id"]
    assert client.delete(f"/api/pracas/{segunda}").status_code == 204

    assert _alterar_praca(client, sp_id, segunda).status_code == 400
    assert _alterar_praca(client, sp_id, 999999).status_code == 400
    assert _alterar_praca(client, sp_id, -1).status_code == 400
    assert client.put(
        f"/api/producao/solicitacoes/{sp_id}/praca", json={}
    ).status_code == 400
    assert client.put(
        f"/api/producao/solicitacoes/{sp_id}/praca", json={"praca_id": primeira, "extra": 1}
    ).status_code == 400
    assert client.get("/api/producao/solicitacoes?praca_id=0").status_code == 400

    assert _alterar_status(client, sp_id, "CANCELADA").status_code == 200
    assert _alterar_praca(client, sp_id, None).status_code == 409
    assert _alterar_praca(client, 999999, primeira).status_code == 404
    assert client.get(
        f"/api/producao/solicitacoes/{sp_id}"
    ).get_json()["solicitacao"]["praca_id"] == primeira


def test_praca_inativa_mantem_historico_e_execucao(app, seeded_client):
    client = seeded_client
    praca_id = _criar_praca(app, client)
    sp_id = _criar_solicitacao(client, praca_id)["id"]
    assert client.delete(f"/api/pracas/{praca_id}").status_code == 204

    # Desativação não apaga o vínculo nem bloqueia a execução já planejada.
    assert _alterar_status(client, sp_id, "EM_PRODUCAO").status_code == 200
    solicitacao = client.get(
        f"/api/producao/solicitacoes/{sp_id}"
    ).get_json()["solicitacao"]
    assert solicitacao["praca_id"] == praca_id
    assert solicitacao["praca"]["ativo"] == 0
    assert client.get(
        f"/api/producao/solicitacoes?praca_id={praca_id}"
    ).get_json()["total"] == 1


def test_cozinha_pode_andar_status_mas_nao_realocar(app, seeded_client):
    client = seeded_client
    praca_id = _criar_praca(app, client)
    sp_id = _criar_solicitacao(client, praca_id)["id"]
    cozinha = app.test_client()
    login = cozinha.post("/api/auth/login", json={
        "username": "cozinha", "password": app.config["COOK_INITIAL_PASSWORD"]
    })
    assert login.status_code == 200, login.get_json()
    assert cozinha.get("/api/producao/solicitacoes").status_code == 200
    assert cozinha.post("/api/producao/solicitacoes", json={
        "ficha_tecnica_id": 1
    }).status_code == 403
    assert _alterar_praca(cozinha, sp_id, None).status_code == 403
    assert _alterar_status(cozinha, sp_id, "EM_PRODUCAO").status_code == 200


def test_conclusao_registra_estoque_sem_perder_vinculo_da_praca(app, seeded_client):
    client = seeded_client
    praca_id = _criar_praca(app, client)
    sp_id = _criar_solicitacao(client, praca_id)["id"]

    # Usa os insumos da ficha demonstrativa para verificar o fluxo real de baixa.
    with app.app_context():
        componentes = [dict(registro) for registro in db.session.execute(text(
            "SELECT fc.produto_id, fc.quantidade, p.conservacao "
            "FROM ficha_tecnica_componente fc "
            "JOIN produto p ON p.id = fc.produto_id "
            "WHERE fc.ficha_tecnica_id = 1"
        )).mappings()]
        locais = {
            r["tipo"]: r["id"] for r in db.session.execute(text(
                "SELECT id, tipo FROM localizacao ORDER BY id DESC"
            )).mappings()
        }
    for comp in componentes:
        lote = client.post("/api/estoque/lotes", json={
            "produto_id": comp["produto_id"],
            "localizacao_id": locais[comp["conservacao"]],
            "data_validade": "2099-12-31",
        })
        assert lote.status_code == 201, lote.get_json()
        entrada = client.post("/api/estoque/movimentacoes", json={
            "tipo": "ENTRADA", "lote_id": lote.get_json()["id"],
            "usuario_id": 1, "quantidade": float(comp["quantidade"]),
        })
        assert entrada.status_code == 201, entrada.get_json()

    assert client.delete(f"/api/pracas/{praca_id}").status_code == 204
    assert _alterar_status(client, sp_id, "EM_PRODUCAO").status_code == 200
    concluida = _alterar_status(client, sp_id, "CONCLUIDA")
    assert concluida.status_code == 200, concluida.get_json()
    assert concluida.get_json()["praca_id"] == praca_id
    assert concluida.get_json()["praca"]["ativo"] == 0

    detalhe = client.get(f"/api/producao/solicitacoes/{sp_id}").get_json()
    assert len(detalhe["lotes_produzidos"]) == 1
    assert sum(c["quantidade_realizada"] for c in detalhe["componentes"]) > 0
    assert _alterar_praca(client, sp_id, None).status_code == 409
    with app.app_context():
        contagem = db.session.execute(text(
            "SELECT COUNT(*) FROM movimentacao_estoque "
            "WHERE solicitacao_producao_id = :id"
        ), {"id": sp_id}).scalar_one()
        assert contagem == len(componentes) + 1
