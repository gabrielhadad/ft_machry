from flask import Blueprint

from app.utils.enums import AcaoPermissao, RecursoPermissao
from app.utils.paginacao import PaginacaoQuery, resposta_paginada
from app.utils.parsing import consulta, entrada
from app.utils.permissoes import exigir_permissao

from .repository import AcessoRepository
from .schemas import GrupoAcessoCreate, GrupoAcessoOut, GrupoAcessoUpdate, PermissaoOut
from .services import AcessoService

grupos_bp = Blueprint("grupos_acesso", __name__)
permissoes_bp = Blueprint("permissoes", __name__)


def get_service() -> AcessoService:
    return AcessoService(AcessoRepository())


def _saida(grupo, totais_de_usuarios: dict[int, int]):
    saida = GrupoAcessoOut.model_validate(grupo).model_dump()
    saida["total_usuarios"] = totais_de_usuarios.get(grupo.id, 0)
    return saida


def _saida_de_um(grupo):
    return _saida(grupo, get_service().contar_usuarios_por_grupo())


@permissoes_bp.get("")
@exigir_permissao(RecursoPermissao.GRUPOS_ACESSO, AcaoPermissao.LER)
def listar_permissoes():
    pagina = get_service().listar_permissoes(consulta(PaginacaoQuery))
    return resposta_paginada(pagina, PermissaoOut)


@grupos_bp.get("")
@exigir_permissao(RecursoPermissao.GRUPOS_ACESSO, AcaoPermissao.LER)
def listar():
    service = get_service()
    pagina = service.listar_grupos(consulta(PaginacaoQuery))
    totais = service.contar_usuarios_por_grupo()
    return resposta_paginada(pagina, lambda grupo: _saida(grupo, totais))


@grupos_bp.get("/<int:grupo_id>")
@exigir_permissao(RecursoPermissao.GRUPOS_ACESSO, AcaoPermissao.LER)
def detalhar(grupo_id: int):
    return _saida_de_um(get_service().obter_grupo(grupo_id))


@grupos_bp.post("")
@exigir_permissao(RecursoPermissao.GRUPOS_ACESSO, AcaoPermissao.CRIAR)
def criar():
    grupo = get_service().criar_grupo(entrada(GrupoAcessoCreate))
    return _saida_de_um(grupo), 201


@grupos_bp.put("/<int:grupo_id>")
@exigir_permissao(RecursoPermissao.GRUPOS_ACESSO, AcaoPermissao.ATUALIZAR)
def atualizar(grupo_id: int):
    grupo = get_service().atualizar_grupo(grupo_id, entrada(GrupoAcessoUpdate))
    return _saida_de_um(grupo)


@grupos_bp.delete("/<int:grupo_id>")
@exigir_permissao(RecursoPermissao.GRUPOS_ACESSO, AcaoPermissao.EXCLUIR)
def remover(grupo_id: int):
    get_service().remover_grupo(grupo_id)
    return "", 204
