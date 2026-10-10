import os
import sqlite3

import click
from flask import Flask, current_app, g

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "schema.sql")
SEEDS_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "seeds.sql")


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
    """Cria o banco a partir de db/schema.sql (e opcionalmente db/seeds.sql)."""
    conn = get_db()
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        conn.executescript(f.read())
    if seed:
        with open(SEEDS_PATH, encoding="utf-8") as f:
            conn.executescript(f.read())
    conn.commit()
    click.echo("Banco inicializado." + (" (com seeds)" if seed else ""))


def init_app(app: Flask):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
