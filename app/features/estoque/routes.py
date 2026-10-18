from flask import Blueprint

from .repository import EstoqueRepository
from .services import EstoqueService

bp = Blueprint("estoque", __name__)


def get_service() -> EstoqueService:
    return EstoqueService(repository=EstoqueRepository())


@bp.get("/inventario")
def inventario():
    return get_service().listar_inventario()


@bp.get("/movimentacoes")
def movimentacoes():
    return get_service().listar_movimentacoes()
