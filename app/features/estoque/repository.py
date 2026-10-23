from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Optional

from db.database_config import get_db

"""Acesso a dados do estoque. """

class EstoqueRepository:
    def _conn(self) -> sqlite3.Connection:
        return get_db()

    @contextmanager
    def transacao(self):
        db = self._conn()
        db.execute("BEGIN IMMEDIATE")
        try:
            yield db
        except Exception:
            db.rollback()
            raise
        else:
            db.commit()

    def listar_inventario(self, produto_id: Optional[int] = None, lote_id: Optional[int] = None):
        sql = "SELECT * FROM vw_inventario WHERE 1=1"
        args: list = []
        if produto_id is not None:
            sql += " AND produto_id = ?"
            args.append(produto_id)
        if lote_id is not None:
            sql += " AND lote_id = ?"
            args.append(lote_id)
        sql += " ORDER BY produto, data_validade, lote_id"
        return self._conn().execute(sql, args).fetchall()

    def listar_movimentacoes(
        self,
        limite: int = 100,
        lote_id: Optional[int] = None,
        usuario_id: Optional[int] = None,
        tipo: Optional[str] = None,
    ):
        sql = "SELECT * FROM movimentacao_estoque WHERE 1=1"
        args: list = []
        if lote_id is not None:
            sql += " AND lote_id = ?"
            args.append(lote_id)
        if usuario_id is not None:
            sql += " AND usuario_id = ?"
            args.append(usuario_id)
        if tipo is not None:
            sql += " AND tipo = ?"
            args.append(tipo)
        sql += " ORDER BY id DESC LIMIT ?"
        args.append(limite)
        return self._conn().execute(sql, args).fetchall()

    def obter_movimentacao(self, mov_id: int):
        return self._conn().execute(
            "SELECT * FROM movimentacao_estoque WHERE id = ?", (mov_id,)
        ).fetchone()

    def inserir_movimentacao(
        self, *, tipo, lote_id, lote_destino_id, quantidade,
        quantidade_destino, motivo, usuario_id, observacao,
    ) -> int:
        cur = self._conn().execute(
            """INSERT INTO movimentacao_estoque
               (tipo, lote_id, lote_destino_id, quantidade, quantidade_destino,
                motivo, usuario_id, observacao)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (tipo, lote_id, lote_destino_id, quantidade, quantidade_destino,
             motivo, usuario_id, observacao),
        )
        return cur.lastrowid

    def transformacao_cadastrada(self, produto_origem_id: int, produto_destino_id: int) -> bool:
        return self._conn().execute(
            """SELECT 1 FROM produto_transformacao
               WHERE produto_origem_id = ? AND produto_destino_id = ?""",
            (produto_origem_id, produto_destino_id),
        ).fetchone() is not None

    def listar_localizacoes(self):
        return self._conn().execute("SELECT * FROM localizacao ORDER BY nome").fetchall()

    def obter_localizacao(self, loc_id: int):
        return self._conn().execute(
            "SELECT * FROM localizacao WHERE id = ?", (loc_id,)
        ).fetchone()

    def inserir_localizacao(self, *, nome, tipo, parent_id, foto_url) -> int:
        cur = self._conn().execute(
            "INSERT INTO localizacao(nome, tipo, parent_id, foto_url) VALUES (?, ?, ?, ?)",
            (nome, tipo, parent_id, foto_url),
        )
        return cur.lastrowid

    def atualizar_localizacao(self, loc_id: int, campos: dict) -> None:
        sql = ", ".join(f"{campo} = ?" for campo in campos)
        self._conn().execute(
            f"UPDATE localizacao SET {sql} WHERE id = ?", (*campos.values(), loc_id)
        )

    def remover_localizacao(self, loc_id: int) -> int:
        cur = self._conn().execute("DELETE FROM localizacao WHERE id = ?", (loc_id,))
        return cur.rowcount

    def existe_incompatibilidade_tipo(self, loc_id: int, novo_tipo: str) -> bool:
        return self._conn().execute(
            """SELECT 1 FROM lote l JOIN produto p ON p.id = l.produto_id
               WHERE l.localizacao_id = ? AND p.conservacao <> ? LIMIT 1""",
            (loc_id, novo_tipo),
        ).fetchone() is not None

    def listar_lotes(self, produto_id: Optional[int] = None, localizacao_id: Optional[int] = None):
        sql = """SELECT l.*, p.nome AS produto, loc.nome AS localizacao FROM lote l
                 JOIN produto p ON p.id = l.produto_id
                 JOIN localizacao loc ON loc.id = l.localizacao_id WHERE 1=1"""
        args: list = []
        if produto_id is not None:
            sql += " AND l.produto_id = ?"
            args.append(produto_id)
        if localizacao_id is not None:
            sql += " AND l.localizacao_id = ?"
            args.append(localizacao_id)
        sql += " ORDER BY l.data_validade IS NULL, l.data_validade, l.id"
        return self._conn().execute(sql, args).fetchall()

    def obter_lote(self, lote_id: int):
        return self._conn().execute("SELECT * FROM lote WHERE id = ?", (lote_id,)).fetchone()

    def inserir_lote(
        self, *, produto_id, localizacao_id, data_producao, data_validade, custo_unitario
    ) -> int:
        cur = self._conn().execute(
            """INSERT INTO lote(produto_id, localizacao_id, data_producao, data_validade,
                                 custo_unitario)
               VALUES (?, ?, ?, ?, ?)""",
            (produto_id, localizacao_id, data_producao, data_validade, custo_unitario),
        )
        return cur.lastrowid

    def atualizar_lote(self, lote_id: int, campos: dict) -> None:
        sql = ", ".join(f"{campo} = ?" for campo in campos)
        self._conn().execute(
            f"UPDATE lote SET {sql} WHERE id = ?", (*campos.values(), lote_id)
        )

    def lotes_fefo_disponiveis(self, produto_id: int):
        return self._conn().execute(
            """SELECT * FROM lote WHERE produto_id = ? AND quantidade > 0
               AND (data_validade IS NULL OR data_validade >= date('now'))
               ORDER BY data_validade IS NULL, data_validade, criado_em, id""",
            (produto_id,),
        ).fetchall()

    def obter_produto(self, produto_id: int):
        return self._conn().execute("SELECT * FROM produto WHERE id = ?", (produto_id,)).fetchone()

    def obter_produto_ativo(self, produto_id: int):
        return self._conn().execute(
            "SELECT * FROM produto WHERE id = ? AND ativo = 1", (produto_id,)
        ).fetchone()

    def obter_usuario_ativo(self, usuario_id: int):
        return self._conn().execute(
            "SELECT * FROM usuario WHERE id = ? AND ativo = 1", (usuario_id,)
        ).fetchone()
