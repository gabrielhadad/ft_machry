from decimal import Decimal

from flask import Blueprint

from app.utils.dinheiro import para_json
from app.utils.enums import AcaoPermissao, RecursoPermissao
from app.utils.paginacao import PaginacaoQuery, resposta_paginada
from app.utils.parsing import consulta, entrada
from app.utils.permissoes import exigir_permissao

from .repository import FichaTecnicaRepository
from .schemas import FaseCatalogoOut, FichaLoteInput, FichaTecnicaInput
from .services import FichaTecnicaService

bp = Blueprint("fichas_tecnicas", __name__)


def get_service() -> FichaTecnicaService:
    return FichaTecnicaService(FichaTecnicaRepository())


def _valor(valor):
    return para_json(valor) if isinstance(valor, Decimal) else valor


def _serializar(ficha, com_custos: bool = True):
    """Os custos só vão no detalhe: na listagem custariam uma simulação por ficha."""
    custos = get_service().custos(ficha) if com_custos else None
    componentes = []
    for componente in ficha.componentes:
        item = {
            "id": componente.id,
            "produto_id": componente.produto_id,
            "produto": componente.produto.nome,
            "unidade_medida": componente.produto.unidade_medida,
            "quantidade": float(componente.quantidade),
            "ficha_tecnica_fase_id": componente.ficha_tecnica_fase_id,
            "fase_ordem": componente.fase.ordem if componente.fase else None,
        }
        if custos:
            item.update({chave: _valor(valor) for chave, valor in custos["componentes"][componente.id].items()})
        componentes.append(item)
    resultado = {
        "id": ficha.id,
        "produto_id": ficha.produto_id,
        "produto": ficha.produto.nome,
        "unidade_rendimento": ficha.produto.unidade_medida,
        "rendimento": float(ficha.rendimento),
        "observacao": ficha.observacao,
        "fases": [
            {
                "id": fase.id,
                "fase_id": fase.fase_id,
                "fase": fase.fase.nome,
                "ordem": fase.ordem,
                "tempo_previsto_min": fase.tempo_previsto_min,
            }
            for fase in ficha.fases
        ],
        "componentes": componentes,
    }
    if custos:
        resultado.update({
            chave: _valor(valor) for chave, valor in custos.items() if chave != "componentes"
        })
    return resultado


def _serializar_resumo(ficha):
    return _serializar(ficha, com_custos=False)


@bp.get("/fases")
@exigir_permissao(RecursoPermissao.FICHAS_TECNICAS, AcaoPermissao.LER)
def listar_fases():
    return resposta_paginada(
        get_service().listar_fases(consulta(PaginacaoQuery)), FaseCatalogoOut
    )


@bp.get("")
@exigir_permissao(RecursoPermissao.FICHAS_TECNICAS, AcaoPermissao.LER)
def listar():
    return resposta_paginada(get_service().listar(consulta(PaginacaoQuery)), _serializar_resumo)


@bp.get("/<int:ficha_id>")
@exigir_permissao(RecursoPermissao.FICHAS_TECNICAS, AcaoPermissao.LER)
def detalhar(ficha_id: int):
    return _serializar(get_service().obter(ficha_id))


@bp.post("")
@exigir_permissao(RecursoPermissao.FICHAS_TECNICAS, AcaoPermissao.CRIAR)
def criar():
    return _serializar(get_service().criar(entrada(FichaTecnicaInput))), 201


@bp.post("/lote")
@exigir_permissao(RecursoPermissao.FICHAS_TECNICAS, AcaoPermissao.CRIAR)
def criar_lote():
    fichas, fases_criadas, ignoradas = get_service().criar_lote(entrada(FichaLoteInput))
    return {
        "items": [_serializar_resumo(ficha) for ficha in fichas],
        "total": len(fichas),
        "fases_criadas": fases_criadas,
        "ignoradas": ignoradas,
    }, 201


@bp.put("/<int:ficha_id>")
@exigir_permissao(RecursoPermissao.FICHAS_TECNICAS, AcaoPermissao.ATUALIZAR)
def atualizar(ficha_id: int):
    return _serializar(
        get_service().atualizar(ficha_id, entrada(FichaTecnicaInput))
    )


@bp.delete("/<int:ficha_id>")
@exigir_permissao(RecursoPermissao.FICHAS_TECNICAS, AcaoPermissao.EXCLUIR)
def remover(ficha_id: int):
    get_service().remover(ficha_id)
    return "", 204
