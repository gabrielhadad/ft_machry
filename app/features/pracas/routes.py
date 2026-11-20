"""Rotas HTTP da gestão de praças."""

from flask import Blueprint

from app.utils.enums import AcaoPermissao, RecursoPermissao
from app.utils.paginacao import PaginacaoQuery, resposta_paginada
from app.utils.parsing import consulta, entrada
from app.utils.permissoes import exigir_permissao

from .repository import PracaRepository
from .schemas import CozinheiroResumo, PracaCreate, PracaOut, PracaUpdate
from .services import PracaService

bp = Blueprint("pracas", __name__)


def get_service() -> PracaService:
    return PracaService(PracaRepository())


def _saida(praca):
    return PracaOut.model_validate(praca).model_dump()


@bp.get("")
@exigir_permissao(RecursoPermissao.PRACAS, AcaoPermissao.LER)
def listar():
    return resposta_paginada(get_service().listar(consulta(PaginacaoQuery)), PracaOut)


@bp.get("/cozinheiros")
@exigir_permissao(RecursoPermissao.PRACAS, AcaoPermissao.LER)
def listar_cozinheiros():
    return resposta_paginada(
        get_service().listar_cozinheiros(consulta(PaginacaoQuery)), CozinheiroResumo
    )


@bp.get("/<int:praca_id>")
@exigir_permissao(RecursoPermissao.PRACAS, AcaoPermissao.LER)
def obter(praca_id: int):
    return _saida(get_service().obter(praca_id))


@bp.post("")
@exigir_permissao(RecursoPermissao.PRACAS, AcaoPermissao.CRIAR)
def criar():
    return _saida(get_service().criar(entrada(PracaCreate))), 201


@bp.put("/<int:praca_id>")
@exigir_permissao(RecursoPermissao.PRACAS, AcaoPermissao.ATUALIZAR)
def atualizar(praca_id: int):
    return _saida(get_service().atualizar(praca_id, entrada(PracaUpdate)))


@bp.delete("/<int:praca_id>")
@exigir_permissao(RecursoPermissao.PRACAS, AcaoPermissao.EXCLUIR)
def desativar(praca_id: int):
    get_service().desativar(praca_id)
    return "", 204
