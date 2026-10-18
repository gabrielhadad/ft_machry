from db.database_config import db
from .models import ItemInventario, MovimentacaoEstoque


class EstoqueRepository:
    def buscar_inventario(self) -> list[dict]:
        """Retorna todos os itens da view de inventário."""
        consulta = db.select(ItemInventario)

        registros = db.session.execute(consulta).scalars().all()
        return [r.to_dict() for r in registros]

    def buscar_movimentacoes(self, limite: int = 100) -> list[dict]:
        """Retorna as movimentações de estoque mais recentes."""
        consulta = (
            db.select(MovimentacaoEstoque)
            .order_by(MovimentacaoEstoque.criado_em.desc())
            .limit(limite)
        )

        registros = db.session.execute(consulta).scalars().all()
        return [r.to_dict() for r in registros]

