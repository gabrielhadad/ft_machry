from __future__ import annotations

from sqlalchemy import text

from db.database_config import db

from .models import SolicitacaoProducao


class ProducaoRepository:

    def listar_solicitacoes(self) -> list[SolicitacaoProducao]:
        return db.session.query(SolicitacaoProducao).order_by(
            SolicitacaoProducao.criado_em.desc()
        ).all()

    def obter_solicitacao(self, sp_id: int):
        return db.session.get(SolicitacaoProducao, sp_id)

    def listar_componentes(self, sp_id: int):
        return db.session.execute(
            text(
                """SELECT * FROM vw_sp_componente WHERE solicitacao_producao_id = :id
                   ORDER BY fase_ordem, componente"""
            ),
            {"id": sp_id},
        ).mappings().all()

    def listar_fases(self, sp_id: int):
        return db.session.execute(
            text(
                """SELECT f.ordem, fp.nome AS fase, f.tempo_previsto_min, f.tempo_realizado_min
                   FROM sp_fase f JOIN fase_producao fp ON fp.id = f.fase_id
                   WHERE f.solicitacao_producao_id = :id ORDER BY f.ordem"""
            ),
            {"id": sp_id},
        ).mappings().all()

    def listar_lotes_produzidos(self, sp_id: int):
        return db.session.execute(
            text("SELECT * FROM vw_sp_producao WHERE solicitacao_producao_id = :id"),
            {"id": sp_id},
        ).mappings().all()
