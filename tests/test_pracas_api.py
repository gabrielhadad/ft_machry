"""Testes HTTP das regras de gerenciamento de praças (Fase 2)."""

from app.features.pracas.models import Praca
from app.features.producao.models import SolicitacaoProducao
from app.features.usuarios.models import Usuario
from db.database_config import db
from sqlalchemy import text


SENHA = "Senha@1234"


def _grupo_id(client, nome: str) -> int:
    grupos = client.get("/api/grupos-acesso").get_json()["items"]
    return next(grupo["id"] for grupo in grupos if grupo["nome"] == nome)


def _novo_usuario(client, username: str, grupo_id: int, *, nome: str | None = None):
    resposta = client.post("/api/usuarios", json={
        "nome": nome or username,
        "username": username,
        "password": SENHA,
        "grupos": [grupo_id],
    })
    assert resposta.status_code == 201, resposta.get_json()
    return resposta.get_json()


def _novo_cozinheiro(client, username: str, *, nome: str | None = None):
    return _novo_usuario(client, username, _grupo_id(client, "Cozinha"), nome=nome)


def _login(app, username: str):
    outro = app.test_client()
    resposta = outro.post("/api/auth/login", json={"username": username, "password": SENHA})
    assert resposta.status_code == 200, resposta.get_json()
    return outro


def _criar_praca(client, cozinheiros: list[int], nome: str = "Grelha"):
    return client.post("/api/pracas", json={
        "nome": nome, "descricao": "Estação de grelhados", "cozinheiros": cozinheiros
    })


def test_crud_pracas_com_varios_cozinheiros_e_desativacao(client):
    ana = _novo_cozinheiro(client, "ana", nome="Ana")
    bruno = _novo_cozinheiro(client, "bruno", nome="Bruno")
    criado = _criar_praca(client, [bruno["id"], ana["id"]])
    assert criado.status_code == 201, criado.get_json()
    praca = criado.get_json()
    assert praca["nome"] == "Grelha"
    assert praca["ativo"] == 1
    assert praca["criado_em"]
    assert [u["nome"] for u in praca["cozinheiros"]] == ["Ana", "Bruno"]

    caminho = f"/api/pracas/{praca['id']}"
    assert client.get(caminho).get_json() == praca
    pagina = client.get("/api/pracas?page=1&per_page=1").get_json()
    assert (pagina["total"], len(pagina["items"]), pagina["pages"]) == (1, 1, 1)

    alterado = client.put(caminho, json={
        "nome": "  Saladas  ", "descricao": " ", "cozinheiros": [ana["id"]]
    })
    assert alterado.status_code == 200, alterado.get_json()
    assert alterado.get_json()["nome"] == "Saladas"
    assert alterado.get_json()["descricao"] is None
    assert [u["id"] for u in alterado.get_json()["cozinheiros"]] == [ana["id"]]

    assert client.delete(caminho).status_code == 204
    assert client.delete(caminho).status_code == 204  # Repetir é idempotente.
    assert client.get(caminho).get_json()["ativo"] == 0
    assert client.get("/api/pracas").get_json()["total"] == 1
    assert client.put(caminho, json={"ativo": 1}).get_json()["ativo"] == 1


def test_validacoes_de_cozinheiros_e_payload(client):
    ana = _novo_cozinheiro(client, "ana")
    dono_id = client.get("/api/auth/me").get_json()["id"]
    invalido = [
        ([], 400),
        ([99999], 400),
        ([dono_id], 400),
        ([ana["id"], ana["id"]], 400),
        ([-3], 400),
    ]
    for ids, esperado in invalido:
        resposta = _criar_praca(client, ids)
        assert resposta.status_code == esperado, resposta.get_json()
    assert client.put(f"/api/usuarios/{ana['id']}", json={"ativo": 0}).status_code == 200
    assert _criar_praca(client, [ana["id"]]).status_code == 400
    assert client.get("/api/pracas").get_json()["total"] == 0

    assert client.post("/api/pracas", json={
        "nome": "A", "cozinheiros": [ana["id"]], "extra": 123
    }).status_code == 400
    assert client.post("/api/pracas", json={
        "nome": "  ", "cozinheiros": [ana["id"]]
    }).status_code == 400


def test_nome_unico_ignorando_caixa_e_atualizacao_atomica(app, client):
    ana = _novo_cozinheiro(client, "ana")
    primeira = _criar_praca(client, [ana["id"]], "Grelha")
    assert primeira.status_code == 201
    segunda = _criar_praca(client, [ana["id"]], "  grelha  ")
    assert segunda.status_code == 409

    praca_id = primeira.get_json()["id"]
    resposta = client.put(f"/api/pracas/{praca_id}", json={
        "nome": "Nova", "cozinheiros": [99999]
    })
    assert resposta.status_code == 400
    assert client.get(f"/api/pracas/{praca_id}").get_json()["nome"] == "Grelha"

    assert client.put(f"/api/pracas/{praca_id}", json={"cozinheiros": []}).status_code == 400
    assert client.put(f"/api/pracas/{praca_id}", json={"ativo": 2}).status_code == 400
    assert client.put(f"/api/pracas/{praca_id}", json={"ativo": None}).status_code == 400
    assert client.put(f"/api/pracas/{praca_id}", json={"nome": None}).status_code == 400
    assert client.put(f"/api/pracas/{praca_id}", json={}).status_code == 400

    with app.app_context():
        # A restrição de unicidade também existe no banco (não apenas no service).
        from sqlalchemy.exc import IntegrityError
        import pytest

        db.session.add(Praca(nome="GRELHA"))
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


