def _criar_e_logar(client, papel: str, username: str):
    resposta = client.post(
        "/api/auth/usuarios",
        json={
            "nome": f"Teste {papel}",
            "username": username,
            "password": "Teste@1234",
            "papel": papel,
        },
    )
    assert resposta.status_code == 201, resposta.get_json()
    client.post("/api/auth/logout")
    login = client.post(
        "/api/auth/login",
        json={"username": username, "password": "Teste@1234"},
    )
    assert login.status_code == 200, login.get_json()
    usuario = login.get_json()
    if usuario.get("deve_trocar_senha"):
        troca = client.post(
            "/api/auth/change-password",
            json={"current_password": "Teste@1234", "new_password": "Nova@1234"},
        )
        assert troca.status_code == 200, troca.get_json()
        usuario = troca.get_json()
    return usuario


def test_owner_lista_responsaveis_ativos(client):
    resposta = client.get("/api/auth/responsaveis")
    assert resposta.status_code == 200
    assert resposta.get_json()
    assert all(usuario["ativo"] == 1 for usuario in resposta.get_json())


def test_admin_pode_listar_responsaveis(client):
    _criar_e_logar(client, "ADMIN", "gestor88")
    resposta = client.get("/api/auth/responsaveis")
    assert resposta.status_code == 200


def test_cozinha_nao_pode_listar_responsaveis_mas_pode_listar_locais(client):
    _criar_e_logar(client, "USER", "cozinha88")
    assert client.get("/api/auth/responsaveis").status_code == 403
    assert client.get("/api/estoque/localizacoes").status_code == 200
