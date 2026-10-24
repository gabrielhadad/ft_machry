import os

from flask import Flask, g, request, send_from_directory, session

from app.utils.config import config as app_config
from app.features import auth, estoque, fichas_tecnicas, producao, produtos
from app.features.estoque.models import Usuario
from db.database_config import db, init_app as init_db

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_PATH = os.path.join(ROOT_PATH, "docs")

def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    prefixo_api = "/api"
    
    app.config.from_object(app_config)
    if config:
        app.config.update(config)

    init_db(app)

    @app.before_request
    def carregar_usuario_e_proteger_api():
        usuario_id = session.get("usuario_id")
        g.usuario = db.session.get(Usuario, usuario_id) if usuario_id else None
        if g.usuario is not None and not g.usuario.ativo:
            session.clear()
            g.usuario = None
        if not request.path.startswith("/api/") or request.path == "/api/auth/login":
            return None
        if g.usuario is None:
            return {"erro": "autenticação necessária"}, 401

        papel = g.usuario.papel
        metodo = request.method
        caminho = request.path
        if caminho in {"/api/auth/me", "/api/auth/logout"}:
            return None
        if papel == "OWNER":
            return None
        if papel == "ADMIN":
            if caminho.startswith("/api/auth/usuarios"):
                return {"erro": "você não tem permissão para esta ação"}, 403
            if caminho.startswith(("/api/produtos", "/api/fichas-tecnicas")) and metodo != "GET":
                return {"erro": "somente a proprietária pode alterar produtos e fichas"}, 403
            return None
        if papel == "USER" and metodo == "GET" and caminho.startswith(("/api/producao", "/api/fichas-tecnicas")):
            return None
        if papel == "USER" and metodo == "PUT" and caminho.startswith("/api/producao/solicitacoes/") and caminho.endswith("/status"):
            return None
        return {"erro": "você não tem permissão para acessar este recurso"}, 403

    app.register_blueprint(auth.bp, url_prefix=f"{prefixo_api}/auth")
    app.register_blueprint(produtos.bp, url_prefix=f"{prefixo_api}/produtos")
    app.register_blueprint(
        fichas_tecnicas.bp, url_prefix=f"{prefixo_api}/fichas-tecnicas"
    )
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
