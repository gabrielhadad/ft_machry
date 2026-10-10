from flask import Blueprint

from ...db import get_db

bp = Blueprint("estoque", __name__, url_prefix="/api/estoque")


@bp.get("/inventario")
def inventario():
    rows = get_db().execute("SELECT * FROM vw_inventario").fetchall()
    return [dict(r) for r in rows]


@bp.get("/movimentacoes")
def movimentacoes():
    rows = get_db().execute(
        "SELECT * FROM movimentacao_estoque ORDER BY criado_em DESC LIMIT 100"
    ).fetchall()
    return [dict(r) for r in rows]
