from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Mapped

from db.database_config import db


class ItemInventario(db.Model):
    """Mapeamento read-only da view vw_inventario."""

    __tablename__ = "vw_inventario"

    lote_id: Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    produto_id: Mapped[int] = db.mapped_column(db.Integer, nullable=False)
    produto: Mapped[str] = db.mapped_column(db.String, nullable=False)
    tipo_produto: Mapped[str] = db.mapped_column(db.String, nullable=False)
    unidade_medida: Mapped[str] = db.mapped_column(db.String, nullable=False)
    quantidade: Mapped[Decimal] = db.mapped_column(db.Numeric, nullable=False)
    data_validade: Mapped[Optional[str]] = db.mapped_column(db.String)
    localizacao: Mapped[str] = db.mapped_column(db.String, nullable=False)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class MovimentacaoEstoque(db.Model):
    """Mapeamento da tabela movimentacao_estoque."""

    __tablename__ = "movimentacao_estoque"

    id: Mapped[int] = db.mapped_column(db.Integer, primary_key=True)
    tipo: Mapped[str] = db.mapped_column(db.String, nullable=False)
    lote_id: Mapped[int] = db.mapped_column(db.Integer, nullable=False)
    lote_destino_id: Mapped[Optional[int]] = db.mapped_column(db.Integer)
    quantidade: Mapped[Decimal] = db.mapped_column(db.Numeric, nullable=False)
    quantidade_destino: Mapped[Optional[Decimal]] = db.mapped_column(db.Numeric)
    motivo: Mapped[Optional[str]] = db.mapped_column(db.Text)
    usuario_id: Mapped[int] = db.mapped_column(db.Integer, nullable=False)
    solicitacao_producao_id: Mapped[Optional[int]] = db.mapped_column(db.Integer)
    sp_componente_id: Mapped[Optional[int]] = db.mapped_column(db.Integer)
    observacao: Mapped[Optional[str]] = db.mapped_column(db.Text)
    criado_em: Mapped[str] = db.mapped_column(db.String, nullable=False)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

