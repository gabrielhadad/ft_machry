import os
import sqlite3

import click
from flask import Flask, current_app, g
from flask_sqlalchemy import SQLAlchemy

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


@click.command("init-db")
@click.option("--seed", is_flag=True, help="Também carrega os dados de exemplo.")
def init_db_command(seed: bool):
    """Cria o banco a partir de schema.sql (e opcionalmente seeds.sql)."""
    path = current_app.config["DATABASE_PATH"]
    if os.path.exists(path):
        click.echo("Banco já criado")
        return

    conn = get_db()
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        conn.executescript(f.read())
    if seed:
        with open(SEEDS_PATH, encoding="utf-8") as f:
            conn.executescript(f.read())
    conn.commit()
    click.echo("Banco inicializado." + (" (com seeds)" if seed else ""))



def init_app(app: Flask):
    if "DATABASE_PATH" in app.config:
        os.makedirs(os.path.dirname(os.path.abspath(app.config["DATABASE_PATH"])) or ".", exist_ok=True)
        if "SQLALCHEMY_DATABASE_URI" not in app.config:
            db_path = os.path.abspath(app.config["DATABASE_PATH"]).replace("\\", "/")
            app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    db.init_app(app)
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)


