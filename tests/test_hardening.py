import pytest

from app import create_app


def _criar_usuario(client, username="seguro1", papel="USER", password="Temp@1234"):
    resposta = client.post(
        "/api/auth/usuarios",
        json={"nome": "Usuário Seguro", "username": username, "password": password, "papel": papel},
    )
    assert resposta.status_code == 201, resposta.get_json()
    return resposta.get_json()


def test_primeiro_acesso_exige_troca_de_senha(client):
    criado = _criar_usuario(client)
    assert criado["deve_trocar_senha"] == 1
    client.post("/api/auth/logout")

    login = client.post("/api/auth/login", json={"username": "seguro1", "password": "Temp@1234"})
    assert login.status_code == 200
    assert login.get_json()["deve_trocar_senha"] == 1
    assert client.get("/api/fichas-tecnicas").status_code == 403

    errada = client.post(
        "/api/auth/change-password",
        json={"current_password": "Errada@123", "new_password": "Nova@1234"},
    )
    assert errada.status_code == 400

    troca = client.post(
        "/api/auth/change-password",
        json={"current_password": "Temp@1234", "new_password": "Nova@1234"},
    )
    assert troca.status_code == 200
    assert troca.get_json()["deve_trocar_senha"] == 0
    assert client.get("/api/fichas-tecnicas").status_code == 200


def test_senha_forte_e_reset_forca_nova_troca(client):
    usuario = _criar_usuario(client, username="reset1")
    fraca = client.put(f"/api/auth/usuarios/{usuario['id']}", json={"password": "abcdefgh"})
    assert fraca.status_code == 400

    reset = client.put(f"/api/auth/usuarios/{usuario['id']}", json={"password": "Reset@1234"})
    assert reset.status_code == 200
    assert reset.get_json()["deve_trocar_senha"] == 1


def test_bloqueio_temporario_apos_tentativas(client):
    client.post("/api/auth/logout")
    for tentativa in range(1, 6):
        resposta = client.post("/api/auth/login", json={"username": "dona", "password": "Errada@123"})
        assert resposta.status_code == (429 if tentativa == 5 else 401)

    bloqueado = client.post("/api/auth/login", json={"username": "dona", "password": "Teste@123"})
    assert bloqueado.status_code == 429


def test_auditoria_e_headers_de_seguranca(client):
    resposta = client.get("/api/auth/auditoria")
    assert resposta.status_code == 200
    eventos = resposta.get_json()
    assert any(item["evento"] == "LOGIN_SUCESSO" for item in eventos)

    health = client.get("/health", headers={"X-Request-ID": "request-teste-123"})
    assert health.headers["X-Request-ID"] == "request-teste-123"
    assert health.headers["X-Content-Type-Options"] == "nosniff"
    assert health.headers["X-Frame-Options"] == "DENY"
    assert health.headers["Referrer-Policy"] == "no-referrer"


def test_producao_recusa_configuracao_insegura():
    with pytest.raises(RuntimeError, match="Configuração insegura de produção"):
        create_app({
            "APP_ENV": "production",
            "TESTING": False,
            "SECRET_KEY": "curta",
            "SESSION_COOKIE_SECURE": False,
            "DB_CONNECTION": "sqlite",
        })
