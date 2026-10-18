from flask import Blueprint

from db.database_config import get_db

bp = Blueprint("produtos", __name__, url_prefix="/api/produtos")


@bp.get("")
def listar():
    rows = get_db().execute(
        "SELECT * FROM produto WHERE ativo = 1 ORDER BY nome"
    ).fetchall()
    return [dict(r) for r in rows]
