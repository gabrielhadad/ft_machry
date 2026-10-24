from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from db.database_config import db


class Localizacao(db.Model):
    __tablename__ = "localizacao"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer)
    foto_url = db.Column(db.Text)


class Lote(db.Model):
    __tablename__ = "lote"

    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, nullable=False)
    localizacao_id = db.Column(db.Integer, nullable=False)
    quantidade = db.Column(db.Numeric(asdecimal=False), nullable=False)
    data_producao = db.Column(db.String)
    data_validade = db.Column(db.String)
    custo_unitario = db.Column(db.Numeric(asdecimal=False))
    criado_em = db.Column(db.String, nullable=False, server_default=db.text("(datetime('now'))"))


class MovimentacaoEstoque(db.Model):
    __tablename__ = "movimentacao_estoque"

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.Text, nullable=False)
    lote_id = db.Column(db.Integer, nullable=False)
    lote_destino_id = db.Column(db.Integer)
    quantidade = db.Column(db.Numeric(asdecimal=False), nullable=False)
    quantidade_destino = db.Column(db.Numeric(asdecimal=False))
    motivo = db.Column(db.Text)
    usuario_id = db.Column(db.Integer, nullable=False)
    solicitacao_producao_id = db.Column(db.Integer)
    sp_componente_id = db.Column(db.Integer)
    observacao = db.Column(db.Text)
    criado_em = db.Column(db.String, nullable=False, server_default=db.text("(datetime('now'))"))

    @classmethod
    def from_row(cls, row) -> "MovimentacaoEstoque":
        return cls(**{chave: row[chave] for chave in row.keys()})


class Produto(db.Model):
    __tablename__ = "produto"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.Text, nullable=False)
    conservacao = db.Column(db.Text, nullable=False)
    validade_obrigatoria = db.Column(db.Integer, nullable=False)
    ativo = db.Column(db.Integer, nullable=False)


class Usuario(db.Model):
    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.Text, nullable=False)
    papel = db.Column(db.Text, nullable=False)
    ativo = db.Column(db.Integer, nullable=False)


class ProdutoTransformacao(db.Model):
    __tablename__ = "produto_transformacao"

    produto_origem_id = db.Column(db.Integer, primary_key=True)
    produto_destino_id = db.Column(db.Integer, primary_key=True)


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
    def from_row(cls, row) -> "ItemInventario":
        return cls(**{chave: row[chave] for chave in row.keys()})


@dataclass
class LoteListado:
    id: int
    produto_id: int
    localizacao_id: int
    quantidade: float
    data_producao: Optional[str]
    data_validade: Optional[str]
    custo_unitario: Optional[float]
    criado_em: str
    produto: str
    localizacao: str

    @classmethod
    def from_row(cls, row) -> "LoteListado":
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
