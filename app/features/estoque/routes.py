from flask import Blueprint

from .repository import EstoqueRepository
from .services import EstoqueService

bp = Blueprint("estoque", __name__, url_prefix="/api/estoque")

_service = EstoqueService(repository=EstoqueRepository())


@bp.get("/inventario")
def inventario():
    return _service.listar_inventario()


@bp.get("/movimentacoes")
def movimentacoes():
    return _service.listar_movimentacoes()
