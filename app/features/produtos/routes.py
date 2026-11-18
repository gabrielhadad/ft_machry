from flask import Blueprint

from app.utils.enums import AcaoPermissao, RecursoPermissao
from app.utils.paginacao import PaginacaoQuery, resposta_paginada
from app.utils.parsing import consulta, entrada
from app.utils.permissoes import exigir_permissao

from .repository import ProdutoRepository
from .schemas import ProdutoCreate, ProdutoLoteCreate, ProdutoOut, ProdutoUpdate
from .services import ProdutoService

bp = Blueprint("produtos", __name__)


def get_service() -> ProdutoService:
    return ProdutoService(ProdutoRepository())


def _saida(produto):
    return ProdutoOut.model_validate(produto).model_dump()


@bp.get("")
@exigir_permissao(RecursoPermissao.PRODUTOS, AcaoPermissao.LER)
def listar():
    return resposta_paginada(get_service().listar(consulta(PaginacaoQuery)), ProdutoOut)


@bp.get("/<int:produto_id>")
@exigir_permissao(RecursoPermissao.PRODUTOS, AcaoPermissao.LER)
def detalhar(produto_id: int):
    return _saida(get_service().obter(produto_id))


@bp.post("")
@exigir_permissao(RecursoPermissao.PRODUTOS, AcaoPermissao.CRIAR)
def criar():
    produto = get_service().criar(entrada(ProdutoCreate))
    return _saida(produto), 201


@bp.post("/lote")
@exigir_permissao(RecursoPermissao.PRODUTOS, AcaoPermissao.CRIAR)
def criar_lote():
    produtos, ignorados = get_service().criar_lote(entrada(ProdutoLoteCreate))
    return {
        "items": [_saida(produto) for produto in produtos],
        "total": len(produtos),
        "ignorados": ignorados,
    }, 201


@bp.put("/<int:produto_id>")
@exigir_permissao(RecursoPermissao.PRODUTOS, AcaoPermissao.ATUALIZAR)
def atualizar(produto_id: int):
    return _saida(get_service().atualizar(produto_id, entrada(ProdutoUpdate)))


@bp.delete("/<int:produto_id>")
@exigir_permissao(RecursoPermissao.PRODUTOS, AcaoPermissao.EXCLUIR)
def remover(produto_id: int):
    get_service().remover(produto_id)
    return "", 204
