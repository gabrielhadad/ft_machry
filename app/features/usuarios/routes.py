from flask import Blueprint, g

from app.features.acessos.repository import AcessoRepository
from app.utils.enums import AcaoPermissao, RecursoPermissao
from app.utils.paginacao import PaginacaoQuery, resposta_paginada
from app.utils.parsing import consulta, entrada
from app.utils.permissoes import exigir_permissao

from .repository import UsuarioRepository
from .schemas import UsuarioCreate, UsuarioOut, UsuarioUpdate
from .services import UsuarioService

bp = Blueprint("usuarios", __name__)


def get_service() -> UsuarioService:
    return UsuarioService(UsuarioRepository(), AcessoRepository())


def _saida(usuario):
    return UsuarioOut.model_validate(usuario).model_dump()


@bp.get("")
@exigir_permissao(RecursoPermissao.USUARIOS, AcaoPermissao.LER)
def listar():
    return resposta_paginada(get_service().listar(consulta(PaginacaoQuery)), UsuarioOut)


@bp.post("")
@exigir_permissao(RecursoPermissao.USUARIOS, AcaoPermissao.CRIAR)
def criar():
    usuario = get_service().criar(entrada(UsuarioCreate))
    return _saida(usuario), 201


@bp.put("/<int:usuario_id>")
@exigir_permissao(RecursoPermissao.USUARIOS, AcaoPermissao.ATUALIZAR)
def atualizar(usuario_id: int):
    usuario = get_service().atualizar(usuario_id, entrada(UsuarioUpdate), g.usuario.id)
    return _saida(usuario)


@bp.delete("/<int:usuario_id>")
@exigir_permissao(RecursoPermissao.USUARIOS, AcaoPermissao.EXCLUIR)
def remover(usuario_id: int):
    get_service().remover(usuario_id, g.usuario.id)
    return "", 204
