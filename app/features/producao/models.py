from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from db.database_config import db


class SolicitacaoProducao(db.Model):
    __tablename__ = "solicitacao_producao"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('ABERTA', 'EM_SEPARACAO', 'EM_PRODUCAO', 'CONCLUIDA', 'CANCELADA')",
            name="ck_solicitacao_status",
        ),
        db.CheckConstraint(
            "prioridade IN ('BAIXA', 'NORMAL', 'ALTA', 'URGENTE')",
            name="ck_solicitacao_prioridade",
        ),
        db.CheckConstraint(
            "quantidade_planejada > 0",
            name="ck_solicitacao_quantidade_planejada",
        ),
        db.CheckConstraint(
            "quantidade_produzida IS NULL OR quantidade_produzida >= 0",
            name="ck_solicitacao_quantidade_produzida",
        ),
        db.Index(
            "idx_solicitacao_planejamento",
            "status",
            "previsto_para",
            "prioridade",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    ficha_tecnica_id = db.Column(
        db.Integer, db.ForeignKey("ficha_tecnica.id"), nullable=False
    )
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    responsavel_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    quantidade_planejada = db.Column(db.Numeric(18, 3), nullable=False)
    quantidade_produzida = db.Column(db.Numeric(18, 3))
    prioridade = db.Column(
        db.Text, nullable=False, default="NORMAL", server_default="NORMAL"
    )
    previsto_para = db.Column(db.String)
    observacao = db.Column(db.Text)
    observacao_execucao = db.Column(db.Text)
    status = db.Column(db.Text, nullable=False, default="ABERTA", server_default="ABERTA")
    criado_em = db.Column(
        db.String,
        nullable=False,
        server_default=db.text("(CAST(CURRENT_TIMESTAMP AS TEXT))"),
    )
    iniciado_em = db.Column(db.String)
    concluido_em = db.Column(db.String)

    @property
    def perda_rendimento(self) -> float | None:
        """Diferença não produzida; não é saldo de estoque porque nunca existiu."""
        if self.quantidade_produzida is None:
            return None
        planejada = Decimal(str(self.quantidade_planejada))
        produzida = Decimal(str(self.quantidade_produzida))
        return float(max(planejada - produzida, Decimal("0")))


class SpFase(db.Model):
    __tablename__ = "sp_fase"
    __table_args__ = (
        db.UniqueConstraint(
            "solicitacao_producao_id", "ordem", name="uq_sp_fase_ordem"
        ),
        db.CheckConstraint(
            "tempo_realizado_min IS NULL OR tempo_realizado_min >= 0",
            name="ck_sp_fase_tempo_realizado",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    solicitacao_producao_id = db.Column(
        db.Integer, db.ForeignKey("solicitacao_producao.id"), nullable=False
    )
    # Mantemos a FK para rastreabilidade, mas a exibição histórica usa o snapshot.
    fase_id = db.Column(db.Integer, db.ForeignKey("fase_producao.id"), nullable=False)
    fase_nome_snapshot = db.Column(db.Text, nullable=False)
    ordem = db.Column(db.Integer, nullable=False)
    tempo_previsto_min = db.Column(db.Integer, nullable=False)
    tempo_realizado_min = db.Column(db.Integer)
    observacao = db.Column(db.Text)
    iniciado_em = db.Column(db.String)
    finalizado_em = db.Column(db.String)


class SpComponente(db.Model):
    __tablename__ = "sp_componente"
    __table_args__ = (
        db.UniqueConstraint(
            "solicitacao_producao_id", "produto_id", name="uq_sp_componente_produto"
        ),
        db.CheckConstraint("quantidade_prevista > 0", name="ck_sp_quantidade_prevista"),
    )

    id = db.Column(db.Integer, primary_key=True)
    solicitacao_producao_id = db.Column(
        db.Integer, db.ForeignKey("solicitacao_producao.id"), nullable=False
    )
    produto_id = db.Column(db.Integer, db.ForeignKey("produto.id"), nullable=False)
    quantidade_prevista = db.Column(db.Numeric(asdecimal=False), nullable=False)
    sp_fase_id = db.Column(db.Integer, db.ForeignKey("sp_fase.id"))


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
    sp_fase_id: int
    fase_id: int
    ordem: int
    fase: str
    tempo_previsto_min: int
    tempo_realizado_min: Optional[int]
    observacao: Optional[str]
    iniciado_em: Optional[str]
    finalizado_em: Optional[str]

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
