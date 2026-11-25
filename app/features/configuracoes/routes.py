from flask import Blueprint

from app.utils.enums import AcaoPermissao, RecursoPermissao
from app.utils.parsing import entrada
from app.utils.permissoes import exigir_permissao

from .schemas import ConfiguracoesInput
from .services import ConfiguracaoService

bp = Blueprint("configuracoes", __name__)


@bp.get("")
@exigir_permissao(RecursoPermissao.CONFIGURACOES, AcaoPermissao.LER)
def obter():
    return ConfiguracaoService().obter().model_dump(mode="json")


@bp.put("")
@exigir_permissao(RecursoPermissao.CONFIGURACOES, AcaoPermissao.ATUALIZAR)
def atualizar():
    return ConfiguracaoService().atualizar(entrada(ConfiguracoesInput)).model_dump(mode="json")
