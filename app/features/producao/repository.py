from __future__ import annotations

from contextlib import contextmanager
from decimal import Decimal

from sqlalchemy import text

from app.features.auth.models import Usuario
from app.features.fichas_tecnicas.models import FichaTecnica
from db.database_config import db

from .models import SolicitacaoProducao, SpComponente, SpFase


class ProducaoRepository:

    @contextmanager
    def transacao(self):
        """Uma única fronteira de commit/rollback para operações entre features."""
        try:
            yield db.session
        except Exception:
            db.session.rollback()
            raise
        else:
            db.session.commit()

    def listar_solicitacoes(self) -> list[SolicitacaoProducao]:
        return db.session.query(SolicitacaoProducao).order_by(
            SolicitacaoProducao.criado_em.desc()
        ).all()

    def obter_solicitacao(self, sp_id: int, para_atualizacao: bool = False):
        if not para_atualizacao:
            return db.session.get(SolicitacaoProducao, sp_id)
        return db.session.execute(
            db.select(SolicitacaoProducao)
            .where(SolicitacaoProducao.id == sp_id)
            .with_for_update()
        ).scalar_one_or_none()

    def obter_ficha(self, ficha_id: int):
        return db.session.get(FichaTecnica, ficha_id)

    def obter_usuario_ativo(self, usuario_id: int):
        return db.session.execute(
            db.select(Usuario).where(Usuario.id == usuario_id, Usuario.ativo == 1)
        ).scalar_one_or_none()

    def criar_solicitacao(
        self,
        ficha: FichaTecnica,
        usuario_id: int,
        quantidade_planejada: Decimal,
        prioridade: str,
        previsto_para: str | None,
        responsavel_id: int | None,
        observacao: str | None,
    ) -> SolicitacaoProducao:
        solicitacao = SolicitacaoProducao(
            ficha_tecnica_id=ficha.id,
            usuario_id=usuario_id,
            responsavel_id=responsavel_id,
            quantidade_planejada=quantidade_planejada,
            prioridade=prioridade,
            previsto_para=previsto_para,
            observacao=observacao,
        )
        db.session.add(solicitacao)
        db.session.flush()

        # A ficha descreve os componentes necessários para o seu rendimento.
        # Ex.: ficha rende 10 e a solicitação pede 20 -> fator 2.
        fator = quantidade_planejada / Decimal(str(ficha.rendimento))

        fases_por_id: dict[int, int] = {}
        for fase in ficha.fases:
            fase_solicitacao = SpFase(
                solicitacao_producao_id=solicitacao.id,
                fase_id=fase.fase_id,
                # Snapshot histórico: mudanças futuras no catálogo não alteram
                # o nome exibido em produções já planejadas.
                fase_nome_snapshot=fase.fase.nome,
                ordem=fase.ordem,
                tempo_previsto_min=fase.tempo_previsto_min,
            )
            db.session.add(fase_solicitacao)
            db.session.flush()
            fases_por_id[fase.id] = fase_solicitacao.id

        for componente in ficha.componentes:
            quantidade = Decimal(str(componente.quantidade)) * fator
            db.session.add(
                SpComponente(
                    solicitacao_producao_id=solicitacao.id,
                    produto_id=componente.produto_id,
                    quantidade_prevista=float(quantidade),
                    sp_fase_id=fases_por_id.get(componente.ficha_tecnica_fase_id),
                )
            )
        db.session.commit()
        return solicitacao

    def definir_status(
        self, solicitacao: SolicitacaoProducao, status: str
    ) -> SolicitacaoProducao:
        """Altera o estado sem commit para permitir orquestração transacional."""
        solicitacao.status = status
        if status == "EM_PRODUCAO" and solicitacao.iniciado_em is None:
            solicitacao.iniciado_em = db.func.current_timestamp()
        if status == "CONCLUIDA":
            solicitacao.concluido_em = db.func.current_timestamp()
        return solicitacao

    def atualizar_status(
        self, solicitacao: SolicitacaoProducao, status: str
    ) -> SolicitacaoProducao:
        with self.transacao():
            self.definir_status(solicitacao, status)
        return solicitacao

    def listar_componentes_modelo(self, sp_id: int) -> list[SpComponente]:
        return (
            db.session.query(SpComponente)
            .filter(SpComponente.solicitacao_producao_id == sp_id)
            .order_by(SpComponente.id)
            .all()
        )

    def listar_fases_modelo(self, sp_id: int) -> list[SpFase]:
        return (
            db.session.query(SpFase)
            .filter(SpFase.solicitacao_producao_id == sp_id)
            .order_by(SpFase.ordem)
            .all()
        )

    def salvar_execucao(
        self,
        solicitacao: SolicitacaoProducao,
        *,
        quantidade_produzida: Decimal | None,
        observacao_execucao: str | None,
        fases: list[tuple[SpFase, object]],
    ) -> SolicitacaoProducao:
        if quantidade_produzida is not None:
            solicitacao.quantidade_produzida = quantidade_produzida
        if observacao_execucao is not None:
            solicitacao.observacao_execucao = observacao_execucao

        for fase, dados in fases:
            # Apenas campos enviados são substituídos; isso permite registrar
            # a execução aos poucos durante o preparo.
            if dados.tempo_realizado_min is not None:
                fase.tempo_realizado_min = dados.tempo_realizado_min
            if dados.observacao is not None:
                fase.observacao = dados.observacao
            if dados.iniciado_em is not None:
                fase.iniciado_em = dados.iniciado_em
            if dados.finalizado_em is not None:
                fase.finalizado_em = dados.finalizado_em

        db.session.flush()
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
                """SELECT f.id AS sp_fase_id, f.fase_id, f.ordem,
                          f.fase_nome_snapshot AS fase,
                          f.tempo_previsto_min, f.tempo_realizado_min,
                          f.observacao, f.iniciado_em, f.finalizado_em
                     FROM sp_fase f
                    WHERE f.solicitacao_producao_id = :id
                    ORDER BY f.ordem"""
            ),
            {"id": sp_id},
        ).mappings().all()

    def listar_lotes_produzidos(self, sp_id: int):
        return db.session.execute(
            text("SELECT * FROM vw_sp_producao WHERE solicitacao_producao_id = :id"),
            {"id": sp_id},
        ).mappings().all()
