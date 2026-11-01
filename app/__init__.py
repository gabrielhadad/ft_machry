import logging
import os
import time
import uuid
from datetime import timedelta

from flask import Flask, g, request, send_from_directory, session

from app.features import auth, estoque, fichas_tecnicas, producao, produtos
from app.features.auth.models import Usuario
from app.utils.config import config as app_config
from db.database_config import db, init_app as init_db

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_PATH = os.path.join(ROOT_PATH, "docs")


def _validar_producao(app: Flask) -> None:
    ambiente = str(app.config.get("APP_ENV", "development")).lower()
    if ambiente != "production" or app.config.get("TESTING"):
        return
    erros = []
    secret = str(app.config.get("SECRET_KEY") or "")
    if len(secret) < 32 or secret == "machry-desenvolvimento-troque-em-producao":
        erros.append("SECRET_KEY deve ter pelo menos 32 caracteres aleatórios")
    if not app.config.get("SESSION_COOKIE_SECURE"):
        erros.append("SESSION_COOKIE_SECURE deve estar habilitado")
    uri = str(app.config.get("DATABASE_URL") or "")
    conexao = str(app.config.get("DB_CONNECTION", "sqlite")).lower()
    if (not uri and conexao == "sqlite") or uri.startswith("sqlite"):
        erros.append("produção deve usar PostgreSQL, não SQLite")
    defaults = {"Dona@123", "Gestor@123", "Cozinha@123"}
    for chave in ("OWNER_INITIAL_PASSWORD", "MANAGER_INITIAL_PASSWORD", "COOK_INITIAL_PASSWORD"):
        valor = str(app.config.get(chave) or "")
        if len(valor) < 8 or valor in defaults:
            erros.append(f"{chave} precisa ser alterada antes do deploy")
    if erros:
        raise RuntimeError("Configuração insegura de produção: " + "; ".join(erros))


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    prefixo_api = "/api"
    app.config.from_object(app_config)
    if config:
        app.config.update(config)

    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(
        minutes=int(app.config.get("SESSION_LIFETIME_MINUTES", 480))
    )
    app.config.setdefault("SESSION_REFRESH_EACH_REQUEST", True)
    _validar_producao(app)
    init_db(app)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    @app.before_request
    def carregar_usuario_e_proteger_api():
        g.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        g.request_started = time.perf_counter()
        usuario_id = session.get("usuario_id")
        g.usuario = db.session.get(Usuario, usuario_id) if usuario_id else None
        if g.usuario is not None and not g.usuario.ativo:
            session.clear()
            g.usuario = None

        if not request.path.startswith("/api/") or request.path == "/api/auth/login":
            return None
        if g.usuario is None:
            return {"erro": "autenticação necessária"}, 401

        caminho = request.path
        if g.usuario.deve_trocar_senha and caminho not in {
            "/api/auth/me", "/api/auth/logout", "/api/auth/change-password"
        }:
            return {"erro": "troca de senha obrigatória antes de continuar"}, 403

        papel = g.usuario.papel
        metodo = request.method
        if caminho in {"/api/auth/me", "/api/auth/logout", "/api/auth/change-password"}:
            return None
        if papel == "OWNER":
            return None
        if papel == "ADMIN":
            if caminho.startswith("/api/auth/usuarios") or caminho.startswith("/api/auth/auditoria"):
                return {"erro": "você não tem permissão para esta ação"}, 403
            if caminho.startswith(("/api/produtos", "/api/fichas-tecnicas")) and metodo != "GET":
                return {"erro": "somente a proprietária pode alterar produtos e fichas"}, 403
            return None
        if papel == "USER" and metodo == "GET" and caminho.startswith(("/api/producao", "/api/fichas-tecnicas")):
            return None
        if papel == "USER" and metodo == "GET" and caminho == "/api/estoque/localizacoes":
            return None
        if papel == "USER" and metodo == "PUT" and caminho.startswith("/api/producao/solicitacoes/") and (
            caminho.endswith("/status") or caminho.endswith("/execucao")
        ):
            return None
        return {"erro": "você não tem permissão para acessar este recurso"}, 403

    @app.after_request
    def aplicar_cabecalhos_e_logar(response):
        response.headers["X-Request-ID"] = getattr(g, "request_id", "")
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        if request.path.startswith("/api/auth/"):
            response.headers["Cache-Control"] = "no-store"
        if str(app.config.get("APP_ENV", "development")).lower() == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        inicio = getattr(g, "request_started", None)
        duracao = round((time.perf_counter() - inicio) * 1000, 2) if inicio else None
        app.logger.info(
            "request_id=%s method=%s path=%s status=%s duration_ms=%s user_id=%s",
            getattr(g, "request_id", "-"), request.method, request.path, response.status_code,
            duracao, getattr(getattr(g, "usuario", None), "id", None),
        )
        return response

    app.register_blueprint(auth.bp, url_prefix=f"{prefixo_api}/auth")
    app.register_blueprint(produtos.bp, url_prefix=f"{prefixo_api}/produtos")
    app.register_blueprint(fichas_tecnicas.bp, url_prefix=f"{prefixo_api}/fichas-tecnicas")
    app.register_blueprint(estoque.bp, url_prefix=f"{prefixo_api}/estoque")
    app.register_blueprint(producao.bp, url_prefix=f"{prefixo_api}/producao")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/openapi.yaml")
    def openapi():
        return send_from_directory(DOCS_PATH, "openapi.yaml")

    @app.get("/docs")
    def docs():
        return send_from_directory(DOCS_PATH, "swagger-ui.html")

    return app
