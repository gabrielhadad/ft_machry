from flask import Flask, send_from_directory

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

    @app.get("/openapi.yaml")
    def openapi():
        return send_from_directory(app.root_path, "openapi.yaml")

    @app.get("/docs")
    def docs():
        # ponytail: Swagger UI via CDN, sem dependência Python; precisa de internet no navegador.
        return """<!doctype html>
<html><head><meta charset="utf-8"><title>ft_machry API</title>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui.css">
</head><body><div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui-bundle.js"></script>
<script>SwaggerUIBundle({url: "/openapi.yaml", dom_id: "#swagger-ui"});</script>
</body></html>"""

    return app
