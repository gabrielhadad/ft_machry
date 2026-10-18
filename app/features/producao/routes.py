from flask import Blueprint

from db.database_config import get_db

bp = Blueprint("producao", __name__, url_prefix="/api/producao")


@bp.get("/solicitacoes")
def listar():
    rows = get_db().execute(
        "SELECT * FROM solicitacao_producao ORDER BY criado_em DESC"
    ).fetchall()
    return [dict(r) for r in rows]


@bp.get("/solicitacoes/<int:sp_id>")
def detalhar(sp_id):
    db = get_db()
    sp = db.execute(
        "SELECT * FROM solicitacao_producao WHERE id = ?", (sp_id,)
    ).fetchone()
    if sp is None:
        return {"erro": "solicitação não encontrada"}, 404

    componentes = db.execute(
        "SELECT * FROM vw_sp_componente WHERE solicitacao_producao_id = ?"
        " ORDER BY fase_ordem, componente",
        (sp_id,),
    ).fetchall()
    fases = db.execute(
        "SELECT f.ordem, fp.nome AS fase, f.tempo_previsto_min, f.tempo_realizado_min"
        " FROM sp_fase f JOIN fase_producao fp ON fp.id = f.fase_id"
        " WHERE f.solicitacao_producao_id = ? ORDER BY f.ordem",
        (sp_id,),
    ).fetchall()
    lotes_produzidos = db.execute(
        "SELECT * FROM vw_sp_producao WHERE solicitacao_producao_id = ?",
        (sp_id,),
    ).fetchall()

    return {
        "solicitacao": dict(sp),
        "componentes": [dict(r) for r in componentes],
        "fases": [dict(r) for r in fases],
        "lotes_produzidos": [dict(r) for r in lotes_produzidos],
    }
