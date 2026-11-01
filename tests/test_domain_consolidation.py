from app.features.auth.models import Usuario
from db.database_config import db


def test_dominios_legados_nao_estao_no_metadata(app):
    """Garante que a fusão não reintroduza entidades paralelas do GAP."""
    with app.app_context():
        tabelas = set(db.metadata.tables)

    assert "produto" in tabelas
    assert "lote" in tabelas
    assert "ficha_tecnica" in tabelas
    assert "solicitacao_producao" in tabelas

    assert {
        "item",
        "ingrediente_ficha",
        "etapa_ficha_tecnica",
        "processamento",
        "item_processamento",
        "etapa_processamento",
    }.isdisjoint(tabelas)


def test_usuario_pertence_ao_dominio_auth():
    assert Usuario.__module__ == "app.features.auth.models"


def test_rotas_legadas_do_gap_nao_estao_expostas(app):
    rotas = {rule.rule for rule in app.url_map.iter_rules()}

    assert "/api/produtos" in rotas
    assert "/api/fichas-tecnicas" in rotas
    assert "/api/estoque/lotes" in rotas
    assert "/api/producao/solicitacoes" in rotas

    assert "/items" not in rotas
    assert "/lotes" not in rotas
    assert "/processamentos" not in rotas


def test_catalogo_nao_pode_invalidar_conservacao_de_lote(seeded_client):
    c = seeded_client
    lote = c.post(
        "/api/estoque/lotes",
        json={"produto_id": 1, "localizacao_id": 1},
    )
    assert lote.status_code == 201, lote.get_json()

    resposta = c.put("/api/produtos/1", json={"conservacao": "RESFRIADO"})
    assert resposta.status_code == 400

    produto = c.get("/api/produtos/1").get_json()
    assert produto["conservacao"] == "SECO"


def test_catalogo_nao_pode_exigir_validade_com_lote_sem_validade(seeded_client):
    c = seeded_client
    lote = c.post(
        "/api/estoque/lotes",
        json={"produto_id": 1, "localizacao_id": 1},
    )
    assert lote.status_code == 201, lote.get_json()
    assert lote.get_json()["data_validade"] is None

    resposta = c.put("/api/produtos/1", json={"validade_obrigatoria": 1})
    assert resposta.status_code == 400

    produto = c.get("/api/produtos/1").get_json()
    assert produto["validade_obrigatoria"] == 0


def test_fefo_prioriza_validade_e_deixa_sem_validade_por_ultimo(seeded_client):
    c = seeded_client

    def criar_lote(validade):
        payload = {"produto_id": 1, "localizacao_id": 1}
        if validade is not None:
            payload["data_validade"] = validade
        resposta = c.post("/api/estoque/lotes", json=payload)
        assert resposta.status_code == 201, resposta.get_json()
        lote_id = resposta.get_json()["id"]
        entrada = c.post(
            "/api/estoque/movimentacoes",
            json={
                "tipo": "ENTRADA",
                "lote_id": lote_id,
                "usuario_id": 1,
                "quantidade": 2,
            },
        )
        assert entrada.status_code == 201, entrada.get_json()
        return lote_id

    expirado = criar_lote("2000-01-01")
    mais_cedo = criar_lote("2099-01-01")
    mais_tarde = criar_lote("2099-02-01")
    sem_validade = criar_lote(None)

    resposta = c.get("/api/estoque/sugestao-saida/1?quantidade=5")
    assert resposta.status_code == 200
    lotes = resposta.get_json()["lotes"]

    assert [item["lote_id"] for item in lotes] == [
        mais_cedo,
        mais_tarde,
        sem_validade,
    ]
    assert expirado not in {item["lote_id"] for item in lotes}
    assert [item["quantidade"] for item in lotes] == [2, 2, 1]
