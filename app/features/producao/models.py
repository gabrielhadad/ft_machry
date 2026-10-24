from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from db.database_config import db


class SolicitacaoProducao(db.Model):
    __tablename__ = "solicitacao_producao"

    id = db.Column(db.Integer, primary_key=True)
    ficha_tecnica_id = db.Column(db.Integer, nullable=False)
    usuario_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Text, nullable=False)
    criado_em = db.Column(db.String, nullable=False, server_default=db.text("(datetime('now'))"))
    concluido_em = db.Column(db.String)


@dataclass
class ComponenteSolicitacao:
    sp_componente_id: int
    solicitacao_producao_id: int
    produto_id: int
    componente: str
    unidade_medida: str
    fase_ordem: Optional[int]
    fase: Optional[str]
    quantidade_prevista: float
    quantidade_realizada: float
    custo_realizado: Optional[float]

    @classmethod
    def from_row(cls, row) -> "ComponenteSolicitacao":
        return cls(**{chave: row[chave] for chave in row.keys()})


@dataclass
class FaseSolicitacao:
    ordem: int
    fase: str
    tempo_previsto_min: int
    tempo_realizado_min: Optional[int]

    @classmethod
    def from_row(cls, row) -> "FaseSolicitacao":
        return cls(**{chave: row[chave] for chave in row.keys()})


@dataclass
class LoteProduzido:
    solicitacao_producao_id: int
    lote_id: int
    quantidade: float
    criado_em: str

    @classmethod
    def from_row(cls, row) -> "LoteProduzido":
        return cls(**{chave: row[chave] for chave in row.keys()})


@dataclass
class SolicitacaoDetalhe:
    solicitacao: SolicitacaoProducao
    componentes: list[ComponenteSolicitacao]
    fases: list[FaseSolicitacao]
    lotes_produzidos: list[LoteProduzido]
