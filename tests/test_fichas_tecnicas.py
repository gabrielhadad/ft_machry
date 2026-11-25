from app.features.fichas_tecnicas.models import FaseProducao
from db.database_config import db


URL = "/api/fichas-tecnicas"


def _produto(client, nome, tipo):
    resposta = client.post(
        "/api/produtos",
        json={"nome": nome, "tipo": tipo, "unidade_medida": "g"},
    )
    assert resposta.status_code == 201
    return resposta.get_json()["id"]


def _preparar(app, client):
    with app.app_context():
        db.session.add_all(
            [FaseProducao(nome="Preparar"), FaseProducao(nome="Cozinhar")]
        )
        db.session.commit()
        fases = db.session.query(FaseProducao).order_by(FaseProducao.id).all()
        fase_ids = [fase.id for fase in fases]
    insumo = _produto(client, "Farinha", "INSUMO")
    final = _produto(client, "Pão", "FINAL")
    return insumo, final, fase_ids


def test_crud_ficha_tecnica(app, client):
    insumo, final, fases = _preparar(app, client)
    payload = {
        "produto_id": final,
        "rendimento": 10,
        "observacao": "Receita base",
        "fases": [
            {"fase_id": fases[0], "ordem": 1, "tempo_previsto_min": 5},
            {"fase_id": fases[1], "ordem": 2, "tempo_previsto_min": 30},
        ],
        "componentes": [
            {"produto_id": insumo, "quantidade": 500, "fase_ordem": 1}
        ],
    }

    criada = client.post(URL, json=payload)
    assert criada.status_code == 201, criada.get_json()
    ficha = criada.get_json()
    assert ficha["produto"] == "Pão"
    assert ficha["componentes"][0]["fase_ordem"] == 1

    payload["rendimento"] = 12
    atualizada = client.put(f"{URL}/{ficha['id']}", json=payload)
    assert atualizada.status_code == 200
    assert atualizada.get_json()["rendimento"] == 12

    assert client.delete(f"{URL}/{ficha['id']}").status_code == 204
    assert client.get(f"{URL}/{ficha['id']}").status_code == 404


def test_regras_da_ficha(app, client):
    insumo, final, fases = _preparar(app, client)
    base = {
        "produto_id": final,
        "rendimento": 1,
        "fases": [{"fase_id": fases[0], "ordem": 1, "tempo_previsto_min": 5}],
        "componentes": [{"produto_id": insumo, "quantidade": 1}],
    }
    assert client.post(URL, json={**base, "produto_id": insumo}).status_code == 400
    assert client.post(URL, json={**base, "componentes": [{"produto_id": final, "quantidade": 1}]}).status_code == 400
    assert client.post(URL, json=base).status_code == 201
    assert client.post(URL, json=base).status_code == 409
    assert client.put(f"/api/produtos/{final}", json={"tipo": "INSUMO"}).status_code == 400



def test_custo_da_ficha_usa_custo_medio_ponderado_movel(app, client):
    from app.features.estoque.models import Localizacao

    insumo, final, fases = _preparar(app, client)
    sem_custo = _produto(client, "Sal", "INSUMO")
    with app.app_context():
        local = Localizacao(nome="Despensa")
        db.session.add(local)
        db.session.commit()
        local_id = local.id

    def lote(produto, custo=None):
        dados = {"produto_id": produto, "localizacao_id": local_id}
        if custo is not None:
            dados["custo_unitario"] = custo
        resposta = client.post("/api/estoque/lotes", json=dados)
        assert resposta.status_code == 201, resposta.get_json()
        return resposta.get_json()["id"]

    def movimentar(tipo, lote_id, quantidade):
        resposta = client.post("/api/estoque/movimentacoes", json={
            "tipo": tipo, "lote_id": lote_id, "usuario_id": 1,
            "quantidade": quantidade, "motivo": "teste",
        })
        assert resposta.status_code == 201, resposta.get_json()

    barato, caro = lote(insumo, 0.02), lote(insumo, 0.08)
    movimentar("ENTRADA", barato, 100)   # média 0,02 com saldo 100
    movimentar("ENTRADA", caro, 100)     # média (100*0,02 + 100*0,08) / 200 = 0,05
    movimentar("SAIDA", barato, 100)     # saída não muda a média
    movimentar("ENTRADA", lote(sem_custo), 50)

    ficha = client.post(URL, json={
        "produto_id": final,
        "rendimento": 1,
        "fases": [{"fase_id": fases[0], "ordem": 1, "tempo_previsto_min": 5}],
        "componentes": [
            {"produto_id": insumo, "quantidade": 500},
            {"produto_id": sem_custo, "quantidade": 10},
        ],
    }).get_json()

    componentes = {item["produto_id"]: item for item in ficha["componentes"]}
    assert componentes[insumo]["custo_unitario"] == 0.05
    assert componentes[insumo]["custo"] == 25.0
    assert componentes[sem_custo]["custo"] is None
    assert ficha["custo_total"] == 25.0
    assert ficha["custo_completo"] is False

    # Nova entrada mais cara: (100*0,05 + 100*0,11) / 200 = 0,08
    movimentar("ENTRADA", lote(insumo, 0.11), 100)
    atualizada = client.get(f"{URL}/{ficha['id']}").get_json()
    assert atualizada["custo_total"] == 40.0


