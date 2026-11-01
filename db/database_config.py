import os

import click
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import URL, event, inspect, text
from werkzeug.security import generate_password_hash

from datetime import datetime, timezone


db = SQLAlchemy()
migrate = Migrate(compare_type=True)


def _montar_database_uri(config: dict):
    if config.get("DATABASE_URL"):
        return config["DATABASE_URL"]

    conexao = str(config.get("DB_CONNECTION", "sqlite")).lower()
    if conexao in {"postgres", "postgresql"}:
        return URL.create(
            "postgresql+psycopg2",
            username=config["DB_USERNAME"],
            password=config["DB_PASSWORD"],
            host=config["DB_HOST"],
            port=int(config["DB_PORT"]),
            database=config["DB_DATABASE"],
        )
    if conexao != "sqlite":
        raise ValueError("DB_CONNECTION deve ser sqlite, postgres ou postgresql")

    caminho = os.path.abspath(config["DATABASE_PATH"]).replace("\\", "/")
    os.makedirs(os.path.dirname(caminho) or ".", exist_ok=True)
    return f"sqlite:///{caminho}"


def _configurar_sqlite(engine) -> None:
    @event.listens_for(engine, "connect")
    def _configurar_conexao(conexao_dbapi, _):
        conexao_dbapi.execute("PRAGMA foreign_keys = ON")
        conexao_dbapi.isolation_level = None

    @event.listens_for(engine, "begin")
    def _begin_immediate(conexao):
        conexao.exec_driver_sql("BEGIN IMMEDIATE")


def _tabelas_existem(engine) -> bool:
    return inspect(engine).has_table("usuario")


def _provisionar_usuarios_iniciais() -> None:
    from app.features.auth.models import Usuario
    from flask import current_app

    configuracoes = [
        ("Proprietária", current_app.config["OWNER_USERNAME"], current_app.config["OWNER_INITIAL_PASSWORD"], "OWNER"),
        ("Gestor", current_app.config["MANAGER_USERNAME"], current_app.config["MANAGER_INITIAL_PASSWORD"], "ADMIN"),
        ("Cozinha", current_app.config["COOK_USERNAME"], current_app.config["COOK_INITIAL_PASSWORD"], "USER"),
    ]
    usuarios = db.session.execute(db.select(Usuario).order_by(Usuario.id)).scalars().all()
    por_username = {usuario.username.lower(): usuario for usuario in usuarios if usuario.username}
    por_papel = {usuario.papel: usuario for usuario in usuarios if usuario.papel}

    for nome, username, password, papel in configuracoes:
        username = username.strip().lower()
        usuario = por_username.get(username)
        if usuario is None and papel == "OWNER":
            usuario = por_papel.get("OWNER") or por_papel.get("ADMIN")
        elif usuario is None and papel == "USER":
            usuario = por_papel.get("USER")
        if usuario is None:
            usuario = Usuario(
                nome=nome,
                username=username,
                senha_hash=generate_password_hash(password),
                papel=papel,
                deve_trocar_senha=0 if current_app.config.get("TESTING") else 1,
                senha_alterada_em=datetime.now(timezone.utc).replace(microsecond=0).isoformat() if current_app.config.get("TESTING") else None,
            )
            db.session.add(usuario)
        else:
            usuario.username = usuario.username or username
            usuario.senha_hash = usuario.senha_hash or generate_password_hash(password)
            if papel == "OWNER":
                usuario.papel = "OWNER"
        por_username[username] = usuario
    db.session.commit()



VIEWS = {
    "vw_inventario": """
        SELECT p.id AS produto_id, p.nome AS produto, p.tipo AS tipo_produto,
               p.unidade_medida, l.id AS lote_id, l.quantidade,
               l.data_validade, loc.nome AS localizacao
          FROM lote l
          JOIN produto p ON p.id = l.produto_id
          JOIN localizacao loc ON loc.id = l.localizacao_id
         WHERE l.quantidade > 0
    """,
    "vw_fefo": """
        SELECT l.* FROM lote l WHERE l.quantidade > 0
         ORDER BY l.produto_id,
                  CASE WHEN l.data_validade IS NULL THEN 1 ELSE 0 END,
                  l.data_validade ASC, l.criado_em ASC, l.id ASC
    """,
    "vw_sp_componente": """
        SELECT c.id AS sp_componente_id, c.solicitacao_producao_id,
               c.produto_id, p.nome AS componente, p.unidade_medida,
               sf.ordem AS fase_ordem, sf.fase_nome_snapshot AS fase,
               c.quantidade_prevista,
               COALESCE(SUM(CASE WHEN m.tipo IN ('CONSUMO_PRODUCAO', 'PERDA')
                                 THEN m.quantidade ELSE 0 END), 0) AS quantidade_realizada,
               SUM(CASE WHEN m.tipo IN ('CONSUMO_PRODUCAO', 'PERDA')
                        THEN m.quantidade * l.custo_unitario ELSE 0 END) AS custo_realizado
          FROM sp_componente c
          JOIN produto p ON p.id = c.produto_id
          LEFT JOIN sp_fase sf ON sf.id = c.sp_fase_id
          LEFT JOIN movimentacao_estoque m
                 ON m.sp_componente_id = c.id
                AND m.tipo IN ('CONSUMO_PRODUCAO', 'PERDA')
          LEFT JOIN lote l ON l.id = m.lote_id
         GROUP BY c.id, c.solicitacao_producao_id, c.produto_id, p.nome,
                  p.unidade_medida, sf.ordem, sf.fase_nome_snapshot, c.quantidade_prevista
    """,
    "vw_sp_producao": """
        SELECT m.solicitacao_producao_id, m.lote_id, m.quantidade, m.criado_em
          FROM movimentacao_estoque m WHERE m.tipo = 'PRODUCAO'
    """,
}


def _criar_views() -> None:
    for nome, consulta in VIEWS.items():
        db.session.execute(text(f"CREATE VIEW {nome} AS {consulta}"))
    db.session.commit()


@click.command("init-db")
@click.option("--seed", is_flag=True, help="Também carrega os dados de exemplo em um banco vazio.")
def init_db_command(seed: bool):
    from flask import current_app

    if not _tabelas_existem(db.engine):
        # create_all fica restrito à suíte unitária. Em runtime o schema é responsabilidade do Alembic.
        if current_app.config.get("TESTING"):
            db.create_all()
            _criar_views()
        else:
            raise click.ClickException(
                "Schema não inicializado. Execute 'flask --app app db upgrade' antes de 'init-db'."
            )

    seed_aplicado = False
    if seed:
        from app.features.produtos.models import Produto

        possui_catalogo = db.session.scalar(db.select(Produto.id).limit(1)) is not None
        if not possui_catalogo:
            from db.seed import carregar_seeds

            carregar_seeds()
            seed_aplicado = True

    _provisionar_usuarios_iniciais()
    if seed and not seed_aplicado:
        click.echo("Banco inicializado; seeds ignorados porque o catálogo já possui dados.")
    else:
        click.echo("Banco inicializado." + (" (com seeds)" if seed_aplicado else ""))


def init_app(app: Flask):
    if "SQLALCHEMY_DATABASE_URI" not in app.config:
        app.config["SQLALCHEMY_DATABASE_URI"] = _montar_database_uri(app.config)
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    db.init_app(app)
    migrate.init_app(app, db, directory="migrations")
    with app.app_context():
        if db.engine.dialect.name == "sqlite":
            _configurar_sqlite(db.engine)

    app.cli.add_command(init_db_command)
