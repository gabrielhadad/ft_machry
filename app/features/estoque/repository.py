from sqlalchemy import select

from .models import ItemInventario, MovimentacaoEstoque
from db.database_config import db


class EstoqueRepository:
    def fetch_inventario(self) -> list[dict]:
        """Retorna todos os itens da view de inventário."""
        stmt = select(ItemInventario)
        rows = db.session.execute(stmt).scalars().all()
        return [r.to_dict() for r in rows]

    def fetch_movimentacoes(self, limit: int = 100) -> list[dict]:
        """Retorna as movimentações de estoque mais recentes."""
        stmt = (
            select(MovimentacaoEstoque)
            .order_by(MovimentacaoEstoque.criado_em.desc())
            .limit(limit)
        )
        rows = db.session.execute(stmt).scalars().all()
        return [r.to_dict() for r in rows]

