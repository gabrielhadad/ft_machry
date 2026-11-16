from sqlalchemy import text

from app.utils.permissoes import catalogo_de_permissoes

SENHA = "Senha@1234"
PRODUTO = {"nome": "Sal", "tipo": "INSUMO", "unidade_medida": "g"}


def grupos_por_nome(client):
    grupos = client.get("/api/grupos-acesso").get_json()["items"]
    return {grupo["nome"]: grupo for grupo in grupos}


def codigos(grupo):
    return [permissao["codigo"] for permissao in grupo["permissoes"]]


def entrar_como(app, client, username, grupos):
    criado = client.post(
        "/api/usuarios",
        json={"nome": "Pessoa de Teste", "username": username, "password": SENHA, "grupos": grupos},
    )
    assert criado.status_code == 201, criado.get_json()
    outro = app.test_client()
    login = outro.post("/api/auth/login", json={"username": username, "password": SENHA})
    assert login.status_code == 200
    return outro


def test_lista_permissoes_do_catalogo(client):
    resposta = client.get("/api/permissoes?per_page=100")
    assert resposta.status_code == 200
    corpo = resposta.get_json()
    assert corpo["total"] == len(catalogo_de_permissoes())
    por_codigo = {permissao["codigo"]: permissao for permissao in corpo["items"]}
    assert "grupos_acesso:excluir" in por_codigo
    assert por_codigo["produtos:ler"]["recurso"] == "produtos"
    assert por_codigo["produtos:ler"]["acao"] == "ler"
    assert por_codigo["produtos:ler"]["descricao"] == "Visualizar produtos"


def test_grupos_padrao(client):
    grupos = grupos_por_nome(client)
    assert set(grupos) == {"Administrador", "Gestor", "Cozinha"}

    administrador = grupos["Administrador"]
    assert administrador["protegido"] == 1
    assert len(administrador["permissoes"]) == len(catalogo_de_permissoes())
    assert administrador["total_usuarios"] == 1

    assert set(codigos(grupos["Cozinha"])) == {
        "fichas_tecnicas:ler",
        "producao:ler",
        "producao:atualizar",
    }
    assert "produtos:criar" not in codigos(grupos["Gestor"])
    assert "estoque:criar" in codigos(grupos["Gestor"])


def test_crud_grupo(client):
    criado = client.post(
        "/api/grupos-acesso",
        json={
            "nome": "Estoquista",
            "descricao": "Recebe mercadoria",
            "permissoes": ["estoque:ler", "estoque:criar"],
        },
    )
    assert criado.status_code == 201
    corpo = criado.get_json()
    assert corpo["protegido"] == 0
    assert corpo["total_usuarios"] == 0
    assert codigos(corpo) == ["estoque:ler", "estoque:criar"]

    repetido = client.post("/api/grupos-acesso", json={"nome": "estoquista"})
    assert repetido.status_code == 409

    assert client.get(f"/api/grupos-acesso/{corpo['id']}").status_code == 200

    atualizado = client.put(
        f"/api/grupos-acesso/{corpo['id']}",
        json={"nome": "Conferente", "permissoes": ["estoque:ler"]},
    )
    assert atualizado.status_code == 200
    assert atualizado.get_json()["nome"] == "Conferente"
    assert codigos(atualizado.get_json()) == ["estoque:ler"]

    invalido = client.put(
        f"/api/grupos-acesso/{corpo['id']}", json={"permissoes": ["estoque:voar"]}
    )
    assert invalido.status_code == 400

    assert client.delete(f"/api/grupos-acesso/{corpo['id']}").status_code == 204
    assert client.get(f"/api/grupos-acesso/{corpo['id']}").status_code == 404


def test_grupo_administrador_e_protegido(client):
    administrador = grupos_por_nome(client)["Administrador"]
    caminho = f"/api/grupos-acesso/{administrador['id']}"
    assert client.put(caminho, json={"nome": "Chefe"}).status_code == 409
    assert client.delete(caminho).status_code == 409


