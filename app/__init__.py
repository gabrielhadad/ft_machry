import os

from flask import Flask, render_template, send_from_directory

from app.utils.config import config as app_config
from app.features import estoque, fichas_tecnicas, producao, produtos
from db.database_config import init_app as init_db

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_PATH = os.path.join(ROOT_PATH, "docs")
FRONTEND_PATH = os.path.join(ROOT_PATH, "frontend")

def create_app(config: dict | None = None) -> Flask:
    app = Flask(
        __name__,
        template_folder=os.path.join(FRONTEND_PATH, "templates"),
        static_folder=os.path.join(FRONTEND_PATH, "static"),
    )
    prefixo_api = "/api"
    
    app.config.from_object(app_config)
    if config:
        app.config.update(config)

    init_db(app)

    app.register_blueprint(produtos.bp, url_prefix=f"{prefixo_api}/produtos")
    app.register_blueprint(
        fichas_tecnicas.bp, url_prefix=f"{prefixo_api}/fichas-tecnicas"
    )
    app.register_blueprint(estoque.bp, url_prefix=f"{prefixo_api}/estoque")
    app.register_blueprint(producao.bp, url_prefix=f"{prefixo_api}/producao")

    @app.get("/painel")
    def painel():
        return render_template("painel.html")

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
