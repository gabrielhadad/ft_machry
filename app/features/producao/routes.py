"""Rotas HTTP de produção.

Controller puro: delega a leitura para o service e serializa com schemas.py

"""
from flask import Blueprint

from . import schemas
from .repository import ProducaoRepository
from .services import ProducaoService

bp = Blueprint("producao", __name__)


def get_service() -> ProducaoService:
    return ProducaoService(ProducaoRepository())


@bp.get("/solicitacoes")
def listar_solicitacoes():
    itens = get_service().listar_solicitacoes()
    return [schemas.SolicitacaoProducaoOut.model_validate(i).model_dump() for i in itens]


@bp.get("/solicitacoes/<int:sp_id>")
def detalhar_solicitacao(sp_id):
    detalhe = get_service().obter_detalhe(sp_id)
    return schemas.SolicitacaoDetalheOut.model_validate(detalhe).model_dump()
