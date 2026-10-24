import os
import sqlite3

import click
from flask import Flask, current_app, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event, inspect

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")
SEEDS_PATH = os.path.join(os.path.dirname(__file__), "seeds.sql")

db = SQLAlchemy()


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        path = current_app.config["DATABASE_PATH"]
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        g.db = sqlite3.connect(path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def _montar_database_uri(config: dict) -> str:
    DB_CONNECTION = config.get("DB_CONNECTION", "sqlite")

    if DB_CONNECTION == "postgres":
        DB_HOST = config["DB_HOST"]
        DB_PORT = config["DB_PORT"]
        DB_DATABASE = config["DB_DATABASE"]
        DB_USERNAME = config["DB_USERNAME"]
        DB_PASSWORD = config["DB_PASSWORD"]
        DATABASE_URL = f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"
        return DATABASE_URL

    DATABASE_PATH = os.path.abspath(config["DATABASE_PATH"]).replace("\\", "/")
    os.makedirs(os.path.dirname(DATABASE_PATH) or ".", exist_ok=True)
    DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
    return DATABASE_URL


def _registrar_begin_immediate(engine) -> None:
    @event.listens_for(engine, "connect")
    def _desligar_begin_implicito(conexao_dbapi, _):
        conexao_dbapi.isolation_level = None

    @event.listens_for(engine, "begin")
    def _begin_immediate(conexao):
        conexao.exec_driver_sql("BEGIN IMMEDIATE")


def _tabelas_existem(engine) -> bool:
    return inspect(engine).has_table("usuario")


@click.command("init-db")
@click.option("--seed", is_flag=True, help="Também carrega os dados de exemplo.")
def init_db_command(seed: bool):
    if _tabelas_existem(db.engine):
        click.echo("Banco já criado")
        return

    caminhos = [SCHEMA_PATH] + ([SEEDS_PATH] if seed else [])

    conexao = db.engine.raw_connection()
    try:
        for caminho in caminhos:
            with open(caminho, encoding="utf-8") as f:
                conexao.executescript(f.read())
        conexao.commit()
    finally:
        conexao.close()
    click.echo("Banco inicializado." + (" (com seeds)" if seed else ""))


def init_app(app: Flask):
    if "SQLALCHEMY_DATABASE_URI" not in app.config:
        app.config["SQLALCHEMY_DATABASE_URI"] = _montar_database_uri(app.config)

    db.init_app(app)

    if app.config.get("DB_CONNECTION", "sqlite") == "sqlite":
        with app.app_context():
            _registrar_begin_immediate(db.engine)

    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
