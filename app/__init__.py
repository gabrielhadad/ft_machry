import os

from flask import Flask, send_from_directory

from app.utils.config import config as app_config
from app.features import estoque, producao, produtos
from db.database_config import init_app as init_db

DOCS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")

def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    prefixo_api = "/api"
    
    app.config.from_object(app_config)
    if config:
        app.config.update(config)

    init_db(app)

    app.register_blueprint(produtos.bp, url_prefix=f"{prefixo_api}/produtos")
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
        # Swagger UI via CDN, sem dependência Python; precisa de internet no navegador.
        return send_from_directory(DOCS_PATH, "swagger-ui.html")

    return app
