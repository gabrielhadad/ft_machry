from flask import Flask

from app.config.config import config as app_config
from app.features import estoque, producao, produtos
from db.database_config import init_app as init_db

def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(app_config)
    if config:
        app.config.update(config)

    init_db(app)

    app.register_blueprint(produtos.bp)
    app.register_blueprint(estoque.bp)
    app.register_blueprint(producao.bp)
    
    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
