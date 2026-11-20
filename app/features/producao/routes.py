"""Rotas HTTP de produção.

Controller puro: delega a leitura para o service e serializa com schemas.py

"""
from flask import Blueprint, g

from app.utils.enums import AcaoPermissao, RecursoPermissao
from app.utils.paginacao import resposta_paginada
from app.utils.parsing import consulta, entrada
from app.utils.permissoes import exigir_permissao

from . import schemas
from .repository import ProducaoRepository
from .services import ProducaoService

bp = Blueprint("producao", __name__)


def get_service() -> ProducaoService:
    return ProducaoService(ProducaoRepository())


@bp.get("/solicitacoes")
@exigir_permissao(RecursoPermissao.PRODUCAO, AcaoPermissao.LER)
def listar_solicitacoes():
    filtros = consulta(schemas.SolicitacaoQuery)
    pagina = get_service().listar_solicitacoes(filtros, filtros.praca_id)
    return resposta_paginada(pagina, schemas.SolicitacaoProducaoOut)


@bp.post("/solicitacoes")
@exigir_permissao(RecursoPermissao.PRODUCAO, AcaoPermissao.CRIAR)
def criar_solicitacao():
    dados = entrada(schemas.SolicitacaoCreate)
    item = get_service().criar_solicitacao(
        dados.ficha_tecnica_id,
        g.usuario.id,
        dados.quantidade_planejada,
        dados.localizacao_destino_id,
        dados.praca_id,
    )
    return schemas.SolicitacaoProducaoOut.model_validate(item).model_dump(), 201


@bp.put("/solicitacoes/<int:sp_id>/praca")
# Atribuir praça altera o planejamento, não o andamento do cozinheiro.
@exigir_permissao(RecursoPermissao.PRODUCAO, AcaoPermissao.CRIAR)
def alterar_praca(sp_id: int):
    dados = entrada(schemas.SolicitacaoPracaUpdate)
    item = get_service().alterar_praca(sp_id, dados.praca_id)
    return schemas.SolicitacaoProducaoOut.model_validate(item).model_dump()


@bp.put("/solicitacoes/<int:sp_id>/status")
@exigir_permissao(RecursoPermissao.PRODUCAO, AcaoPermissao.ATUALIZAR)
def atualizar_status(sp_id: int):
    dados = entrada(schemas.SolicitacaoStatusUpdate)
    item = get_service().atualizar_status(sp_id, dados.status, g.usuario.id)
    return schemas.SolicitacaoProducaoOut.model_validate(item).model_dump()


@bp.get("/solicitacoes/<int:sp_id>")
@exigir_permissao(RecursoPermissao.PRODUCAO, AcaoPermissao.LER)
def detalhar_solicitacao(sp_id):
    detalhe = get_service().obter_detalhe(sp_id)
    return schemas.SolicitacaoDetalheOut.model_validate(detalhe).model_dump()
