NOVO = {
    "nome": "Maria Souza",
    "username": "Maria.Souza",
    "password": "Senha@1234",
}


def grupo_id(client, nome):
    grupos = client.get("/api/grupos-acesso").get_json()["items"]
    return next(grupo["id"] for grupo in grupos if grupo["nome"] == nome)


def test_sessao_expira_apos_inatividade(app):
    from datetime import timedelta

    assert app.config["PERMANENT_SESSION_LIFETIME"] == timedelta(minutes=60)
    assert app.config["SESSION_REFRESH_EACH_REQUEST"] is True


def test_login_logout_e_me(client):
    resposta = client.get("/api/auth/me")
    assert resposta.status_code == 200
    corpo = resposta.get_json()
    assert corpo["username"] == "dona"
    assert "senha_hash" not in corpo
    assert [grupo["nome"] for grupo in corpo["grupos"]] == ["Administrador"]
    assert "usuarios:criar" in corpo["permissoes"]

    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_login_invalido(client):
    resposta = client.post("/api/auth/login", json={"username": "dona", "password": "errada"})
    assert resposta.status_code == 401


def test_crud_usuario(client):
    cozinha = grupo_id(client, "Cozinha")
    gestor = grupo_id(client, "Gestor")

    criado = client.post("/api/usuarios", json={**NOVO, "grupos": [cozinha]})
    assert criado.status_code == 201
    corpo = criado.get_json()
    assert corpo["username"] == "maria.souza"
    assert [grupo["nome"] for grupo in corpo["grupos"]] == ["Cozinha"]
    assert "permissoes" not in corpo

    assert client.post("/api/usuarios", json={**NOVO, "grupos": [cozinha]}).status_code == 409

    usernames = [u["username"] for u in client.get("/api/usuarios").get_json()["items"]]
    assert "maria.souza" in usernames

    atualizado = client.put(f"/api/usuarios/{corpo['id']}", json={"grupos": [gestor], "ativo": 0})
    assert atualizado.status_code == 200
    assert [grupo["nome"] for grupo in atualizado.get_json()["grupos"]] == ["Gestor"]
    assert atualizado.get_json()["ativo"] == 0

    assert client.put("/api/usuarios/9999", json={"nome": "Alguém"}).status_code == 404


def test_grupo_inexistente_ao_criar_usuario(client):
    resposta = client.post("/api/usuarios", json={**NOVO, "grupos": [9999]})
    assert resposta.status_code == 400


def test_excluir_usuario_apenas_desativa(app, client):
    cozinha = grupo_id(client, "Cozinha")
    criado = client.post("/api/usuarios", json={**NOVO, "grupos": [cozinha]}).get_json()

    assert client.delete(f"/api/usuarios/{criado['id']}").status_code == 204

    usuarios = {u["username"]: u for u in client.get("/api/usuarios").get_json()["items"]}
    assert usuarios["maria.souza"]["ativo"] == 0
    assert [grupo["nome"] for grupo in usuarios["maria.souza"]["grupos"]] == ["Cozinha"]

    outro = app.test_client()
    login = outro.post(
        "/api/auth/login", json={"username": "maria.souza", "password": NOVO["password"]}
    )
    assert login.status_code == 401

    assert client.delete("/api/usuarios/9999").status_code == 404


def test_nao_exclui_a_propria_conta(client):
    meu_id = client.get("/api/auth/me").get_json()["id"]
    assert client.delete(f"/api/usuarios/{meu_id}").status_code == 409


def test_excluir_exige_permissao(app, client):
    gestor = grupo_id(client, "Gestor")
    alvo = client.post("/api/usuarios", json={**NOVO, "grupos": [gestor]}).get_json()
    client.post(
        "/api/usuarios",
        json={
            "nome": "Outra Pessoa",
            "username": "outra",
            "password": "Senha@1234",
            "grupos": [gestor],
        },
    )
    outro = app.test_client()
    outro.post("/api/auth/login", json={"username": "outra", "password": "Senha@1234"})
    assert outro.delete(f"/api/usuarios/{alvo['id']}").status_code == 403


def test_nao_desativa_a_propria_conta(client):
    meu_id = client.get("/api/auth/me").get_json()["id"]
    resposta = client.put(f"/api/usuarios/{meu_id}", json={"ativo": 0})
    assert resposta.status_code == 409


def test_administrador_precisa_de_usuario_ativo(client):
    meu_id = client.get("/api/auth/me").get_json()["id"]
    resposta = client.put(f"/api/usuarios/{meu_id}", json={"grupos": []})
    assert resposta.status_code == 409


def test_sem_permissao_nao_gerencia_usuarios(app, client):
    gestor = grupo_id(client, "Gestor")
    client.post("/api/usuarios", json={**NOVO, "grupos": [gestor]})
    outro = app.test_client()
    login = outro.post(
        "/api/auth/login", json={"username": "maria.souza", "password": NOVO["password"]}
    )
    assert login.status_code == 200
    assert "usuarios:ler" not in login.get_json()["permissoes"]
    assert outro.get("/api/usuarios").status_code == 403
    assert outro.post("/api/usuarios", json=NOVO).status_code == 403
