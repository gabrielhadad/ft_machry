import sqlite3

from flask import Blueprint, request

from db.database_config import get_db

bp = Blueprint("produtos", __name__)


CAMPOS = (
    "nome",
    "tipo",
    "unidade_medida",
    "grupo_id",
    "conservacao",
    "validade_obrigatoria",
    "validade_padrao_dias",
    "foto_url",
)


def _buscar(produto_id):
    return get_db().execute(
        "SELECT * FROM produto WHERE id = ? AND ativo = 1", (produto_id,)
    ).fetchone()


def _campos():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return None, "corpo deve ser um objeto JSON"
    campos = {k: dados[k] for k in CAMPOS if k in dados}
    if not campos:
        return None, "nenhum campo de produto informado"
    if "nome" in campos and not str(campos["nome"] or "").strip():
        return None, "'nome' não pode ser vazio"
    return campos, None


def _gravar(sql, params):
    # NOT NULL, CHECK e FOREIGN KEY do schema fazem a validação de domínio.
    db = get_db()
    try:
        cur = db.execute(sql, params)
    except sqlite3.IntegrityError as e:
        return None, str(e)
    db.commit()
    return cur, None


@bp.get("")
def listar():
    rows = get_db().execute(
        "SELECT * FROM produto WHERE ativo = 1 ORDER BY nome"
    ).fetchall()
    return [dict(r) for r in rows]


@bp.get("/<int:produto_id>")
def detalhar(produto_id):
    row = _buscar(produto_id)
    if row is None:
        return {"erro": "produto não encontrado"}, 404
    return dict(row)


@bp.post("")
def criar():
    campos, erro = _campos()
    if erro:
        return {"erro": erro}, 400
    cur, erro = _gravar(
        f"INSERT INTO produto ({', '.join(campos)})"
        f" VALUES ({', '.join('?' * len(campos))})",
        tuple(campos.values()),
    )
    if erro:
        return {"erro": erro}, 400
    return dict(_buscar(cur.lastrowid)), 201


@bp.put("/<int:produto_id>")
def atualizar(produto_id):
    if _buscar(produto_id) is None:
        return {"erro": "produto não encontrado"}, 404
    campos, erro = _campos()
    if erro:
        return {"erro": erro}, 400
    _, erro = _gravar(
        f"UPDATE produto SET {', '.join(f'{k} = ?' for k in campos)} WHERE id = ?",
        (*campos.values(), produto_id),
    )
    if erro:
        return {"erro": erro}, 400
    return dict(_buscar(produto_id))


@bp.delete("/<int:produto_id>")
def remover(produto_id):
    # Exclusão lógica: produto é referenciado por lote, ficha técnica e
    # movimentações, e listar() já filtra por ativo = 1.
    cur, _ = _gravar(
        "UPDATE produto SET ativo = 0 WHERE id = ? AND ativo = 1", (produto_id,)
    )
    if cur.rowcount == 0:
        return {"erro": "produto não encontrado"}, 404
    return "", 204
