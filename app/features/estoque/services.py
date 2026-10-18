from .repository import EstoqueRepository


class EstoqueService:
    def __init__(self, repository: EstoqueRepository) -> None:
        self.repository = repository

    def listar_inventario(self) -> list[dict]:
        """Retorna o inventário atual."""
        return self.repository.buscar_inventario()

    def listar_movimentacoes(self, limit: int = 100) -> list[dict]:
        """Retorna as movimentações de estoque mais recentes."""
        return self.repository.buscar_movimentacoes(limite=limit)