def test_cozinheiro_inativo_impede_reativacao_ate_substituicao(client):
    ana = _novo_cozinheiro(client, "ana")
    bruno = _novo_cozinheiro(client, "bruno")
    praca_id = _criar_praca(client, [ana["id"]]).get_json()["id"]
    caminho = f"/api/pracas/{praca_id}"
    assert client.delete(caminho).status_code == 204
    assert client.put(f"/api/usuarios/{ana['id']}", json={"ativo": 0}).status_code == 200
    assert client.put(caminho, json={"ativo": 1}).status_code == 400
    resposta = client.put(caminho, json={"ativo": 1, "cozinheiros": [bruno["id"]]})
    assert resposta.status_code == 200, resposta.get_json()
    assert resposta.get_json()["ativo"] == 1
    assert [c["id"] for c in resposta.get_json()["cozinheiros"]] == [bruno["id"]]


def test_listagem_cozinheiros_e_permissoes(app, client):
    ana = _novo_cozinheiro(client, "ana")
    gestor = _novo_usuario(client, "gestor.teste", _grupo_id(client, "Gestor"))
    cozinha = _login(app, "ana")
    gestor_cliente = _login(app, "gestor.teste")

    resposta = cozinha.get("/api/pracas/cozinheiros")
    assert resposta.status_code == 200
    ids = {p["id"] for p in resposta.get_json()["items"]}
    assert ana["id"] in ids
    assert gestor["id"] not in ids
    assert cozinha.get("/api/pracas").status_code == 200
    assert cozinha.post("/api/pracas", json={"nome": "P", "cozinheiros": [ana["id"]]}).status_code == 403
    assert gestor_cliente.get("/api/pracas").status_code == 200
    criado = _criar_praca(gestor_cliente, [ana["id"]])
    assert criado.status_code == 201, criado.get_json()
    assert cozinha.delete(f"/api/pracas/{criado.get_json()['id']}").status_code == 403
    assert gestor_cliente.delete(f"/api/pracas/{criado.get_json()['id']}").status_code == 204

    sem_grupo = client.post("/api/usuarios", json={
        "nome": "Sem Grupo", "username": "sem.grupo", "password": SENHA, "grupos": []
    })
    assert sem_grupo.status_code == 201
    assert _login(app, "sem.grupo").get("/api/pracas").status_code == 403
    assert app.test_client().get("/api/pracas").status_code == 401


def test_desativar_preserva_solicitacao_e_vinculos(app, seeded_client):
    client = seeded_client
    with app.app_context():
        cozinheiro = next(
            u for u in db.session.execute(db.select(Usuario)).scalars()
            if any(g.nome == "Cozinha" for g in u.grupos)
        )
        ficha_id = db.session.execute(text("SELECT id FROM ficha_tecnica LIMIT 1")).scalar_one()
    criado = _criar_praca(client, [cozinheiro.id])
    assert criado.status_code == 201, criado.get_json()
    praca_id = criado.get_json()["id"]

    with app.app_context():
        solicitacao = SolicitacaoProducao(
            ficha_tecnica_id=ficha_id, usuario_id=cozinheiro.id, praca_id=praca_id
        )
        db.session.add(solicitacao)
        db.session.commit()
        sp_id = solicitacao.id

    assert client.delete(f"/api/pracas/{praca_id}").status_code == 204
    with app.app_context():
        assert db.session.get(SolicitacaoProducao, sp_id).praca_id == praca_id
        praca = db.session.get(Praca, praca_id)
        assert praca.ativo == 0
        assert [u.id for u in praca.cozinheiros] == [cozinheiro.id]


def test_rotas_ausentes_e_paginacao_invalida(client):
    assert client.get("/api/pracas/99999").status_code == 404
    assert client.put("/api/pracas/99999", json={"nome": "Nova"}).status_code == 404
    assert client.delete("/api/pracas/99999").status_code == 404
    assert client.get("/api/pracas?page=0").status_code == 400
    assert client.get("/api/pracas/cozinheiros?per_page=0").status_code == 400


def test_usuario_nao_pode_deixar_praca_ativa_sem_cozinheiro(client):
    ana = _novo_cozinheiro(client, "ana")
    bruno = _novo_cozinheiro(client, "bruno")
    praca = _criar_praca(client, [ana["id"]]).get_json()
    assert client.put(f"/api/usuarios/{ana['id']}", json={"ativo": 0}).status_code == 409
    assert client.put(f"/api/usuarios/{ana['id']}", json={"grupos": []}).status_code == 409
    assert client.delete(f"/api/usuarios/{ana['id']}").status_code == 409
    assert client.put(f"/api/pracas/{praca['id']}", json={
        "cozinheiros": [ana["id"], bruno["id"]]
    }).status_code == 200
    assert client.put(f"/api/usuarios/{ana['id']}", json={"ativo": 0}).status_code == 200
    assert client.get(f"/api/pracas/{praca['id']}").get_json()["ativo"] == 1
