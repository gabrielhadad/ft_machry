from flask import Flask

from . import db


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object("app.config.Config")
    if config:
        app.config.update(config)

    db.init_app(app)

    from .features import estoque, producao, produtos

    app.register_blueprint(produtos.bp)
    app.register_blueprint(estoque.bp)
    app.register_blueprint(producao.bp)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
