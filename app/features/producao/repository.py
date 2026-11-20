from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import selectinload

from db.database_config import db

from app.features.estoque.models import Localizacao
from app.features.pracas.models import Praca
from app.features.fichas_tecnicas.models import FichaTecnica
from app.utils.enums import StatusSolicitacao
from app.utils.paginacao import PaginacaoQuery, paginar
from app.utils.interfaces.repository import RepositorioBase

from .models import SolicitacaoProducao, SpComponente, SpFase


class ProducaoRepository(RepositorioBase):
    def listar_solicitacoes(
        self, paginacao: PaginacaoQuery, praca_id: int | None = None
    ):
        consulta = db.select(SolicitacaoProducao).options(
            selectinload(SolicitacaoProducao.praca)
        )
        if praca_id is not None:
            consulta = consulta.where(SolicitacaoProducao.praca_id == praca_id)
        return paginar(
            consulta.order_by(
                SolicitacaoProducao.criado_em.desc(), SolicitacaoProducao.id.desc()
            ),
            paginacao,
        )

    def obter_solicitacao(self, sp_id: int, para_atualizacao: bool = False):
        return db.session.get(
            SolicitacaoProducao, sp_id, with_for_update=para_atualizacao
        )

    def obter_praca(self, praca_id: int, para_atualizacao: bool = False):
        return db.session.get(Praca, praca_id, with_for_update=para_atualizacao)

    def obter_ficha(self, ficha_id: int):
        return db.session.get(FichaTecnica, ficha_id)

    def obter_localizacao(self, localizacao_id: int):
        return db.session.get(Localizacao, localizacao_id)

    def primeira_localizacao_compativel(self, conservacao: str):
        return db.session.execute(
            db.select(Localizacao)
            .where(Localizacao.tipo == conservacao)
            .order_by(Localizacao.id)
            .limit(1)
        ).scalar_one_or_none()

    def criar_solicitacao(
        self, ficha: FichaTecnica, usuario_id: int, quantidade: float,
        localizacao_id: int,
        praca_id: int | None = None,
    ) -> SolicitacaoProducao:
        solicitacao = SolicitacaoProducao(
            ficha_tecnica_id=ficha.id,
            usuario_id=usuario_id,
            quantidade_planejada=quantidade,
            localizacao_destino_id=localizacao_id,
            praca_id=praca_id,
        )
        db.session.add(solicitacao)
        db.session.flush()
        fator = quantidade / float(ficha.rendimento)
        fases_por_id = {}
        for fase in ficha.fases:
            fase_solicitacao = SpFase(
                solicitacao_producao_id=solicitacao.id,
                fase_id=fase.fase_id,
                ordem=fase.ordem,
                tempo_previsto_min=fase.tempo_previsto_min,
            )
            db.session.add(fase_solicitacao)
            db.session.flush()
            fases_por_id[fase.id] = fase_solicitacao.id
        for componente in ficha.componentes:
            db.session.add(SpComponente(
                solicitacao_producao_id=solicitacao.id,
                produto_id=componente.produto_id,
                quantidade_prevista=float(componente.quantidade) * fator,
                sp_fase_id=fases_por_id.get(componente.ficha_tecnica_fase_id),
            ))
        # A transação é concluída pelo service junto às validações de praça.
        return solicitacao

    def componentes_da_solicitacao(self, sp_id: int) -> list[SpComponente]:
        return list(db.session.execute(
            db.select(SpComponente)
            .where(SpComponente.solicitacao_producao_id == sp_id)
            .order_by(SpComponente.id)
            .with_for_update()
        ).scalars())

    def marcar_status(self, solicitacao: SolicitacaoProducao, status: StatusSolicitacao) -> None:
        solicitacao.status = status
        if status == StatusSolicitacao.CONCLUIDA:
            solicitacao.concluido_em = db.func.current_timestamp()
        elif solicitacao.concluido_em is not None:
            solicitacao.concluido_em = None

    def atualizar_status(self, solicitacao: SolicitacaoProducao, status: str) -> SolicitacaoProducao:
        self.marcar_status(solicitacao, status)
        db.session.commit()
        return solicitacao

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
