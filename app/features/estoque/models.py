from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Optional


"""Entidades de domínio do estoque"""

@dataclass
class Localizacao:
    id: int
    nome: str
    tipo: str
    parent_id: Optional[int]
    foto_url: Optional[str]

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Localizacao":
        return cls(
            id=row["id"],
            nome=row["nome"],
            tipo=row["tipo"],
            parent_id=row["parent_id"],
            foto_url=row["foto_url"],
        )


@dataclass
class Lote:
    id: int
    produto_id: int
    localizacao_id: int
    quantidade: float
    data_producao: Optional[str]
    data_validade: Optional[str]
    custo_unitario: Optional[float]
    criado_em: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Lote":
        return cls(
            id=row["id"],
            produto_id=row["produto_id"],
            localizacao_id=row["localizacao_id"],
            quantidade=row["quantidade"],
            data_producao=row["data_producao"],
            data_validade=row["data_validade"],
            custo_unitario=row["custo_unitario"],
            criado_em=row["criado_em"],
        )


@dataclass
class LoteListado(Lote):
    produto: str = ""
    localizacao: str = ""

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "LoteListado":
        dados = Lote.from_row(row)
        return cls(produto=row["produto"], localizacao=row["localizacao"], **dados.__dict__)


@dataclass
class MovimentacaoEstoque:
    id: int
    tipo: str
    lote_id: int
    lote_destino_id: Optional[int]
    quantidade: float
    quantidade_destino: Optional[float]
    motivo: Optional[str]
    usuario_id: int
    solicitacao_producao_id: Optional[int]
    sp_componente_id: Optional[int]
    observacao: Optional[str]
    criado_em: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "MovimentacaoEstoque":
        return cls(**{chave: row[chave] for chave in row.keys()})


@dataclass
class ItemInventario:
    produto_id: int
    produto: str
    tipo_produto: str
    unidade_medida: str
    lote_id: int
    quantidade: float
    data_validade: Optional[str]
    localizacao: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "ItemInventario":
        return cls(**{chave: row[chave] for chave in row.keys()})


@dataclass
class LoteSugerido:
    lote_id: int
    quantidade: float
    data_validade: Optional[str]


@dataclass
class SugestaoSaida:
    produto_id: int
    quantidade_solicitada: float
    lotes: list[LoteSugerido]
    quantidade_faltante: float