def test_permissoes_limitam_as_rotas(app, client):
    criado = client.post(
        "/api/grupos-acesso", json={"nome": "Leitura de produtos", "permissoes": ["produtos:ler"]}
    ).get_json()
    leitor = entrar_como(app, client, "leitor", [criado["id"]])

    assert leitor.get("/api/produtos").status_code == 200
    assert leitor.post("/api/produtos", json=PRODUTO).status_code == 403
    assert leitor.get("/api/estoque/lotes").status_code == 403
    assert leitor.get("/api/usuarios").status_code == 403
    assert leitor.get("/api/auth/me").status_code == 200


def test_grupo_gestor(app, client):
    grupos = grupos_por_nome(client)
    gestor = entrar_como(app, client, "gestor.turno", [grupos["Gestor"]["id"]])

    assert gestor.get("/api/produtos").status_code == 200
    assert gestor.post("/api/produtos", json=PRODUTO).status_code == 403
    assert gestor.get("/api/estoque/localizacoes").status_code == 200
    assert gestor.get("/api/usuarios").status_code == 403
    assert gestor.get("/api/grupos-acesso").status_code == 403


def test_grupo_cozinha(app, client):
    grupos = grupos_por_nome(client)
    cozinha = entrar_como(app, client, "cozinha.turno", [grupos["Cozinha"]["id"]])

    assert cozinha.get("/api/producao/solicitacoes").status_code == 200
    assert cozinha.get("/api/fichas-tecnicas").status_code == 200
    criar = cozinha.post("/api/producao/solicitacoes", json={"ficha_tecnica_id": 1})
    assert criar.status_code == 403
    assert cozinha.get("/api/estoque/lotes").status_code == 403


def test_usuario_sem_grupo_nao_acessa_nada(app, client):
    sem_grupo = entrar_como(app, client, "sem.grupo", [])
    assert sem_grupo.get("/api/auth/me").get_json()["permissoes"] == []
    assert sem_grupo.get("/api/fichas-tecnicas").status_code == 403


def test_rota_sem_permissao_configurada_e_bloqueada(app):
    app.add_url_rule(
        "/api/teste-sem-permissao", endpoint="teste", view_func=lambda: {"ok": True}
    )
    with app.app_context():
        result = app.test_cli_runner().invoke(args=["init-db"])
    assert result.exit_code == 0, result.output
    client = app.test_client()
    client.post("/api/auth/login", json={"username": "dona", "password": "Teste@123"})

    resposta = client.get("/api/teste-sem-permissao")
    assert resposta.status_code == 403
    assert resposta.get_json()["erro"] == "rota sem permissão configurada"


def test_migra_papeis_antigos_para_grupos(app):
    from db.database_config import db

    with app.app_context():
        result = app.test_cli_runner().invoke(args=["init-db"])
        assert result.exit_code == 0, result.output

        db.session.execute(text("ALTER TABLE usuario ADD COLUMN papel TEXT"))
        db.session.execute(text("UPDATE usuario SET papel = 'OWNER' WHERE username = 'dona'"))
        db.session.execute(text("UPDATE usuario SET papel = 'ADMIN' WHERE username = 'gestor'"))
        db.session.execute(text("UPDATE usuario SET papel = 'USER' WHERE username = 'cozinha'"))
        db.session.execute(text(
            "INSERT INTO usuario (nome, username, senha_hash, papel) "
            "VALUES ('Antiga', 'antiga', 'x', 'ADMIN')"
        ))
        db.session.execute(text("DELETE FROM usuario_grupo_acesso"))
        db.session.commit()

        result = app.test_cli_runner().invoke(args=["init-db"])
        assert result.exit_code == 0, result.output

        vinculos = db.session.execute(text(
            "SELECT u.username, g.nome FROM usuario u "
            "JOIN usuario_grupo_acesso v ON v.usuario_id = u.id "
            "JOIN grupo_acesso g ON g.id = v.grupo_acesso_id"
        )).all()

    assert dict(vinculos) == {
        "dona": "Administrador",
        "gestor": "Gestor",
        "cozinha": "Cozinha",
        "antiga": "Gestor",
    }
