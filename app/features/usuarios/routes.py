"""GET /usuarios, GET /transformacoes e POST /transformacoes do blueprint de
estoque. Implementados em estilo direto (SQL cru via get_db()), igual ao
arquivo routes.py original, em vez de passar pelas camadas schemas/
repository/services — são endpoints pequenos, só pra desbloquear o frontend.
"""
import sqlite3

from flask import request

from db.database_config import get_db

from ..estoque.routes import bp


def _erro(msg, status=400):
    return {"erro": str(msg)}, status


def _corpo():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        raise ValueError("envie um objeto JSON")
    return dados


def _inteiro(dados, nome):
    valor = dados.get(nome)
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        raise ValueError(f"{nome} deve ser inteiro positivo")
    return valor


def _existe_produto_ativo(db, produto_id):
    return db.execute(
        "SELECT 1 FROM produto WHERE id = ? AND ativo = 1", (produto_id,)
    ).fetchone() is not None


@bp.get("/usuarios")
def usuarios_ativos():
    linhas = get_db().execute(
        "SELECT id, nome, papel FROM usuario WHERE ativo = 1 ORDER BY nome"
    ).fetchall()
    return [dict(r) for r in linhas]


@bp.get("/transformacoes")
def listar_transformacoes():
    linhas = get_db().execute(
        "SELECT produto_origem_id, produto_destino_id FROM produto_transformacao "
        "ORDER BY produto_origem_id, produto_destino_id"
    ).fetchall()
    return [dict(r) for r in linhas]


@bp.post("/transformacoes")
def autorizar_transformacao():
    try:
        dados = _corpo()
        origem = _inteiro(dados, "produto_origem_id")
        destino = _inteiro(dados, "produto_destino_id")
        if origem == destino:
            raise ValueError("origem e destino precisam ser diferentes")
    except ValueError as exc:
        return _erro(exc)

    db = get_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        if not _existe_produto_ativo(db, origem) or not _existe_produto_ativo(db, destino):
            raise ValueError("produtos ativos não encontrados")
        db.execute(
            "INSERT INTO produto_transformacao (produto_origem_id, produto_destino_id) VALUES (?, ?)",
            (origem, destino),
        )
        db.commit()
    except (ValueError, sqlite3.IntegrityError) as exc:
        db.rollback()
        return _erro(exc)
    except Exception:
        db.rollback()
        raise

    return {"produto_origem_id": origem, "produto_destino_id": destino}, 201
