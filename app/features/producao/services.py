"""Regras de negócio de produção, orquestrando o repository."""
from __future__ import annotations

from app.utils.errors import RegistroNaoEncontrado

from . import models
from .repository import ProducaoRepository


class ProducaoService:
    def __init__(self, repository: ProducaoRepository) -> None:
        self.repository = repository

    def listar_solicitacoes(self) -> list[models.SolicitacaoProducao]:
        return self.repository.listar_solicitacoes()

    def obter_detalhe(self, sp_id: int) -> models.SolicitacaoDetalhe:
        solicitacao = self.repository.obter_solicitacao(sp_id)
        if solicitacao is None:
            raise RegistroNaoEncontrado("solicitação não encontrada")

        return models.SolicitacaoDetalhe(
            solicitacao=solicitacao,
            componentes=[
                models.ComponenteSolicitacao.from_row(r)
                for r in self.repository.listar_componentes(sp_id)
            ],
            fases=[
                models.FaseSolicitacao.from_row(r)
                for r in self.repository.listar_fases(sp_id)
            ],
            lotes_produzidos=[
                models.LoteProduzido.from_row(r)
                for r in self.repository.listar_lotes_produzidos(sp_id)
            ],
        )