def test_metodo_de_custo_configuravel(app, client):
    from app.features.estoque.models import Localizacao

    insumo, final, fases = _preparar(app, client)
    with app.app_context():
        local = Localizacao(nome="Despensa")
        db.session.add(local)
        db.session.commit()
        local_id = local.id

    def lote(custo):
        return client.post("/api/estoque/lotes", json={
            "produto_id": insumo, "localizacao_id": local_id, "custo_unitario": custo,
        }).get_json()["id"]

    def movimentar(tipo, lote_id, quantidade):
        assert client.post("/api/estoque/movimentacoes", json={
            "tipo": tipo, "lote_id": lote_id, "usuario_id": 1,
            "quantidade": quantidade, "motivo": "teste",
        }).status_code == 201

    barato, caro = lote(0.02), lote(0.08)
    movimentar("ENTRADA", barato, 100)
    movimentar("ENTRADA", caro, 100)
    movimentar("SAIDA", barato, 100)
    ficha = client.post(URL, json={
        "produto_id": final,
        "rendimento": 1,
        "fases": [{"fase_id": fases[0], "ordem": 1, "tempo_previsto_min": 5}],
        "componentes": [{"produto_id": insumo, "quantidade": 500}],
    }).get_json()

    assert client.get("/api/configuracoes").get_json() == {"metodo_custo_medio": "PONDERADO_MOVEL"}
    assert ficha["custo_total"] == 25.0  # móvel: a saída não muda a média de 0,05

    resposta = client.put("/api/configuracoes", json={"metodo_custo_medio": "PONDERADO_SALDO"})
    assert resposta.status_code == 200
    assert resposta.get_json()["metodo_custo_medio"] == "PONDERADO_SALDO"
    # pelo saldo: só resta o lote de 0,08
    assert client.get(f"{URL}/{ficha['id']}").get_json()["custo_total"] == 40.0

    assert client.put("/api/configuracoes", json={"metodo_custo_medio": "OUTRO"}).status_code == 400
    assert client.put("/api/configuracoes", json={"desconhecido": 1}).status_code == 400



def test_custo_fefo_mostra_quanto_custaria_consumir_agora(app, client):
    from app.features.estoque.models import Localizacao

    insumo, final, fases = _preparar(app, client)
    with app.app_context():
        local = Localizacao(nome="Despensa")
        db.session.add(local)
        db.session.commit()
        local_id = local.id

    def lote_com_saldo(custo, validade, quantidade):
        lote_id = client.post("/api/estoque/lotes", json={
            "produto_id": insumo, "localizacao_id": local_id,
            "custo_unitario": custo, "data_validade": validade,
        }).get_json()["id"]
        assert client.post("/api/estoque/movimentacoes", json={
            "tipo": "ENTRADA", "lote_id": lote_id, "usuario_id": 1, "quantidade": quantidade,
        }).status_code == 201
        return lote_id

    # O lote mais caro vence primeiro, então o FEFO começa por ele.
    lote_com_saldo(0.10, "2098-01-01", 300)
    lote_com_saldo(0.01, "2099-01-01", 1000)
    ficha = client.post(URL, json={
        "produto_id": final,
        "rendimento": 1,
        "fases": [{"fase_id": fases[0], "ordem": 1, "tempo_previsto_min": 5}],
        "componentes": [{"produto_id": insumo, "quantidade": 500}],
    }).get_json()

    componente = ficha["componentes"][0]
    # 300 * 0,10 + 200 * 0,01 = 32,00
    assert componente["custo_fefo"] == 32.0
    assert componente["custo_fefo_completo"] is True
    assert componente["falta_estoque"] == 0
    assert ficha["custo_total_fefo"] == 32.0
    # média móvel: (300*0,10 + 1000*0,01) / 1300 por grama, vezes 500
    assert ficha["custo_total"] == 15.38

    # A listagem não traz custos; o detalhe traz.
    listada = client.get(URL).get_json()["items"][0]
    assert "custo_total" not in listada and "custo_fefo" not in listada["componentes"][0]

    # Sem saldo suficiente, mostra o que dá para cobrir e quanto falta.
    maior = client.put(f"{URL}/{ficha['id']}", json={
        "produto_id": final,
        "rendimento": 1,
        "fases": [{"fase_id": fases[0], "ordem": 1, "tempo_previsto_min": 5}],
        "componentes": [{"produto_id": insumo, "quantidade": 1500}],
    }).get_json()
    componente = maior["componentes"][0]
    assert componente["falta_estoque"] == 200
    assert componente["custo_fefo"] == 40.0
    assert componente["custo_fefo_completo"] is False
    assert maior["custo_fefo_completo"] is False


def test_custos_usam_decimal(app, client):
    from app.features.estoque.models import Localizacao

    insumo, final, fases = _preparar(app, client)
    with app.app_context():
        local = Localizacao(nome="Despensa")
        db.session.add(local)
        db.session.commit()
        local_id = local.id
    lote_id = client.post("/api/estoque/lotes", json={
        "produto_id": insumo, "localizacao_id": local_id, "custo_unitario": 0.1,
    }).get_json()["id"]
    assert client.post("/api/estoque/movimentacoes", json={
        "tipo": "ENTRADA", "lote_id": lote_id, "usuario_id": 1, "quantidade": 3,
    }).status_code == 201
    ficha = client.post(URL, json={
        "produto_id": final,
        "rendimento": 1,
        "fases": [{"fase_id": fases[0], "ordem": 1, "tempo_previsto_min": 5}],
        "componentes": [{"produto_id": insumo, "quantidade": 3}],
    }).get_json()
    componente = ficha["componentes"][0]
    assert componente["custo_unitario"] == 0.1
    assert componente["custo"] == 0.3
    assert componente["custo_fefo"] == 0.3
    # Mais de 6 casas no custo unitário é recusado em vez de arredondado em silêncio.
    assert client.put(f"/api/estoque/lotes/{lote_id}", json={"custo_unitario": 0.1234567}).status_code == 400
